import pytest
import copy
from app.models import Product
from app.chaos.engine import ChaosEngine
from app.buyers.schemas import BuyerIntentSchema, HardConstraints, SoftPreferences
from app.buyers.configurations import StructuredBuyer
from app.commerce.runner import CommerceRunner
from app.commerce.state import CommerceState

@pytest.fixture
def mock_data():
    p1 = Product(sku="SKU-1", category="cables", title="Basic Cable", description="A cable")
    p1.price_paise = 1000
    
    products = [p1]
    inventory = {"SKU-1": 1}
    pricing = {"SKU-1": 1000}
    policy = {"shipping_available": True, "flat_shipping_paise": 0}
    
    intent = BuyerIntentSchema(
        intent_id="INT-COMCHAOS-1",
        raw_intent="I need a cable",
        hard_constraints=HardConstraints(required_categories=["cables"]),
        soft_preferences=SoftPreferences(),
        target_budget_paise=5000,
        max_budget_paise=10000,
        autonomy_level="supervised",
        seed=42
    )
    
    return products, inventory, pricing, policy, intent

def test_stale_inventory_blocks_payment(mock_data):
    products, inventory, pricing, policy, intent = mock_data
    
    engine = ChaosEngine()
    engine.apply(products, inventory, pricing, policy, seed=42, profile="commerce")
    cloned_products, cloned_inv, cloned_pricing, cloned_policy = engine.get_state()
    
    agent = StructuredBuyer(intent, cloned_products, {})
    runner = CommerceRunner(agent, cloned_inv, cloned_pricing, cloned_policy, chaos_engine=engine)
    
    runner.run_to_precheck()
    assert runner.state_machine.current_state == CommerceState.READY_FOR_PAYMENT
    
    # Process payment
    runner.process_payment()
    
    # Chaos engine triggered at EVALUATION and zeroed the inventory.
    # So payment validation should catch it.
    assert runner.state_machine.current_state == CommerceState.ABORTED
    reason = runner.state_machine.trace_events[-1]["payload"]["details"]["reason"]
    assert "STALE" in reason or "INVENTORY" in reason

def test_stale_price_blocks_payment(mock_data):
    products, inventory, pricing, policy, intent = mock_data
    
    engine = ChaosEngine()
    # Change seed to trigger a different chaos sequence if needed, but the current commerce chaos
    # implementation statically injects PRICE_HIKE, INV_ZERO, and CHK_NOSHIP for the single item.
    # Wait, the current implementation applies all three. Let's isolate the price one.
    # To isolate, we can just apply a manual injection.
    
    engine._clone_state(products, inventory, pricing, policy)
    from app.chaos.engine import ChaosInjection
    engine.pending_injections = [
        ChaosInjection(
            chaos_id="PRICE_HIKE_SKU-1",
            family="price",
            target="SKU-1",
            severity="medium",
            seed=1,
            before_state={"price_paise": 1000},
            mutated_state={"price_paise": 2000},
            reversible_patch={"sku": "SKU-1", "price_paise": 1000},
            start_boundary="READY_FOR_PAYMENT",
            end_boundary="COMPLETED"
        )
    ]
    
    cloned_products, cloned_inv, cloned_pricing, cloned_policy = engine.get_state()
    agent = StructuredBuyer(intent, cloned_products, {})
    runner = CommerceRunner(agent, cloned_inv, cloned_pricing, cloned_policy, chaos_engine=engine)
    
    runner.run_to_precheck()
    assert runner.state_machine.current_state == CommerceState.READY_FOR_PAYMENT
    
    runner.process_payment()
    
    assert runner.state_machine.current_state == CommerceState.ABORTED
    reason = runner.state_machine.trace_events[-1]["payload"]["details"]["reason"]
    assert reason == "STALE_PRICE"

def test_shipping_unavailable_blocks_payment(mock_data):
    products, inventory, pricing, policy, intent = mock_data
    engine = ChaosEngine()
    
    engine._clone_state(products, inventory, pricing, policy)
    from app.chaos.engine import ChaosInjection
    engine.pending_injections = [
        ChaosInjection(
            chaos_id="CHK_NOSHIP",
            family="checkout",
            target="merchant_policy",
            severity="high",
            seed=1,
            before_state={"shipping_available": True},
            mutated_state={"shipping_available": False},
            reversible_patch={"key": "shipping_available", "value": True},
            start_boundary="READY_FOR_PAYMENT",
            end_boundary="COMPLETED"
        )
    ]
    
    cloned_products, cloned_inv, cloned_pricing, cloned_policy = engine.get_state()
    agent = StructuredBuyer(intent, cloned_products, {})
    runner = CommerceRunner(agent, cloned_inv, cloned_pricing, cloned_policy, chaos_engine=engine)
    
    runner.run_to_precheck()
    assert runner.state_machine.current_state == CommerceState.READY_FOR_PAYMENT
    
    runner.process_payment()
    
    assert runner.state_machine.current_state == CommerceState.ABORTED
    reason = runner.state_machine.trace_events[-1]["payload"]["details"]["reason"]
    assert reason == "STALE_SHIPPING_POLICY"
