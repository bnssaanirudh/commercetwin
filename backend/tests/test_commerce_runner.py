import pytest
from app.models import Product
from app.commerce.runner import CommerceRunner, CommerceState

class MockAgent:
    def __init__(self, selected_cart=None):
        self.selected_cart = selected_cart or []
    def discover_candidates(self): return []
    def evaluate_candidates(self, candidates): return self.selected_cart
    def select_cart(self, valid_candidates): return self.selected_cart

def test_runner_happy_path():
    p = Product(sku="TEST-1", title="Test", category="Test")
    setattr(p, 'price_paise', 100)
    runner = CommerceRunner(
        agent=MockAgent([p]),
        inventory_db={"TEST-1": 1},
        pricing_db={"TEST-1": 100},
        merchant_policy_db={"shipping_available": True, "flat_shipping_paise": 0}
    )
    runner.run_to_precheck()
    assert runner.state_machine.current_state == CommerceState.READY_FOR_PAYMENT
    assert runner.final_total_paise == 100

def test_runner_inventory_zero():
    p = Product(sku="TEST-1", title="Test", category="Test")
    setattr(p, 'price_paise', 100)
    runner = CommerceRunner(
        agent=MockAgent([p]),
        inventory_db={"TEST-1": 0}, # Out of stock
        pricing_db={"TEST-1": 100},
        merchant_policy_db={"shipping_available": True, "flat_shipping_paise": 0}
    )
    runner.run_to_precheck()
    assert runner.state_machine.current_state == CommerceState.ABORTED
    assert runner.state_machine.trace_events[-1]["payload"]["details"]["reason"] == "INVENTORY_ZERO"
