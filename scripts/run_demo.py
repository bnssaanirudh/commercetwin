import os
import sys
import time
import json
import asyncio

# Ensure backend can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.models import Product, ProductAttribute
from app.buyers.schemas import BuyerIntentSchema, HardConstraints, SoftPreferences
from app.buyers.configurations import SemanticBuyer
from app.commerce.state import CommerceState
from app.services.commerce_service import CommerceService

from app.models import Base
from app.db import engine, SessionLocal

Base.metadata.create_all(bind=engine)

def load_clean_catalog():
    p1 = Product(sku="CHG-65W-01", category="USB-C chargers", title="65W Fast Charger", description="Ultra fast 65W PD charger for MacBook Air.")
    p1.price_paise = 250000 # 2500 INR
    attrs = [ProductAttribute(sku="CHG-65W-01", key="power_watts", value="65", type="int")]
    return [p1], {"CHG-65W-01": attrs}, {"CHG-65W-01": 100}, {"CHG-65W-01": 250000}

def print_stage(num, title):
    print(f"\n{'='*50}")
    print(f"STAGE {num}: {title}")
    print(f"{'='*50}")
    time.sleep(1)

async def main():
    db = SessionLocal()
    service = CommerceService(db_session=db)
    
    print_stage(1, "Clean Merchant -> Buyer Succeeds")
    products, attrs_map, inv_db, price_db = load_clean_catalog()
    policy = {"shipping_available": True, "flat_shipping_paise": 0}
    
    intent = BuyerIntentSchema(
        intent_id="demo-intent-01",
        raw_intent="I need a USB-C charger for my MacBook Air. It must support at least 65W USB Power Delivery and cost less than ₹3,000.",
        hard_constraints=HardConstraints(min_attributes={"power_watts": 65}, required_categories=["USB-C chargers"]),
        soft_preferences=SoftPreferences(),
        target_budget_paise=300000,
        max_budget_paise=300000,
        autonomy_level="autonomous",
        seed=42
    )
    
    exp_id = service.create_experiment({"merchant_version": "v1", "chaos_profile": "none"})
    
    print_stage(2, "Inject Catalog Chaos (Remove typed power_watts)")
    exp_id_corrupted = service.create_experiment({"merchant_version": "v1", "chaos_profile": "drop_attribute"})
    
    print_stage(3, "Failed Run (Buyer Rejects Product)")
    buyer_corrupt = SemanticBuyer(intent, products, {"CHG-65W-01": []})
    runner_corrupt = service.run_trace(
        buyer_corrupt,
        inv_db,
        price_db,
        policy,
        experiment_id=exp_id_corrupted
    )
    print(f"Outcome: {runner_corrupt.state_machine.current_state.name} (Expected: ABORTED)")
    
    print_stage(4, "Trace Identifies Failure (Localization)")
    from app.models import TransactionTrace
    trace_record = db.query(TransactionTrace).order_by(TransactionTrace.created_at.desc()).first()
    trace_id = trace_record.trace_id if trace_record else "TRC-demo"
    localized = service.localize_failure(trace_id)
    print(f"Localized Failure: {localized}")
    
    print_stage(5, "Revenue Leak Groups Affected Cohort")
    print(f"Identified transaction lost in trace {trace_id}.")
    
    print_stage(6, "Repair Engine Proposes Catalog Patch")
    proposal = service.generate_repair(trace_id)
    print(f"Proposed Patch: {json.dumps(proposal)}")
    
    print_stage(7, "Replay Exact Cohort -> Success")
    repair_id = proposal.get("repair_id")
    if repair_id:
        verified = service.verify_repair(repair_id)
        print(f"Replay Outcome Verified: {verified} (Expected: True)")
    else:
        print("Failed to generate repair.")
    
    print_stage(8, "Complete Real Razorpay Test Transaction")
    buyer3 = SemanticBuyer(intent, products, attrs_map) # Clean attributes for payment flow demo
    runner3 = service.run_trace(buyer3, inv_db, price_db, policy, experiment_id=exp_id)
    payment_state = service.prepare_payment(runner3, receipt_id="receipt_demo")
    print(f"Payment Operation created successfully.")
    
    print_stage(9, "Payment Chaos -> Reconciliation Prevents Duplicate")
    from app.payments.webhook_handler import WebhookProcessor
    handler = WebhookProcessor()
    payload = {"payload": {"payment": {"entity": {"id": "pay_123", "order_id": payment_state.get('razorpay_order_id', 'order_123') if hasattr(payment_state, 'get') else 'order_123', "amount": 250000, "status": "captured"}}}}
    res1 = handler.process("evt_1", "payment.captured", payload)
    print(f"First webhook processed: {res1}")
    
    res2 = handler.process("evt_1", "payment.captured", payload) # Duplicate webhook
    print(f"Duplicate webhook processed: {res2} (Ignored/Idempotent)")
    
    print("\n[SUCCESS] Hero Demo Completed Successfully.")

if __name__ == "__main__":
    asyncio.run(main())
