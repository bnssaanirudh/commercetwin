from app.commerce.runner import CommerceRunner, CommerceState
from app.models import Product


class MockAgent:
    def __init__(self, selected_cart=None) -> None:
        self.selected_cart = selected_cart or []
        self.intent = type("I", (), {"intent_id": "mock", "max_budget_paise": 999999})()
        self.trace_events: list = []

    def log_trace(self, event_type: str, details) -> None:
        self.trace_events.append({"event_type": event_type, "details": details})

    def discover_candidates(self) -> list:
        return self.selected_cart

    def evaluate_candidates(self, candidates: list) -> list:
        return candidates

    def select_cart(self, valid_candidates: list) -> list:
        return self.selected_cart


def _product(sku: str = "TEST-1", price: int = 100) -> Product:
    p = Product(sku=sku, title="Test", category="test")
    p.price_paise = price
    return p


def test_runner_happy_path():
    """Valid cart with matching inventory and price must reach READY_FOR_PAYMENT."""
    p = _product("TEST-1", 100)
    runner = CommerceRunner(
        agent=MockAgent([p]),
        inventory_db={"TEST-1": 1},
        pricing_db={"TEST-1": 100},
        merchant_policy_db={"shipping_available": True, "flat_shipping_paise": 0},
    )
    runner.run_to_precheck()
    assert runner.state_machine.current_state == CommerceState.READY_FOR_PAYMENT
    assert runner.final_total_paise == 100


def test_runner_inventory_zero():
    """Out-of-stock item must abort with INVENTORY_ZERO."""
    p = _product("TEST-1", 100)
    runner = CommerceRunner(
        agent=MockAgent([p]),
        inventory_db={"TEST-1": 0},
        pricing_db={"TEST-1": 100},
        merchant_policy_db={"shipping_available": True, "flat_shipping_paise": 0},
    )
    runner.run_to_precheck()
    assert runner.state_machine.current_state == CommerceState.ABORTED
    last = runner.state_machine.trace_events[-1]
    assert last["payload"]["details"]["reason"] == "INVENTORY_ZERO"


def test_runner_price_mismatch_aborts():
    """Cart with stale price (agent 100 vs DB 200) must abort with PRICE_MISMATCH."""
    p = _product("TEST-1", 100)  # agent thinks 100
    runner = CommerceRunner(
        agent=MockAgent([p]),
        inventory_db={"TEST-1": 5},
        pricing_db={"TEST-1": 200},  # DB says 200
        merchant_policy_db={"shipping_available": True, "flat_shipping_paise": 0},
    )
    runner.run_to_precheck()
    assert runner.state_machine.current_state == CommerceState.ABORTED
    last = runner.state_machine.trace_events[-1]
    assert last["payload"]["details"]["reason"] == "PRICE_MISMATCH"


def test_runner_empty_cart_aborts():
    """No valid products must abort with NO_VALID_PRODUCTS_FOUND."""
    runner = CommerceRunner(
        agent=MockAgent([]),  # empty cart
        inventory_db={},
        pricing_db={},
        merchant_policy_db={"shipping_available": True, "flat_shipping_paise": 0},
    )
    runner.run_to_precheck()
    assert runner.state_machine.current_state == CommerceState.ABORTED


def test_runner_shipping_fee_added():
    """Flat shipping fee must be included in the final total."""
    p = _product("TEST-1", 1000)
    runner = CommerceRunner(
        agent=MockAgent([p]),
        inventory_db={"TEST-1": 10},
        pricing_db={"TEST-1": 1000},
        merchant_policy_db={"shipping_available": True, "flat_shipping_paise": 500},
    )
    runner.run_to_precheck()
    assert runner.state_machine.current_state == CommerceState.READY_FOR_PAYMENT
    assert runner.final_total_paise == 1500  # 1000 item + 500 shipping
