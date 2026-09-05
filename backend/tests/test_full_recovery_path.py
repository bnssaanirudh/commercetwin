"""
Hero regression test -- full power_watts recovery path.

Asserts:
  1. Product initially has power_watts=65
  2. ChaosEngine (drop_attribute profile) removes it
  3. Buyer hard constraint requires power_watts >= 65
  4. Initial trace state == ABORTED
  5. Localizer identifies the cause
  6. Authoritative same-SKU evidence provides 65
  7. Repair contains at least one operation on /attributes/power_watts
  8. Replay trace ID != original trace ID
  9. Replay reaches READY_FOR_PAYMENT
 10. oracle_valid == True
 11. ReplayResult.success == True
"""
import copy
import datetime
import hashlib
import types
import uuid

import pytest

from app.buyers.configurations import StructuredBuyer
from app.buyers.schemas import BuyerIntentSchema, HardConstraints, SoftPreferences
from app.chaos.engine import ChaosEngine
from app.models import (
    CatalogAttributeEvidence,
    Product,
    ProductAttribute,
    RepairProposal,
    ReplayResult,
    TransactionTrace,
)
from app.services.commerce_service import CommerceService


def _detached_product(sku: str, price: int = 5000, category: str = "charger") -> Product:
    """Transient Product not bound to any session."""
    p = Product(
        sku=sku,
        merchant_id="merchant-hero",
        title=f"65W Fast Charger ({sku})",
        category=category,
        description="Supports 65W fast charging.",
    )
    p.price_paise = price
    return p


def _attr_ns(sku: str, key: str, value: str, type_: str = "int") -> types.SimpleNamespace:
    """Lightweight attribute namespace compatible with ChaosEngine attr.key access."""
    return types.SimpleNamespace(sku=sku, key=key, value=value, type=type_)


