from app.analytics.causal import CausalLocalizer
from app.analytics.repair import RepairSynthesizer
from app.commerce.runner import CommerceState
from app.models import Product


def test_repair_synthesizer_patch_schema():
    """
    Verifies that the RepairSynthesizer rejects buyer-targeting patches
    and accepts valid catalog patches.
    """
    from app.analytics.repair import RepairGuardrailViolation

    synth = RepairSynthesizer(None)

    # Valid catalog patch should not raise
    result = synth.synthesize(
        failure_cluster={"failure_id": "test"},
        repair_type="CATALOG_SCHEMA_PATCH",
        proposed_patch={"target_sku": "SKU-1", "operations": [{"key": "power", "new_value": "65W"}]},
    )
    assert result is not None
    assert "repair_id" in result

    # Buyer-targeting patch must be rejected
    import pytest
    with pytest.raises(RepairGuardrailViolation):
        synth.synthesize(
            failure_cluster={"failure_id": "test"},
            repair_type="CATALOG_SCHEMA_PATCH",
            proposed_patch={"buyer_constraints": "hacked"},
        )


def test_repair_synthesizer_blocks_financial_patch():
    """Repair must not allow modifying payment_amount or financial_policy."""
    from app.analytics.repair import RepairGuardrailViolation

    synth = RepairSynthesizer(None)

    import pytest
    with pytest.raises(RepairGuardrailViolation):
        synth.synthesize(
            failure_cluster={"failure_id": "test"},
            repair_type="CATALOG_SCHEMA_PATCH",
            proposed_patch={"payment_amount": 1},
        )


def test_unused_product_model():
    """Sanity check: Product model can be instantiated."""
    p = Product(sku="TEST", title="Test Product", category="test")
    assert p.sku == "TEST"


class MockAgent:
    def __init__(self):
        self.intent = type("Intent", (), {
            "hard_constraints": type("HC", (), {
                "required_attributes": {"power": "65W"}
            })()
        })()
        self.attributes_map = {"SKU-1": []}

    def discover_candidates(self):
        return []
    def evaluate_candidates(self, candidates):
        return candidates
    def select_cart(self, valid):
        return valid


class MockRunner:
    def __init__(self, fails_due_to=None):
        self.inventory_db = {"SKU-1": 10}
        self.pricing_db = {"SKU-1": 100}
        self.merchant_policy_db = {}
        self.agent = MockAgent()
        self.fails_due_to = fails_due_to
        self.state_machine = type("SM", (), {"current_state": CommerceState.ABORTED})()
        self.cart = [Product(sku="SKU-1", title="Test", category="test")]
        self.cart[0].price_paise = 100

    def run_to_precheck(self):
        if self.fails_due_to == "MISSING_REQUIRED_ATTRIBUTE":
            # Check if attribute was injected by localizer
            attrs = self.agent.attributes_map.get("SKU-1", [])
            has_power = any(a.key == "power" and a.value == "65W" for a in attrs)
            if has_power:
                self.state_machine.current_state = CommerceState.READY_FOR_PAYMENT
            else:
                self.state_machine.current_state = CommerceState.ABORTED
        elif self.fails_due_to == "STALE_INVENTORY":
            if self.inventory_db.get("SKU-1", 0) > 0:
                self.state_machine.current_state = CommerceState.READY_FOR_PAYMENT
            else:
                self.state_machine.current_state = CommerceState.ABORTED
        elif self.fails_due_to == "STALE_PRICE":
            if self.pricing_db.get("SKU-1") == 100:
                self.state_machine.current_state = CommerceState.READY_FOR_PAYMENT
            else:
                self.state_machine.current_state = CommerceState.ABORTED
        else:
            self.state_machine.current_state = CommerceState.READY_FOR_PAYMENT

    def process_payment(self):
        pass


def test_causal_localizer_missing_attribute():
    def factory():
        return MockRunner(fails_due_to="MISSING_REQUIRED_ATTRIBUTE")

    localizer = CausalLocalizer(
        runner_factory=factory,
        base_inventory={"SKU-1": 10},
        base_pricing={"SKU-1": 100},
        base_policy={}
    )
    result = localizer.localize("MISSING_REQUIRED_ATTRIBUTE", "SKU-1")
    assert result["hypothesis"] == "missing_typed_attribute"
    assert result["confidence"] == "HIGH"


def test_causal_localizer_stale_inventory():
    def factory():
        return MockRunner(fails_due_to="STALE_INVENTORY")

    localizer = CausalLocalizer(
        runner_factory=factory,
        base_inventory={"SKU-1": 0},
        base_pricing={"SKU-1": 100},
        base_policy={}
    )
    result = localizer.localize("STALE_INVENTORY", "SKU-1")
    assert result["hypothesis"] == "stale inventory"
    assert result["confidence"] == "HIGH"


def test_causal_localizer_stale_price():
    def factory():
        return MockRunner(fails_due_to="STALE_PRICE")

    localizer = CausalLocalizer(
        runner_factory=factory,
        base_inventory={"SKU-1": 10},
        base_pricing={"SKU-1": 50}, # wrong base price
        base_policy={}
    )
    result = localizer.localize("STALE_PRICE", "SKU-1")
    assert result["hypothesis"] == "price drift"
    assert result["confidence"] == "HIGH"

def test_causal_localizer_baseline_passes():
    def factory():
        return MockRunner(fails_due_to=None)
    localizer = CausalLocalizer(
        runner_factory=factory,
        base_inventory={"SKU-1": 10},
        base_pricing={"SKU-1": 100},
        base_policy={}
    )
    result = localizer.localize("UNKNOWN", "SKU-1")
    assert result["hypothesis"] == "Baseline did not fail"
