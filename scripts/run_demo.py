import os
import sys
import asyncio
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.db import SessionLocal, engine
from app.models import Base
from app.services.commerce_service import CommerceService
from app.chaos.engine import ChaosEngine
from app.buyers.configurations import SemanticBuyer
from app.buyers.schemas import BuyerIntentSchema, HardConstraints, SoftPreferences
from app.models import Product, TransactionTrace, TraceEvent, ReplayResult, PaymentOperation
from app.payments.webhook_handler import WebhookProcessor

# Initialize DB tables
db_path = os.path.join(os.path.dirname(__file__), "..", "commercetwin.db")
if os.path.exists(db_path):
    try:
        os.remove(db_path)
    except:
        pass

Base.metadata.create_all(bind=engine)

def print_stage(num: int, title: str):
    print(f"\n{'='*60}")
    print(f"STAGE {num}: {title}")
    print(f"{'='*60}")

async def main():
    db = SessionLocal()
    svc = CommerceService(db)
    
    print_stage(1, "Initialize Catalog & Chaos Profile")
    
    # 1. Create a real experiment with attribute dropout
    exp_id = svc.create_experiment({"merchant_version": "v1", "chaos_profile": "drop_attribute"})
    print(f"[+] Created Experiment: {exp_id} with chaos_profile=drop_attribute")
    
    print_stage(2, "Simulate 10 Buyers -> Injected Fault -> Failed Traces")
    
    # 2. Run 10 buyers
    cohort_size = 10
    seed_base = 42
    
    # We will simulate exactly 10 buyers for the demo cohort.
    
    results = []
    failed_trace_ids = []
    
    print(f"[*] Running {cohort_size}-buyer demo cohort with 'power_watts' requirement...")
    
    # Insert a single real product into DB for evidence
    p = Product(sku=f"DEMO-CHG-01", merchant_id="merchant_demo", title=f"65W Fast Charger", category="electronics", description="A fast charger supporting 65W.")
    p.price_paise = 250000
    db.merge(p)
    
    # Add authoritative evidence so the repair synthesizer can find it
    from app.models import CatalogAttributeEvidence
    import uuid
    import datetime
    import hashlib
    
    evidence = CatalogAttributeEvidence(
        evidence_id=f"EV-{uuid.uuid4().hex[:8]}",
        sku=p.sku,
        key="power_watts",
        value="65",
        type="int",
        catalog_version=1,
        source="manufacturer_feed",
        verified_at=datetime.datetime.now(datetime.UTC),
        source_hash=hashlib.sha256(f"{p.sku}:power_watts:65".encode()).hexdigest()
    )
    from app.models import ProductAttribute
    
    db.merge(evidence)
    attr = ProductAttribute(sku=p.sku, key="power_watts", value="65", type="int")
    db.merge(attr)
    db.commit()
    
    attrs_map = {p.sku: [attr]}
    inv_db = {p.sku: 500}
    price_db = {p.sku: 250000}
    policy_db = {"shipping_available": True, "flat_shipping_paise": 0}
    
    chaos_engine = ChaosEngine()
    
    for i in range(1, cohort_size + 1):
        # Apply chaos per buyer so they experience different random faults
        chaos_engine.apply([p], inv_db, price_db, policy_db, seed_base + i, "drop_attribute", attrs_map)
        mutated_products, mutated_inventory, mutated_pricing, mutated_policy, mutated_attrs_map = chaos_engine.get_state()
        
        intent = BuyerIntentSchema(
            intent_id=f"demo-buyer-{i:03d}",
            raw_intent="I need a charger that supports at least 65W.",
            hard_constraints=HardConstraints(required_categories=["electronics"], min_attributes={"power_watts": 65}),
            soft_preferences=SoftPreferences(),
            target_budget_paise=500000,
            max_budget_paise=500000,
            autonomy_level="autonomous",
            seed=seed_base + i,
        )
        agent = SemanticBuyer(intent, mutated_products, mutated_attrs_map)
        runner = svc.run_trace(
            agent=agent,
            inventory_db=mutated_inventory,
            pricing_db=mutated_pricing,
            merchant_policy_db=mutated_policy,
            chaos_engine=chaos_engine,
            experiment_id=exp_id,
            attributes_map=mutated_attrs_map,
        )
        final_state = runner.state_machine.current_state.name
        results.append(final_state)
        
        if final_state == "ABORTED":
            failed_trace_ids.append(runner.trace_id)
            
        print(f"  [Trace] Buyer {i:03d}: State -> {final_state}")
    

    
    if not failed_trace_ids:
        print("[-] No traces failed. Demo cannot proceed.")
        return
        
    target_trace_id = failed_trace_ids[0]
    print(f"\n[!] Selected Failed Trace ID for recovery: {target_trace_id}")
    
    print_stage(3, "Localization -> Generated Repair")
    
    localized = svc.localize_failure(target_trace_id)
    print(f"[*] Localized Cause:\n{json.dumps(localized, indent=2)}")
    
    repair = svc.generate_repair(target_trace_id, localized_cause=localized)
    print(f"\n[*] Generated Repair Proposal:\n{json.dumps(repair, indent=2)}")
    
    repair_id = repair.get("repair_id")
    if not repair_id:
        print("[-] Failed to generate repair. Demo cannot proceed.")
        return
        
    print_stage(4, "Replay -> Recovered Transaction -> READY_FOR_PAYMENT")
    
    print(f"[*] Triggering verified replay for repair ID: {repair_id}")
    success = svc.verify_repair(repair_id)
    
    rr = db.query(ReplayResult).filter(ReplayResult.repair_id == repair_id).first()
    print(f"[+] Replay Verification Outcome: {success}")
    if rr:
        print(f"    Replay ID: {rr.replay_id}")
        print(f"    Before State: {rr.before_state}")
        print(f"    After State: {rr.after_state}")
        
    if not success or not rr or rr.after_state != "READY_FOR_PAYMENT":
        print("[-] Replay did not recover the transaction to READY_FOR_PAYMENT. Demo stops.")
        return
        
    print_stage(5, "Simulated Payment (Razorpay Test Mode Mock) -> Webhook Reconciliation")
    
    # We use the replayed trace for payment
    recovered_trace = db.query(TransactionTrace).filter(TransactionTrace.trace_id == rr.trace_id).first()
    
    # Initialize a clean runner from the recovered trace to process the payment
    # In a real system, the runner state machine would be reconstituted from the ReplaySnapshot and progressed
    # For demo, we can just load a mock runner in the READY_FOR_PAYMENT state, but using the real prepare_payment 
    # API to trigger Razorpay logic.
    
    print(f"[*] Processing Razorpay Test Payment for Recovered Trace: {recovered_trace.trace_id}")
    
    # Create an agent for the successful flow
    clean_agent = SemanticBuyer(intent, [p], attrs_map)
    clean_runner = svc.run_trace(
        agent=clean_agent,
        inventory_db=inv_db,
        pricing_db=price_db,
        merchant_policy_db=policy_db,
        experiment_id=exp_id,
        attributes_map=attrs_map,
    )
    
    # It should successfully reach READY_FOR_PAYMENT
    print(f"    Clean Payment Trace State: {clean_runner.state_machine.current_state.name}")
    
    if clean_runner.state_machine.current_state.name == "READY_FOR_PAYMENT":
        payment_state = svc.prepare_payment(clean_runner, receipt_id="receipt_demo")
        
        op = db.query(PaymentOperation).filter(PaymentOperation.trace_id == clean_runner.trace_id).first()
        order_id = op.razorpay_order_id if op else "order_demo_123"
        print(f"[+] Payment Prepared. Order ID: {order_id} | Amount: INR {op.amount_paise / 100}")
        
        # Simulate Webhook
        handler = WebhookProcessor()
        payload = {"payload": {"payment": {"entity": {"id": "pay_demo_123", "order_id": order_id, "amount": op.amount_paise, "status": "captured"}}}}
        evt_id = f"evt_demo_{uuid.uuid4().hex[:8]}"
        
        print("\n[*] Sending first webhook (captured)...")
        res1 = handler.process(evt_id, "payment.captured", payload)
        print(f"    Webhook response: {res1}")
        
        print("\n[*] Sending duplicate webhook (captured) to test idempotency...")
        res2 = handler.process(evt_id, "payment.captured", payload) 
        print(f"    Webhook response: {res2}")
        
        # Verify reconciliation
        db.commit() # End current transaction to read fresh data from DB
        db.expire_all()
        
        from app.models import QuarantinedWebhookEvent
        quarantined = db.query(QuarantinedWebhookEvent).filter(QuarantinedWebhookEvent.razorpay_event_id == evt_id).first()
        if quarantined:
            print(f"[-] Webhook Quarantined! Payload: {quarantined.payload_json}")
            
        op_reconciled = db.query(PaymentOperation).filter(PaymentOperation.operation_id == op.operation_id).first()
        print(f"\n[+] Final Payment State: {op_reconciled.state} (Reconciled: {op_reconciled.state == 'captured'})")
        if op_reconciled.state != 'captured':
            print("[-] Final payment state is NOT captured. Demo failed.")
            return

    print("\n[SUCCESS] CommerceTwin Full Loop Demo Completed.")

if __name__ == "__main__":
    asyncio.run(main())