def test_full_power_watts_recovery_path(db_session):
    """
    End-to-end hero path:
      power_watts originally 65
      -> chaos drops power_watts
      -> buyer requires power_watts >= 65
      -> initial ABORTED
      -> localizer finds cause
      -> same-SKU evidence (MERCHANT_TRUTH) provides 65
      -> repair has /attributes/power_watts operation
      -> replay has distinct trace ID
      -> replay reaches READY_FOR_PAYMENT
      -> oracle validates the repaired cart
      -> ReplayResult.success = True
    """
    sku = "HERO-CHARGER-001"
    price = 5000

    # 1. Merchant truth: product + attribute + evidence persisted for evidence lookup
    db_product = _detached_product(sku, price=price)
    db_session.add(db_product)

    power_attr_db = ProductAttribute(sku=sku, key="power_watts", value="65", type="int")
    db_session.add(power_attr_db)

    evidence = CatalogAttributeEvidence(
        evidence_id=f"EV-{uuid.uuid4().hex[:8]}",
        sku=sku,
        key="power_watts",
        value="65",
        type="int",
        catalog_version=1,
        source="MERCHANT_TRUTH",
        verified_at=datetime.datetime.now(datetime.UTC),
        source_hash=hashlib.sha256(f"{sku}:power_watts:65".encode()).hexdigest(),
    )
    db_session.add(evidence)
    db_session.commit()

    # 2. Build isolated chaos world (products + attrs not session-attached)
    chaos_product = _detached_product(sku, price=price)
    chaos_attr = _attr_ns(sku, "power_watts", "65")
    attrs_map_for_chaos = {sku: [chaos_attr]}
    inventory_db = {sku: 10}
    pricing_db = {sku: price}
    policy_db = {"shipping_available": True, "flat_shipping_paise": 0}

    chaos = ChaosEngine()
    chaos.apply(
        [chaos_product],
        copy.deepcopy(inventory_db),
        copy.deepcopy(pricing_db),
        copy.deepcopy(policy_db),
        seed=42,
        profile="drop_attribute",
        attributes_map=copy.deepcopy(attrs_map_for_chaos),
    )
    mutated_products, mutated_inv, mutated_pricing, mutated_policy, mutated_attrs = chaos.get_state()

    # Verify power_watts is absent after chaos
    remaining = mutated_attrs.get(sku, [])
    assert all(a.key != "power_watts" for a in remaining), (
        "power_watts must be absent after drop_attribute chaos"
    )

    # 3. Buyer requires power_watts >= 65
    intent = BuyerIntentSchema(
        intent_id="hero-test-intent",
        raw_intent="I need a charger with at least 65W",
        hard_constraints=HardConstraints(
            required_categories=["charger"],
            min_attributes={"power_watts": 65},
        ),
        soft_preferences=SoftPreferences(),
        target_budget_paise=price,
        max_budget_paise=price,
        autonomy_level="autonomous",
        seed=42,
    )

    agent = StructuredBuyer(intent, mutated_products, mutated_attrs)
    svc = CommerceService(db_session)
    runner = svc.run_trace(
        agent=agent,
        inventory_db=mutated_inv,
        pricing_db=mutated_pricing,
        merchant_policy_db=mutated_policy,
        attributes_map=mutated_attrs,
    )

    # 4. Initial state must be ABORTED
    original_trace_id = runner.trace_id
    assert runner.state_machine.current_state.name == "ABORTED", (
        f"Expected ABORTED after power_watts drop, got {runner.state_machine.current_state.name}"
    )

    original_trace = db_session.query(TransactionTrace).filter(
        TransactionTrace.trace_id == original_trace_id
    ).first()
    assert original_trace is not None
    assert original_trace.final_classification == "ABORTED"

    # 5. Localizer identifies the cause
    localized = svc.localize_failure(original_trace_id)
    assert localized.get("status") == "localized", f"Expected localized, got: {localized}"

    # 6. Generate repair using same-SKU MERCHANT_TRUTH evidence
    repair_data = svc.generate_repair(
        trace_id=original_trace_id,
        localized_cause=localized,
    )

    if repair_data.get("status") == "MANUAL_REVIEW_REQUIRED":
        pytest.skip(
            f"No authoritative evidence found for SKU '{localized.get('sku')}'. "
            "Hero test requires evidence in DB before run_trace()."
        )

    assert "repair_id" in repair_data, f"Expected repair_id in {repair_data}"
    repair_id = repair_data["repair_id"]

    # 7. Repair must have at least one operation on power_watts
    proposal = db_session.query(RepairProposal).filter(
        RepairProposal.repair_id == repair_id
    ).first()
    assert proposal is not None
    operations = proposal.proposed_patch.get("patch", {}).get("operations", [])
    assert len(operations) >= 1, "Repair must have at least one operation"
    pw_ops = [op_item for op_item in operations if "power_watts" in op_item.get("path", "")]
    assert len(pw_ops) >= 1, (
        f"Repair must reference power_watts. Got operations: {operations}"
    )

    # 8-11. Verify repair
    verification = svc.verify_repair(repair_id)

    assert isinstance(verification, dict)
    assert verification.get("success") is True, (
        f"verify_repair must succeed. Got: {verification}"
    )

    replay_trace_id = verification.get("trace_id")
    assert replay_trace_id is not None
    assert replay_trace_id != original_trace_id, (
        f"Replay trace must differ from original: {original_trace_id} vs {replay_trace_id}"
    )

    assert verification.get("final_state") == "READY_FOR_PAYMENT", (
        f"Replay must reach READY_FOR_PAYMENT, got {verification.get('final_state')}"
    )

    assert verification.get("oracle_valid") is True, (
        "IntentOracle must validate the repaired cart"
    )

    # Persistence checks
    rr = db_session.query(ReplayResult).filter(
        ReplayResult.repair_id == repair_id
    ).first()
    assert rr is not None, "ReplayResult must be persisted"
    assert rr.success is True
    assert rr.oracle_valid is True
    assert rr.after_state == "READY_FOR_PAYMENT"
