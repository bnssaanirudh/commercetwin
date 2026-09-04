import pytest
from app.analytics.verifier import RepairVerifier
from app.commerce.runner import CommerceRunner
from app.commerce.state import CommerceState
from app.buyers.agent import BaseBuyerAgent
from app.models import Product

# ── Shared helpers ─────────────────────────────────────────────────────────────

class MockAgent(BaseBuyerAgent):
    def discover_candidates(self):
        p = Product(sku="SKU-1", merchant_id="m1", title="Widget", category="Electronics")
        p.price_paise = 1000
        return [p]

    def evaluate_candidates(self, products):
        return products

    def select_cart(self):
        p = Product(sku="SKU-1", merchant_id="m1", title="Widget", category="Electronics")
        p.price_paise = 1000
        return [p]


BASE_POLICY = {"shipping_available": True, "flat_shipping_paise": 0}

def _runner(inventory: dict, pricing: dict):
    agent = MockAgent(intent="test", products=[], attributes_map={})
    return CommerceRunner(agent=agent, inventory_db=dict(inventory),
                          pricing_db=dict(pricing), merchant_policy_db=dict(BASE_POLICY))


# ── Tests ───────────────────────────────────────────────────────────────────────

def test_known_good_repair_verified():
    """Fixing inventory exhaustion → VERIFIED."""
    broken_inv = {"SKU-1": 0}
    fixed_inv = {"SKU-1": 10}
    pricing = {"SKU-1": 1000}

    verifier = RepairVerifier()
    result = verifier.verify(
        repair_proposal={"repair_id": "r1"},
        cohort_factory=lambda tid: _runner(broken_inv, pricing),
        cohort_trace_ids=["trace-a", "trace-b"],
        patched_cohort_factory=lambda tid: _runner(fixed_inv, pricing),
    )

    assert result.status == "VERIFIED"
    assert result.before_metrics["successes"] == 0
    assert result.after_metrics["successes"] == 2


def test_ineffective_repair_rejected():
    """Patching the wrong thing still fails → REJECTED."""
    broken_inv = {"SKU-1": 0}
    still_broken_inv = {"SKU-1": 0}   # repair does nothing
    pricing = {"SKU-1": 1000}

    verifier = RepairVerifier()
    result = verifier.verify(
        repair_proposal={"repair_id": "r2"},
        cohort_factory=lambda tid: _runner(broken_inv, pricing),
        cohort_trace_ids=["trace-c"],
        patched_cohort_factory=lambda tid: _runner(still_broken_inv, pricing),
    )

    assert result.status == "REJECTED"
    assert "did not meaningfully improve" in result.trade_off_notes


def test_repair_causing_payment_regression_rejected():
    """If a patched runner enters AMBIGUOUS_REMOTE_STATE without completing → REJECTED."""
    import requests
    from app.chaos.payment_chaos import PaymentChaosAdapter

    class AlwaysTimeoutService:
        def create_order(self, amount_paise, receipt, notes=None):
            raise requests.exceptions.ReadTimeout("chaos")

        def fetch_orders_by_receipt(self, receipt_id):
            return []  # Nothing found → aborts

    broken_inv = {"SKU-1": 0}
    fixed_inv = {"SKU-1": 10}
    pricing = {"SKU-1": 1000}

    def patched_with_chaos(tid):
        agent = MockAgent(intent="test", products=[], attributes_map={})
        adapter = PaymentChaosAdapter(AlwaysTimeoutService())
        return CommerceRunner(agent=agent, inventory_db=dict(fixed_inv),
                              pricing_db=dict(pricing), merchant_policy_db=dict(BASE_POLICY),
                              payment_adapter=adapter)

    verifier = RepairVerifier()
    result = verifier.verify(
        repair_proposal={"repair_id": "r3"},
        cohort_factory=lambda tid: _runner(broken_inv, pricing),
        cohort_trace_ids=["trace-d"],
        patched_cohort_factory=patched_with_chaos,
    )

    assert result.status == "REJECTED"
    assert "regression" in result.trade_off_notes.lower()
