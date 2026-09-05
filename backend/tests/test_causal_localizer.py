from app.analytics.repair import RepairSynthesizer
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
