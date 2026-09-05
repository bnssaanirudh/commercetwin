import sys
import os

# Ensure backend module is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.models import Product
from app.commerce.runner import CommerceRunner
from app.commerce.state import CommerceState

class MockAgent:
    def __init__(self, selected_cart=None):
        self.selected_cart = selected_cart or []
        # Provide intent with a high budget so budget check never triggers in regression tests
        self.intent = type("Intent", (), {"intent_id": "regression", "max_budget_paise": 99999999})()

    def discover_candidates(self):
        return []

    def evaluate_candidates(self, candidates):
        return self.selected_cart

    def select_cart(self, valid_candidates):
        return self.selected_cart

def run_regression_suite():
    print("Starting CommerceTwin Deterministic Regression Suite...")
    
    p1 = Product(sku="SKU-1", title="Item 1", category="Cat")
    setattr(p1, 'price_paise', 100)
    p2 = Product(sku="SKU-2", title="Item 2", category="Cat")
    setattr(p2, 'price_paise', 200)
    products = [p1, p2]
    
    # Test 1: Successful Path
    print("Test 1: Happy Path to Payment")
    runner1 = CommerceRunner(
        agent=MockAgent(selected_cart=[products[0]]),
        inventory_db={"SKU-1": 10},
        pricing_db={"SKU-1": 100},
        merchant_policy_db={"shipping_available": True, "flat_shipping_paise": 0}
    )
    runner1.run_to_precheck()
    if runner1.state_machine.current_state == CommerceState.ABORTED:
        print("Test 1 aborted. Traces:", runner1.state_machine.trace_events)
    assert runner1.state_machine.current_state == CommerceState.READY_FOR_PAYMENT, f"Expected READY_FOR_PAYMENT, got {runner1.state_machine.current_state}"
    assert runner1.final_total_paise == 100
    
    # Test 2: Inventory Out of Stock
    print("Test 2: Precheck Aborts on Zero Inventory")
    runner2 = CommerceRunner(
        agent=MockAgent(selected_cart=[products[0]]),
        inventory_db={"SKU-1": 0},
        pricing_db={"SKU-1": 100},
        merchant_policy_db={"shipping_available": True, "flat_shipping_paise": 0}
    )
    runner2.run_to_precheck()
    assert runner2.state_machine.current_state == CommerceState.ABORTED
    assert runner2.state_machine.trace_events[-1]["payload"]["details"].get("reason") == "INVENTORY_ZERO"
    
    # Test 3: Price Mismatch
    print("Test 3: Precheck Aborts on Price Mismatch")
    item = Product(sku="SKU-1", title="Item 1", category="Cat")
    setattr(item, 'price_paise', 50) # Agent hallucinated a cheaper price
    runner3 = CommerceRunner(
        agent=MockAgent(selected_cart=[item]),
        inventory_db={"SKU-1": 10},
        pricing_db={"SKU-1": 100}, # Real price is 100
        merchant_policy_db={"shipping_available": True, "flat_shipping_paise": 0}
    )
    runner3.run_to_precheck()
    assert runner3.state_machine.current_state == CommerceState.ABORTED
    assert runner3.state_machine.trace_events[-1]["payload"]["details"].get("reason") == "PRICE_MISMATCH"
    
    # Test 4: Shipping Unavailable
    print("Test 4: Precheck Aborts on Shipping Unavailable")
    runner4 = CommerceRunner(
        agent=MockAgent(selected_cart=[products[0]]),
        inventory_db={"SKU-1": 10},
        pricing_db={"SKU-1": 100},
        merchant_policy_db={"shipping_available": False, "flat_shipping_paise": 0}
    )
    runner4.run_to_precheck()
    assert runner4.state_machine.current_state == CommerceState.ABORTED
    assert runner4.state_machine.trace_events[-1]["payload"]["details"].get("reason") == "SHIPPING_UNAVAILABLE"
    
    print("Regression Suite Passed Successfully. 100% Deterministic Core invariants validated.")
    sys.exit(0)

if __name__ == "__main__":
    try:
        run_regression_suite()
    except AssertionError as e:
        print(f"REGRESSION FAILED: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"REGRESSION FAILED WITH UNEXPECTED ERROR: {str(e)}")
        sys.exit(1)
