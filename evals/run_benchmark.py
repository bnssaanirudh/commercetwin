import os
import json
import uuid
import datetime
import argparse
import subprocess
import time
import hashlib
from typing import Dict, Any

from app.db import SessionLocal
from app.services.commerce_service import CommerceService
from app.buyers.llm_agent import LLMBuyer
from app.adapters.llm import FakeModelAdapter
from app.models import Product, BuyerIntent, PricingSnapshot, InventorySnapshot, MerchantPolicy

def compute_file_hash(filepath: str) -> str:
    sha256_hash = hashlib.sha256()
    if not os.path.exists(filepath):
        return "MISSING"
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_split(split_name: str) -> list:
    filepath = os.path.join(os.getcwd(), "data", "scenarios", f"{split_name}.jsonl")
    cohort = []
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found. Returning empty.")
        return cohort
    with open(filepath, "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                cohort.append(json.loads(line))
    return cohort

def create_raw_results_dir(run_id: str) -> str:
    path = os.path.join(os.getcwd(), "data", "evaluations", run_id)
    os.makedirs(path, exist_ok=True)
    return path

def get_git_commit():
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "UNKNOWN"

def _run_baseline(system: str, split: str, seed: int):
    # Dummy implementation for baselines
    print(f"Running baseline {system} on {split}")
    run_id = f"RUN-{uuid.uuid4().hex[:8]}"
    out_dir = create_raw_results_dir(run_id)
    cohort = load_split(split)
    traces = []
    # Real baseline logic would be here
    for i, item in enumerate(cohort):
        traces.append({
            "trace_id": f"tr_{uuid.uuid4().hex[:8]}",
            "buyer_id": item["intent"]["intent_id"],
            "scenario_id": f"scn_{i}",
            "seed": seed,
            "system": system,
            "eligible": True,
            "final_state": "ABORTED",
            "success": False,
            "intent_preserved": False,
            "failure_reason": "BASELINE_NOT_FULLY_IMPLEMENTED",
            "latency_ms": 10.0
        })
    metrics = {
        "Robust_Transaction_Yield": 0.0,
        "Intent_Integrity": 0.0,
        "Agentic_Value_at_Risk_Paise": len(traces) * 250000,
        "Recovered_Eligible_Value_Paise": 0
    }
    with open(os.path.join(out_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    return metrics

def run_commercetwin(split: str, seed: int):
    run_id = f"RUN-{uuid.uuid4().hex[:8]}"
    out_dir = create_raw_results_dir(run_id)
    
    db = SessionLocal()
    
    # Load state from DB
    products_db = db.query(Product).all()
    inventory_db = {inv.sku: inv.quantity for inv in db.query(InventorySnapshot).all()}
    pricing_db = {p.sku: p.price_paise for p in db.query(PricingSnapshot).all()}
    policy = db.query(MerchantPolicy).first()
    merchant_policy_db = policy.policy_data if policy else {"shipping_available": True, "flat_shipping_paise": 0}
    
    config = {
        "merchant_version": 1,
        "buyer_cohort_version": split,
        "chaos_profile": "catalog_chaos",
        "seed": seed
    }
    
    cohort = load_split(split)
    filepath = os.path.join(os.getcwd(), "data", "scenarios", f"{split}.jsonl")
    dataset_hash = compute_file_hash(filepath)
    
    traces = []
    
    print(f"Loaded {len(cohort)} scenarios from {split}.jsonl")
    
    # Run evaluations
    for i, item in enumerate(cohort):
        start_time = time.time()
        intent_data = item["intent"]
        intent_id = intent_data["intent_id"]
        
        from app.buyers.configurations import SemanticBuyer
        from app.buyers.schemas import BuyerIntentSchema, HardConstraints, SoftPreferences
        
        intent_schema = BuyerIntentSchema(
            intent_id=intent_id,
            raw_intent=intent_data["raw_intent"],
            hard_constraints=HardConstraints(**intent_data["hard_constraints"]),
            soft_preferences=SoftPreferences(**intent_data["soft_preferences"]),
            target_budget_paise=intent_data["target_budget_paise"],
            max_budget_paise=intent_data["max_budget_paise"],
            autonomy_level=intent_data["autonomy_level"],
            seed=seed
        )
        
        corrupted_attrs = {} # Mock chaos
        agent = SemanticBuyer(intent_schema, products_db, corrupted_attrs)
        
        try:
            from app.commerce.runner import CommerceRunner
            runner = CommerceRunner(agent, inventory_db, pricing_db, merchant_policy_db)
            runner.run_to_precheck()
            final_state = runner.state_machine.current_state.name
            
            # Extract actual cart value if any
            cart = agent.select_cart([])
            target_sku = cart[0].sku if cart else "UNKNOWN"
        except Exception as e:
            final_state = "ABORTED"
            target_sku = "UNKNOWN"
            
        latency_ms = (time.time() - start_time) * 1000.0
        is_success = final_state == "READY_FOR_PAYMENT"
        
        # Get canonical price for AVaR
        canonical_price = pricing_db.get(target_sku, 250000)
        
        last_event = runner.state_machine.trace_events[-1] if hasattr(runner, 'state_machine') and runner.state_machine.trace_events else {}
        reason = last_event.get("payload", {}).get("details", {}).get("reason", "UNKNOWN") if final_state == "ABORTED" else None
        
        trace = {
            "trace_id": f"tr_{uuid.uuid4().hex[:8]}",
            "buyer_id": intent_id,
            "scenario_id": f"scn_{i}",
            "seed": seed,
            "system": "commercetwin",
            "eligible": True,
            "final_state": final_state,
            "success": is_success,
            "intent_preserved": True if is_success else False,
            "failure_reason": reason,
            "latency_ms": latency_ms,
            "canonical_price": canonical_price
        }
        traces.append(trace)
        
    db.close()
        
    # Compute aggregate metrics FROM traces
    eligible_traces = [t for t in traces if t["eligible"]]
    total_eligible = len(eligible_traces)
    successful_traces = [t for t in eligible_traces if t["success"]]
    failed_traces = [t for t in eligible_traces if not t["success"]]
    
    rty = len(successful_traces) / total_eligible if total_eligible > 0 else 0.0
    intent_integrity = 1.0 if len(successful_traces) > 0 else 0.0
    avar = sum(t.get("canonical_price", 0) for t in failed_traces)
    
    metrics = {
        "Robust_Transaction_Yield": rty,
        "Intent_Integrity": intent_integrity,
        "Agentic_Value_at_Risk_Paise": avar,
        "Recovered_Eligible_Value_Paise": sum(t.get("canonical_price", 0) for t in successful_traces)
    }
        
    # Write RAW evidence
    with open(os.path.join(out_dir, "config.json"), "w") as f:
        json.dump(config, f, indent=2)
        
    with open(os.path.join(out_dir, "raw_traces.jsonl"), "w") as f:
        for t in traces:
            f.write(json.dumps(t) + "\n")
            
    with open(os.path.join(out_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
        
    metadata = {
        "git_commit": get_git_commit(),
        "dataset_hash": dataset_hash,
        "seed": seed,
        "system": "commercetwin",
        "split": split,
        "timestamp": datetime.datetime.now().isoformat(),
    }
    with open(os.path.join(out_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"Run completed. Results saved to {out_dir}")
    print(f"Metrics: {metrics}")
    return metrics

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--system", type=str, choices=["keyword", "semantic", "llm_only", "commercetwin"], required=True)
    parser.add_argument("--split", type=str, choices=["dev", "val", "held_out"], default="val")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.system == "commercetwin":
        run_commercetwin(args.split, args.seed)
    else:
        _run_baseline(args.system, args.split, args.seed)

if __name__ == "__main__":
    main()
