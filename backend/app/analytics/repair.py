import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.models import RepairProposal, FailureCluster

# --- Guardrail constants ---
ALLOWED_REPAIR_TYPES = {"CATALOG_SCHEMA_PATCH", "MERCHANT_CONFIG_PATCH", "TRANSACTION_RELIABILITY_PATCH"}

BLOCKED_PATCH_KEYS = {"buyer_constraints", "invent_fact"}

class RepairGuardrailViolation(Exception):
    """Raised when a proposed repair violates a safety policy."""
    pass


class RepairSynthesizer:
    """
    Synthesizes RepairProposals from FailureClusters.
    All repairs are sandbox-only and subject to strict guardrails.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def synthesize(
        self,
        failure_cluster: dict,
        repair_type: str = None,
        proposed_patch: dict = None,
        evidence: list = None,
        expected_affected_traces: list = None,
        estimated_impact_paise: int = 0,
        repair_cost_paise: int = 0,
        safety_notes: str = "",
        verification_plan: str = "",
        confidence: int = 50,
        localized_cause: dict = None,
    ) -> dict:
        """
        Returns a validated RepairProposal dict (and optionally persists to DB).
        Raises RepairGuardrailViolation for any policy breach.
        """
        
        evidence = evidence or []
        expected_affected_traces = expected_affected_traces or []
        
        # Auto-generation for MISSING_TYPED_ATTRIBUTE
        if localized_cause and localized_cause.get("hypothesis") == "missing_typed_attribute":
            repair_type = "CATALOG_SCHEMA_PATCH"
            sku = localized_cause.get("sku")
            attr = localized_cause.get("intervention", "").split("'")[1] if "'" in localized_cause.get("intervention", "") else "unknown"
            
            # Attempt to extract the value from the intervention string
            import re
            match = re.search(r"restore missing attributes \{.*?:\s*'([^']+)'\}", localized_cause.get("intervention", ""))
            if not match:
                match = re.search(r"restore missing attributes \{.*?:\s*([^}]+)\}", localized_cause.get("intervention", ""))
            
            if match:
                value = match.group(1).strip()
                proposed_patch = {
                    "target_sku": sku,
                    "operations": [{"op": "add", "path": f"/attributes/{attr}", "value": value}],
                    "value_source": "inferred_from_buyer_intent"
                }
                confidence = max(confidence, 90)
            else:
                return {"status": "MANUAL_REVIEW_REQUIRED", "reason": f"Factual value for {attr} on {sku} not found."}

        # --- Guardrail 1: Repair type must be supported ---
        if repair_type not in ALLOWED_REPAIR_TYPES:
            raise RepairGuardrailViolation(
                f"Unsupported repair type '{repair_type}'. Allowed: {ALLOWED_REPAIR_TYPES}"
            )

        # --- Guardrail 2: Blocked patch keys (buyer constraints, invented facts) ---
        for blocked_key in BLOCKED_PATCH_KEYS:
            if blocked_key in proposed_patch:
                raise RepairGuardrailViolation(
                    f"Proposed patch contains blocked key '{blocked_key}'. "
                    f"Repairs cannot mutate buyer constraints or invent product facts."
                )

        # --- Guardrail 3: Cannot increase price_paise ---
        if "price_paise" in proposed_patch:
            original = proposed_patch.get("_original_price_paise")
            new_price = proposed_patch["price_paise"]
            if original is not None and new_price > original:
                raise RepairGuardrailViolation(
                    f"Proposed patch increases price_paise from {original} to {new_price}. "
                    f"Price increases based on inferred buyer willingness-to-pay are prohibited."
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
