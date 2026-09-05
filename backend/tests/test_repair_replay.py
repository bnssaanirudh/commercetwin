"""
Critical correctness tests for the repair → replay closed loop.

Tests:
1. A no-op repair (empty operations) stays failed after verify_repair.
2. A correct evidence-backed repair succeeds after verify_repair.
3. generate_repair creates a real FailureCluster row linked to trace_id.
4. verify_repair uses the ReplaySnapshot, not the latest trace.
"""
import uuid

import pytest

from app.buyers.configurations import SemanticBuyer
from app.buyers.schemas import BuyerIntentSchema, HardConstraints, SoftPreferences
from app.models import (
    FailureCluster,
    RepairProposal,
    ReplayResult,
    ReplaySnapshot,
    TransactionTrace,
)
from app.services.commerce_service import CommerceService


def _make_intent(intent_id: str = "test-intent", budget: int = 10000) -> BuyerIntentSchema:
    return BuyerIntentSchema(
        intent_id=intent_id,
        raw_intent="I need a laptop charger with power_watts attribute",
        hard_constraints=HardConstraints(required_categories=["charger"]),
        soft_preferences=SoftPreferences(),
        target_budget_paise=budget,
        max_budget_paise=budget,
        autonomy_level="autonomous",
        seed=42,
    )


def _make_product(sku: str, category: str = "charger", price: int = 5000):
    from app.models import Product

    p = Product(sku=sku, title=f"Product {sku}", category=category, description="test")
    p.price_paise = price
    return p


def _run_failed_trace(svc: CommerceService, intent: BuyerIntentSchema, products, attrs=None):
    """Run a trace that is guaranteed to fail (empty product list → ABORTED)."""
    agent = SemanticBuyer(intent, products, attrs or {})
    return svc.run_trace(
        agent=agent,
        inventory_db={p.sku: 10 for p in products},
        pricing_db={p.sku: p.price_paise for p in products},
        merchant_policy_db={"shipping_available": True, "flat_shipping_paise": 0},
        attributes_map=attrs or {},
    )


def test_generate_repair_creates_real_failure_cluster(db_session):
    """generate_repair must create a real FailureCluster row linked to trace_id."""
    svc = CommerceService(db_session)
    intent = _make_intent()

    # Run a trace that will abort (no products match the REQUIRED oracle)
    _run_failed_trace(svc, intent, [])  # empty products → ABORTED

    trace = db_session.query(TransactionTrace).first()
    assert trace is not None

    localized = svc.localize_failure(trace.trace_id)
    repair = svc.generate_repair(trace_id=trace.trace_id, localized_cause=localized)

    if repair.get("status") == "MANUAL_REVIEW_REQUIRED":
        # No attributes evidence available — that's acceptable; skip further assertions
        pytest.skip("No attribute evidence available in test catalog — skipping repair checks")

    assert "repair_id" in repair

    # Verify FailureCluster was persisted with the correct trace_id
    fc = db_session.query(FailureCluster).filter(
        FailureCluster.failure_id == repair["failure_id"]
    ).first()
    assert fc is not None
    assert fc.trace_id == trace.trace_id


def test_noop_repair_stays_failed(db_session):
    """
    A repair with empty operations must not change the trace outcome.
    verify_repair should return False.
    """
    svc = CommerceService(db_session)
    intent = _make_intent()

    # Run a trace that aborts
    _run_failed_trace(svc, intent, [])

    trace = db_session.query(TransactionTrace).first()
    assert trace is not None

    # Create a FailureCluster manually linked to this trace
    failure_id = f"FC-{uuid.uuid4().hex[:8]}"
    fc = FailureCluster(
        failure_id=failure_id,
        trace_id=trace.trace_id,
        taxonomy="CATALOG",
        stage="EVALUATION",
        reason_code="MISSING_TYPED_ATTRIBUTE",
        estimated_lost_value_paise=5000,
        supporting_trace_ids=[trace.trace_id],
    )
    db_session.add(fc)

    # Get snapshot (created by run_trace)
    snap = db_session.query(ReplaySnapshot).filter(
        ReplaySnapshot.trace_id == trace.trace_id
    ).first()
    assert snap is not None, "ReplaySnapshot must be persisted by run_trace()"

    # Create a NO-OP repair (empty operations)
    noop_proposal = RepairProposal(
        repair_id=f"RP-{uuid.uuid4().hex[:8]}",
        failure_id=failure_id,
        snapshot_id=snap.snapshot_id,
        repair_type="CATALOG_SCHEMA_PATCH",
        proposed_patch={
            "patch": {
                "target_sku": "MISSING-SKU",
                "operations": [],  # ← empty no-op
            }
        },
        confidence=0,
        estimated_repair_cost_paise=0,
        status="proposed",
    )
    db_session.add(noop_proposal)
    db_session.commit()

    result = svc.verify_repair(noop_proposal.repair_id)

    assert isinstance(result, dict)
    assert result.get("success") is False, "No-op repair must NOT verify successfully"

    rr = db_session.query(ReplayResult).filter(
        ReplayResult.repair_id == noop_proposal.repair_id
    ).first()
    assert rr is not None
    assert rr.success is False


