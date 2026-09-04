import os
import sys
import json
import argparse
import time
import csv

# Ensure backend can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.buyers.schemas import BuyerIntentSchema
from app.models import Product, ProductAttribute
from app.buyers.configurations import StructuredBuyer, SemanticBuyer
from app.buyers.llm_agent import LLMBuyer
from app.adapters.llm import FakeModelAdapter
from app.commerce.runner import CommerceRunner
from app.commerce.state import CommerceState
from app.commerce.tracer import TraceRecorder

def load_catalog(filepath: str):
    products = []
    attributes_map = {}
    inventory_db = {}
    pricing_db = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row['sku']
            products.append(Product(
                sku=sku,
                category=row['category'],
                title=row['title'],
                description=row['description']
            ))
            # Set dynamic property for the agents to read
            price = int(row['price_paise'])
            products[-1].price_paise = price
            
            pricing_db[sku] = price
            inventory_db[sku] = int(row['inventory'])
            
            attrs = []
            if row.get('brand'): attrs.append(ProductAttribute(sku=sku, attribute_key="brand", attribute_value=row['brand']))
            if row.get('color'): attrs.append(ProductAttribute(sku=sku, attribute_key="color", attribute_value=row['color']))
            attributes_map[sku] = attrs
            
    return products, attributes_map, inventory_db, pricing_db

def load_scenarios(split: str):
    filepath = os.path.join(os.path.dirname(__file__), "..", "data", "scenarios", f"{split}.jsonl")
    scenarios = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                scenarios.append(BuyerIntentSchema.model_validate(data["intent"]))
    return scenarios

def run_benchmark(split: str, system: str):
    print(f"Running benchmark: system={system}, split={split}")
    
    # Load data
    catalog_path = os.path.join(os.path.dirname(__file__), "..", "data", "merchant", "catalog.csv")
    products, attributes_map, inventory_db, pricing_db = load_catalog(catalog_path)
    scenarios = load_scenarios(split)
    
    merchant_policy_db = {"shipping_available": True, "flat_shipping_paise": 0}
    
    results = {
        "system": system,
        "split": split,
        "total_scenarios": len(scenarios),
        "successful_transactions": 0,
        "aborted_transactions": 0,
        "abort_reasons": {},
        "average_latency_ms": 0,
        "total_latency_ms": 0
    }
    
    for intent in scenarios:
        start_time = time.time()
        
        # Instantiate correct agent
        if system == "keyword":
            agent = StructuredBuyer(intent, products, attributes_map)
        elif system == "semantic":
            agent = SemanticBuyer(intent, products, attributes_map)
        elif system == "llm_only":
            adapter = FakeModelAdapter()
            # For llm_only to have any chance, we would need to mock responses. 
            # In benchmark mode without real LLM, it will likely just fail cleanly (which is fine for baseline mechanics)
            # unless we seeded it. It will return empty array and abort.
            agent = LLMBuyer(intent, products, attributes_map, adapter)
        else:
            raise ValueError(f"Unknown system: {system}")
            
        runner = CommerceRunner(agent, inventory_db, pricing_db, merchant_policy_db)
        tracer = TraceRecorder(
            trace_id=f"TR-{intent.intent_id}",
            experiment_id=f"benchmark_{system}_{split}",
            buyer_config=system,
            intent_version="1.0",
            merchant_version=1,
            catalog_version=1
        )
        
        try:
            runner.run_to_precheck()
        except Exception as e:
            pass # Runner handles exceptions internally in state machine
            
        # Sync runner trace events to our tracer
        for event in runner.state_machine.trace_events:
            tracer.record_event(event["event_type"], event["payload"])
        for event in agent.trace_events:
            tracer.record_event(event["event_type"], event["details"])
            
        latency = int((time.time() - start_time) * 1000)
        results["total_latency_ms"] += latency
        
        final_state = runner.state_machine.current_state
        if final_state == CommerceState.READY_FOR_PAYMENT:
            results["successful_transactions"] += 1
        else:
            results["aborted_transactions"] += 1
            # Find reason
            reason = "UNKNOWN"
            for ev in reversed(runner.state_machine.trace_events):
                if ev["event_type"] == "STATE_ENTERED" and ev["payload"]["state"] == CommerceState.ABORTED.value:
                    reason = ev["payload"].get("details", {}).get("reason", "UNKNOWN")
                    break
            results["abort_reasons"][reason] = results["abort_reasons"].get(reason, 0) + 1

    if results["total_scenarios"] > 0:
        results["average_latency_ms"] = results["total_latency_ms"] / results["total_scenarios"]
        
    # Write JSON output
    out_prefix = os.path.join(os.path.dirname(__file__), "..", "data", "evaluations", f"{system}_{split}")
    os.makedirs(os.path.dirname(out_prefix), exist_ok=True)
    
    with open(f"{out_prefix}_results.json", 'w') as f:
        json.dump(results, f, indent=2)
        
    # Write Markdown summary
    with open(f"{out_prefix}_summary.md", 'w') as f:
        f.write(f"# Benchmark Summary: {system} ({split})\n\n")
        f.write(f"- Total Scenarios: {results['total_scenarios']}\n")
        f.write(f"- Successful Transactions: {results['successful_transactions']}\n")
        f.write(f"- Aborted Transactions: {results['aborted_transactions']}\n")
        f.write(f"- Average Latency (ms): {results['average_latency_ms']:.2f}\n\n")
        f.write("## Abort Reasons\n")
        for reason, count in results["abort_reasons"].items():
            f.write(f"- {reason}: {count}\n")
            
    print(f"Completed {system}. Success: {results['successful_transactions']}/{results['total_scenarios']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", required=True)
    parser.add_argument("--system", required=True, choices=["keyword", "semantic", "llm_only", "commercetwin"])
    args = parser.parse_args()
    
    run_benchmark(args.split, args.system)
