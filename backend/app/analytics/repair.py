import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models import RepairProposal

# --- Guardrail constants ---
ALLOWED_REPAIR_TYPES = {"CATALOG_SCHEMA_PATCH", "MERCHANT_CONFIG_PATCH", "TRANSACTION_RELIABILITY_PATCH"}

BLOCKED_PATCH_KEYS = {
    "buyer_constraints",
    "invent_fact",
    "payment_amount",
    "payment_credentials",
    "financial_policy",
    "price_floor",
    "price_ceiling",
}


class RepairGuardrailViolation(Exception):
    """Raised when a proposed repair violates a safety policy."""


class RepairSynthesizer:
    """
    Synthesizes RepairProposals from FailureClusters.
    All repairs are sandbox-only and subject to strict guardrails.
    """

    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def synthesize(
        self,
        failure_cluster: dict,
        repair_type: str | None = None,
        proposed_patch: dict | None = None,
        evidence: list | None = None,
        expected_affected_traces: list | None = None,
        estimated_impact_paise: int = 0,
        repair_cost_paise: int = 0,
        safety_notes: str = "",
        verification_plan: str = "",
        confidence: int = 50,
        localized_cause: dict | None = None,
        snapshot_id: str | None = None,
        attributes_evidence: list | None = None,
    ) -> dict[str, Any]:
        """
        Returns a validated RepairProposal dict (and optionally persists to DB).
        Raises RepairGuardrailViolation for any policy breach.

        attributes_evidence: list of ProductAttribute-like dicts with keys
          {key, value, type} from authoritative merchant products that HAVE the
          missing attribute. Used to build real non-empty patch operations.
        """
        evidence = evidence or []
        expected_affected_traces = expected_affected_traces or []
        proposed_patch = proposed_patch or {}
        attributes_evidence = attributes_evidence or []

        # --- Auto-build patch for MISSING_TYPED_ATTRIBUTE ---
        if localized_cause and localized_cause.get("hypothesis") == "missing_typed_attribute":
            repair_type = "CATALOG_SCHEMA_PATCH"
            sku = localized_cause.get("sku", "unknown")

            if not attributes_evidence:
                # No authoritative merchant evidence — cannot safely invent facts.
                return {
                    "status": "MANUAL_REVIEW_REQUIRED",
                    "reason": (
                        f"Factual value for missing attribute on {sku} not found in merchant catalog. "
                        "Must be verified externally before a repair can be proposed."
                    ),
                }

            # Build patch operations from authoritative evidence
            operations = []
            for attr in attributes_evidence:
                operations.append({
                    "op": "add",
                    "path": f"/attributes/{attr['key']}",
                    "value": attr["value"],
                    "type": attr["type"],
                    "evidence_source": "merchant_catalog",
                })

            proposed_patch = {
                "target_sku": sku,
                "operations": operations,
            }
            confidence = 85
            safety_notes = "Patch sourced from authoritative merchant catalog evidence."
            verification_plan = "Replay original failed trace with patched attributes in sandbox."

        # --- Guardrail 1: Repair type must be supported ---
        if repair_type not in ALLOWED_REPAIR_TYPES:
            raise RepairGuardrailViolation(
                f"Unsupported repair type '{repair_type}'. Allowed: {ALLOWED_REPAIR_TYPES}"
            )

        # --- Guardrail 2: Blocked patch keys (buyer constraints, invented facts) ---
        def contains_blocked_key(data: dict | list) -> str | None:
            if isinstance(data, dict):
                for k, v in data.items():
                    if k in BLOCKED_PATCH_KEYS:
                        return k
                    found = contains_blocked_key(v)
                    if found:
                        return found
            elif isinstance(data, list):
                for item in data:
                    found = contains_blocked_key(item)
                    if found:
                        return found
            return None

        blocked = contains_blocked_key(proposed_patch)
        if blocked:
            raise RepairGuardrailViolation(
                f"Proposed patch contains blocked key '{blocked}'. "
                "Repairs cannot mutate buyer constraints or invent product facts."
            )

        # --- Guardrail 3: Cannot increase price_paise ---
        if "price_paise" in proposed_patch:
            original = proposed_patch.get("_original_price_paise")
            new_price = proposed_patch["price_paise"]
            if original is not None and new_price > original:
                raise RepairGuardrailViolation(
                    f"Proposed patch increases price_paise from {original} to {new_price}. "
                    "Price increases based on inferred buyer willingness-to-pay are prohibited."
                )

        # --- Guardrail 4: Repairs cannot target production (no 'production' flag) ---
        if proposed_patch.get("target_environment") == "production":
            raise RepairGuardrailViolation(
                "Repairs cannot target production systems. Set target_environment to 'sandbox'."
            )

        # --- Guardrail 5: cost must be non-negative integer (paise) ---
        if not isinstance(repair_cost_paise, int) or repair_cost_paise < 0:
            raise RepairGuardrailViolation("repair_cost_paise must be a non-negative integer.")

        proposal = {
            "repair_id": str(uuid.uuid4()),
            "failure_id": failure_cluster.get("failure_id"),
            "snapshot_id": snapshot_id,
            "repair_type": repair_type,
            "proposed_patch": proposed_patch,
            "evidence": evidence,
            "expected_affected_traces": expected_affected_traces,
            "estimated_impact_paise": estimated_impact_paise,
            "estimated_repair_cost_paise": repair_cost_paise,
            "confidence": confidence,
            "safety_notes": safety_notes,
            "verification_plan": verification_plan,
            "status": "proposed",
        }

        # Persist to DB if session provided
        if self.db is not None:
            db_row = RepairProposal(
                repair_id=proposal["repair_id"],
                failure_id=proposal["failure_id"],
                snapshot_id=proposal["snapshot_id"],
                repair_type=proposal["repair_type"],
                proposed_patch={
                    "patch": proposed_patch,
                    "evidence": evidence,
                    "expected_affected_traces": expected_affected_traces,
                    "estimated_impact_paise": estimated_impact_paise,
                    "safety_notes": safety_notes,
                    "verification_plan": verification_plan,
                },
                confidence=confidence,
                estimated_repair_cost_paise=repair_cost_paise,
                status="proposed",
            )
            self.db.add(db_row)
            self.db.commit()

        return proposal
