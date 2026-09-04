import pytest
from app.buyers.schemas import BuyerIntentSchema, HardConstraints, SoftPreferences
from app.models import Product
from app.buyers.configurations import StructuredBuyer
from app.commerce.runner import CommerceRunner
from app.commerce.state import CommerceState, InvalidStateTransitionError

@pytest.fixture
def mock_catalog():
    p1 = Product(sku="SKU-1", category="cables", title="Cable")
    p1.price_paise = 1000
    p2 = Product(sku="SKU-2", category="adapters", title="Adapter")
    p2.price_paise = 2000
    return [p1, p2]

@pytest.fixture
def intent():
    return BuyerIntentSchema(
        intent_id="INT-1",
        raw_intent="I need a cable",
        hard_constraints=HardConstraints(required_categories=["cables"]),
        soft_preferences=SoftPreferences(),
        target_budget_paise=5000,
        max_budget_paise=10000,
        autonomy_level="supervised",
        seed=42
    )

@pytest.fixture
def base_dbs():
    return {
        "inventory": {"SKU-1": 10, "SKU-2": 5},
        "pricing": {"SKU-1": 1000, "SKU-2": 2000},
        "policy": {"shipping_available": True, "flat_shipping_paise": 500}
    }

def test_valid_journey(intent, mock_catalog, base_dbs):
    agent = StructuredBuyer(intent, mock_catalog, {})
    runner = CommerceRunner(agent, base_dbs["inventory"], base_dbs["pricing"], base_dbs["policy"])
    
    runner.run_to_precheck()
    assert runner.state_machine.current_state == CommerceState.READY_FOR_PAYMENT
    assert runner.final_total_paise == 1500 # 1000 for item + 500 shipping

def test_no_valid_product(intent, mock_catalog, base_dbs):
    # Require something not in catalog
    intent.hard_constraints.required_categories = ["laptops"]
    agent = StructuredBuyer(intent, mock_catalog, {})
    runner = CommerceRunner(agent, base_dbs["inventory"], base_dbs["pricing"], base_dbs["policy"])
    
    runner.run_to_precheck()
    assert runner.state_machine.current_state == CommerceState.ABORTED
    assert runner.state_machine.trace_events[-1]["payload"]["details"]["reason"] == "NO_VALID_PRODUCTS_FOUND"

def test_invalid_cart(intent, mock_catalog, base_dbs):
    # Require 2 items but budget too low
    intent.hard_constraints.required_categories = ["cables", "adapters"]
    intent.max_budget_paise = 1500 # Cost is 3000
    agent = StructuredBuyer(intent, mock_catalog, {})
    runner = CommerceRunner(agent, base_dbs["inventory"], base_dbs["pricing"], base_dbs["policy"])
    
    runner.run_to_precheck()
    assert runner.state_machine.current_state == CommerceState.ABORTED
    assert runner.state_machine.trace_events[-1]["payload"]["details"]["reason"] == "INVALID_CART_CONSTRUCTED"

def test_inventory_zero(intent, mock_catalog, base_dbs):
    base_dbs["inventory"]["SKU-1"] = 0
    agent = StructuredBuyer(intent, mock_catalog, {})
    runner = CommerceRunner(agent, base_dbs["inventory"], base_dbs["pricing"], base_dbs["policy"])
    
    runner.run_to_precheck()
    assert runner.state_machine.current_state == CommerceState.ABORTED
    assert runner.state_machine.trace_events[-1]["payload"]["details"]["reason"] == "INVENTORY_ZERO"

def test_price_mismatch(intent, mock_catalog, base_dbs):
    # Catalog has 1000, DB has 1500
    base_dbs["pricing"]["SKU-1"] = 1500
    agent = StructuredBuyer(intent, mock_catalog, {})
    runner = CommerceRunner(agent, base_dbs["inventory"], base_dbs["pricing"], base_dbs["policy"])
    
    runner.run_to_precheck()
    assert runner.state_machine.current_state == CommerceState.ABORTED
    assert runner.state_machine.trace_events[-1]["payload"]["details"]["reason"] == "PRICE_MISMATCH"

def test_shipping_unavailable(intent, mock_catalog, base_dbs):
    base_dbs["policy"]["shipping_available"] = False
    agent = StructuredBuyer(intent, mock_catalog, {})
    runner = CommerceRunner(agent, base_dbs["inventory"], base_dbs["pricing"], base_dbs["policy"])
    
    runner.run_to_precheck()
    assert runner.state_machine.current_state == CommerceState.ABORTED
    assert runner.state_machine.trace_events[-1]["payload"]["details"]["reason"] == "SHIPPING_UNAVAILABLE"

def test_repeated_transition(intent, mock_catalog, base_dbs):
    agent = StructuredBuyer(intent, mock_catalog, {})
    runner = CommerceRunner(agent, base_dbs["inventory"], base_dbs["pricing"], base_dbs["policy"])
    
    # Manually force a bad state transition
    with pytest.raises(InvalidStateTransitionError):
        runner.state_machine.transition_to(CommerceState.READY_FOR_PAYMENT)