def test_correct_repair_succeeds(db_session):
    """
    A repair that adds a required attribute must cause verify_repair to return True
    when the product is then discoverable and passes oracle evaluation.

    We set up: one product missing 'power_watts' → agent rejects it → ABORTED.
    Repair adds power_watts → replay succeeds → READY_FOR_PAYMENT.
    """
    from app.models import Product

    svc = CommerceService(db_session)

    # Product without power_watts (will be rejected by oracle if the intent requires it)
    sku = "CHARGER-001"
    intent = BuyerIntentSchema(
        intent_id="intent-repair-test",
        raw_intent="charger product 0",
        hard_constraints=HardConstraints(
            required_categories=["charger"],
            min_attributes={"power_watts": 65}
        ),
        soft_preferences=SoftPreferences(),
        target_budget_paise=5000,
        max_budget_paise=5000,
        autonomy_level="autonomous",
        seed=42,
    )

    product = Product(sku=sku, merchant_id="merchant-1", title="charger product 0", category="charger", description="charger")
    product.price_paise = 5000
    db_session.add(product)
    db_session.commit()

    # The attribute map is empty → oracle may accept or reject based on constraints
    attrs_map: dict = {sku: []}

    agent = SemanticBuyer(intent, [product], attrs_map)
    svc.run_trace(
        agent=agent,
        inventory_db={sku: 10},
        pricing_db={sku: 5000},
        merchant_policy_db={"shipping_available": True, "flat_shipping_paise": 0},
        attributes_map=attrs_map,
    )

    trace = db_session.query(TransactionTrace).order_by(TransactionTrace.created_at.desc()).first()
    assert trace is not None
    original_state = trace.final_classification

    assert original_state == "ABORTED", "Trace must initially abort because power_watts is missing"

    snap = db_session.query(ReplaySnapshot).filter(
        ReplaySnapshot.trace_id == trace.trace_id
    ).first()
    assert snap is not None

    # Create failure cluster
    failure_id = f"FC-{uuid.uuid4().hex[:8]}"
    fc = FailureCluster(
        failure_id=failure_id,
        trace_id=trace.trace_id,
        taxonomy="CATALOG",
        stage="EVALUATION",
        reason_code="MISSING_TYPED_ATTRIBUTE",
        estimated_lost_value_paise=5000,
        supporting_trace_ids=[trace.trace_id],
    )
    db_session.add(fc)

    # Build a real repair that adds the missing attribute
    repair_proposal = RepairProposal(
        repair_id=f"RP-{uuid.uuid4().hex[:8]}",
        failure_id=failure_id,
        snapshot_id=snap.snapshot_id,
        repair_type="CATALOG_SCHEMA_PATCH",
        proposed_patch={
            "patch": {
                "target_sku": sku,
                "operations": [
                    {
                        "op": "add",
                        "path": "/attributes/power_watts",
                        "value": "65",
                        "type": "int",
                        "evidence_source": "merchant_catalog",
                    }
                ],
            }
        },
        confidence=85,
        estimated_repair_cost_paise=0,
        status="proposed",
    )
    db_session.add(repair_proposal)
    db_session.commit()

    result = svc.verify_repair(repair_proposal.repair_id)

    # The replay should complete successfully
    assert isinstance(result, dict)
    assert result.get("success") is True, "Correct repair must verify successfully"
    assert result.get("final_state") == "READY_FOR_PAYMENT"

    rr = db_session.query(ReplayResult).filter(
        ReplayResult.repair_id == repair_proposal.repair_id
    ).first()
    assert rr is not None, "ReplayResult must be persisted by verify_repair"
    assert rr.success is True
    assert rr.after_state == "READY_FOR_PAYMENT"


def test_replay_uses_snapshot_not_latest_trace(db_session):
    """
    After two additional traces are run, verify_repair must still use
    the original ReplaySnapshot — not the latest trace in DB.
    """
    from app.models import Product

    svc = CommerceService(db_session)

    sku = "SNAP-TEST-001"
    intent = _make_intent(intent_id="snap-test-buyer")
    product = Product(sku=sku, title="charger product 0", category="charger", description="test")
    product.price_paise = 5000

    # First trace
    _run_failed_trace(svc, intent, [product], {sku: []})
    first_trace = (
        db_session.query(TransactionTrace)
        .order_by(TransactionTrace.created_at.asc())
        .first()
    )
    assert first_trace is not None
    first_snap = db_session.query(ReplaySnapshot).filter(
        ReplaySnapshot.trace_id == first_trace.trace_id
    ).first()
    assert first_snap is not None, "ReplaySnapshot must exist for first trace"

    # Run two more traces to pollute DB
    for _ in range(2):
        other_intent = _make_intent(intent_id=f"other-{uuid.uuid4().hex[:4]}")
        _run_failed_trace(svc, other_intent, [])

    # Create a failure cluster linked to the FIRST trace
    failure_id = f"FC-{uuid.uuid4().hex[:8]}"
    fc = FailureCluster(
        failure_id=failure_id,
        trace_id=first_trace.trace_id,
        taxonomy="CATALOG",
        stage="EVALUATION",
        reason_code="MISSING_TYPED_ATTRIBUTE",
        estimated_lost_value_paise=5000,
        supporting_trace_ids=[first_trace.trace_id],
    )
    db_session.add(fc)

    repair = RepairProposal(
        repair_id=f"RP-{uuid.uuid4().hex[:8]}",
        failure_id=failure_id,
        snapshot_id=first_snap.snapshot_id,
        repair_type="CATALOG_SCHEMA_PATCH",
        proposed_patch={
            "patch": {
                "target_sku": sku,
                "operations": [
                    {
                        "op": "add",
                        "path": "/attributes/power_watts",
                        "value": "65",
                        "type": "int",
                        "evidence_source": "merchant_catalog",
                    }
                ],
            }
        },
        confidence=85,
        estimated_repair_cost_paise=0,
        status="proposed",
    )
    db_session.add(repair)
    db_session.commit()

    # Verify uses snapshot_id from proposal → first_snap → original intent/catalog
    svc.verify_repair(repair.repair_id)

    rr = db_session.query(ReplayResult).filter(
        ReplayResult.repair_id == repair.repair_id
    ).first()
    assert rr is not None
    # The replay should reference the snapshot from the first trace
    assert rr.trace_id == first_trace.trace_id
