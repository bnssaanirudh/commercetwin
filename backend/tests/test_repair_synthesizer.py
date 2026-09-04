import pytest
from app.analytics.repair import RepairSynthesizer, RepairGuardrailViolation

CLUSTER = {"failure_id": "cluster-001", "stage": "COMMERCE", "reason_code": "PRICE_MISMATCH"}

def make_synth():
    return RepairSynthesizer(db=None)

def test_valid_catalog_patch_accepted():
    synth = make_synth()
    proposal = synth.synthesize(
        failure_cluster=CLUSTER,
        repair_type="CATALOG_SCHEMA_PATCH",
        proposed_patch={"add_attribute": {"key": "power_watts", "value": "65", "type": "integer"}},
        evidence=["trace-001", "trace-002"],
        expected_affected_traces=["trace-001"],
        estimated_impact_paise=5000,
        repair_cost_paise=200,
        safety_notes="Adds missing typed attribute. Sandbox only.",
        verification_plan="Replay cohort after attribute addition. Expect COMPLETED state.",
        confidence=80,
    )
    assert proposal["repair_id"] is not None
    assert proposal["status"] == "proposed"
    assert proposal["repair_type"] == "CATALOG_SCHEMA_PATCH"

def test_price_increase_rejected():
    synth = make_synth()
    with pytest.raises(RepairGuardrailViolation, match="increases price_paise"):
        synth.synthesize(
            failure_cluster=CLUSTER,
            repair_type="MERCHANT_CONFIG_PATCH",
            proposed_patch={
                "price_paise": 2000,
                "_original_price_paise": 1000,  # Trying to raise from 1000 to 2000
            },
            evidence=["trace-001"],
            expected_affected_traces=["trace-001"],
            estimated_impact_paise=1000,
            repair_cost_paise=0,
            safety_notes="",
            verification_plan="",
        )

def test_buyer_constraint_mutation_rejected():
    synth = make_synth()
    with pytest.raises(RepairGuardrailViolation, match="buyer_constraints"):
        synth.synthesize(
            failure_cluster=CLUSTER,
            repair_type="MERCHANT_CONFIG_PATCH",
            proposed_patch={"buyer_constraints": {"budget_paise": 99999}},
            evidence=[],
            expected_affected_traces=[],
            estimated_impact_paise=0,
            repair_cost_paise=0,
            safety_notes="",
            verification_plan="",
        )

def test_invented_fact_rejected():
    synth = make_synth()
    with pytest.raises(RepairGuardrailViolation, match="invent_fact"):
        synth.synthesize(
            failure_cluster=CLUSTER,
            repair_type="CATALOG_SCHEMA_PATCH",
            proposed_patch={"invent_fact": {"product_is_eco_friendly": True}},
            evidence=[],
            expected_affected_traces=[],
            estimated_impact_paise=0,
            repair_cost_paise=0,
            safety_notes="",
            verification_plan="",
        )

def test_production_target_rejected():
    synth = make_synth()
    with pytest.raises(RepairGuardrailViolation, match="production"):
        synth.synthesize(
            failure_cluster=CLUSTER,
            repair_type="TRANSACTION_RELIABILITY_PATCH",
            proposed_patch={"target_environment": "production", "retry_budget_ms": 5000},
            evidence=[],
            expected_affected_traces=[],
            estimated_impact_paise=0,
            repair_cost_paise=0,
            safety_notes="",
            verification_plan="",
        )

def test_unsupported_repair_type_rejected():
    synth = make_synth()
    with pytest.raises(RepairGuardrailViolation, match="Unsupported repair type"):
        synth.synthesize(
            failure_cluster=CLUSTER,
            repair_type="OVERRIDE_BUYER_DECISION",
            proposed_patch={"force_purchase": True},
            evidence=[],
            expected_affected_traces=[],
            estimated_impact_paise=0,
            repair_cost_paise=0,
            safety_notes="",
            verification_plan="",
        )
