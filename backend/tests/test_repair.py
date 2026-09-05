from app.analytics.repair import RepairSynthesizer, RepairGuardrailViolation
from app.models import Product

def test_repair_synthesizer_full():
    synth = RepairSynthesizer(None)
    
    # Missing typed attribute
    res1 = synth.synthesize(
        {"failure_id": "test", "reason_code": "MISSING_TYPED_ATTRIBUTE", "best_hypothesis": {"hypothesis": "missing_typed_attribute", "intervention": "restore missing attribute {'ram': '16GB'} for ['SKU-1']"}},
        "CATALOG_SCHEMA_PATCH",
        {"target_sku": "SKU-1", "operations": [{"key": "ram", "new_value": "16GB"}]}
    )
    assert res1["repair_type"] == "CATALOG_SCHEMA_PATCH"

    # Price drift - test fallback behavior since it's not allowed
    import pytest
    with pytest.raises(RepairGuardrailViolation):
        res2 = synth.synthesize(
            {"failure_id": "test", "reason_code": "UNKNOWN"},
            "UNKNOWN",
            {}
        )

    # Stale inventory
    with pytest.raises(RepairGuardrailViolation):
        res3 = synth.synthesize(
            {"failure_id": "test", "reason_code": "INVENTORY_ZERO", "best_hypothesis": {"hypothesis": "stale inventory", "intervention": "restore stock"}},
            "INVENTORY_RESTOCK",
            {"target_sku": "SKU-1", "restock_quantity": 10}
        )

    # Fallback
    with pytest.raises(RepairGuardrailViolation):
        res4 = synth.synthesize(
            {"failure_id": "test", "reason_code": "UNKNOWN"},
            "UNKNOWN",
            {}
        )
    import pytest
    with pytest.raises(RepairGuardrailViolation):
        synth.synthesize(
            {"failure_id": "test"},
            "CATALOG_SCHEMA_PATCH",
            {"financial_policy": "hacked"}
        )
