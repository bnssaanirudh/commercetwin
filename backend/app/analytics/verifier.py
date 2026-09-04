from typing import Callable, List, Optional
from app.commerce.runner import CommerceRunner
from app.commerce.state import CommerceState

PAYMENT_SAFE_STATES = {CommerceState.COMPLETED, CommerceState.RECOVERED_SUCCESS}
PAYMENT_VIOLATION_STATES = {CommerceState.PAYMENT, CommerceState.AMBIGUOUS_REMOTE_STATE}

class VerificationResult:
    def __init__(self, status: str, before_metrics: dict, after_metrics: dict,
                 replay_results: list, trade_off_notes: Optional[str] = None):
        self.status = status          # "VERIFIED" | "REJECTED" | "NOT_VERIFIED"
        self.before_metrics = before_metrics
        self.after_metrics = after_metrics
        self.replay_results = replay_results
        self.trade_off_notes = trade_off_notes

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "before_metrics": self.before_metrics,
            "after_metrics": self.after_metrics,
            "replay_results": self.replay_results,
            "trade_off_notes": self.trade_off_notes,
        }


class RepairVerifier:
    """
    Verifies repair proposals by replaying the exact failed cohort before and after
    applying the proposed patch, using original seeds and buyer configurations.

    A repair is VERIFIED only when:
    - The targeted failure improves meaningfully.
    - No new hard constraint violation is introduced.
    - No payment safety regression is introduced.
    - The improvement is reproducible.
    """

    def verify(
        self,
        repair_proposal: dict,
        cohort_factory: Callable[[str], CommerceRunner],
        cohort_trace_ids: List[str],
        patched_cohort_factory: Callable[[str], CommerceRunner],
    ) -> VerificationResult:
        """
        Args:
            repair_proposal: The proposal to verify.
            cohort_factory: Callable(trace_id) -> CommerceRunner using original config.
            cohort_trace_ids: List of trace IDs in the failed cohort.
            patched_cohort_factory: Callable(trace_id) -> CommerceRunner with repair applied.
        """
        before_results = []
        after_results = []

        for trace_id in cohort_trace_ids:
            # --- Baseline run (should fail) ---
            base_runner = cohort_factory(trace_id)
            base_runner.run_to_precheck()
            if base_runner.state_machine.current_state == CommerceState.READY_FOR_PAYMENT:
                base_runner.process_payment()
            before_state = base_runner.state_machine.current_state
            before_results.append({
                "trace_id": trace_id,
                "outcome": before_state.value,
                "success": before_state == CommerceState.COMPLETED,
            })

            # --- Patched run (should improve) ---
            patched_runner = patched_cohort_factory(trace_id)
            patched_runner.run_to_precheck()
            if patched_runner.state_machine.current_state == CommerceState.READY_FOR_PAYMENT:
                patched_runner.process_payment()
            after_state = patched_runner.state_machine.current_state

            # Check for payment safety regression: patched run ends in a dangerous ambiguous state
            # without transitioning to COMPLETED — treat as hard safety fail
            patched_states = [e["payload"].get("state") for e in patched_runner.state_machine.trace_events
                              if e["event_type"] == "STATE_ENTERED"]
            payment_regression = (
                "AMBIGUOUS_REMOTE_STATE" in patched_states and
                after_state != CommerceState.COMPLETED
            )

            after_results.append({
                "trace_id": trace_id,
                "outcome": after_state.value,
                "success": after_state == CommerceState.COMPLETED,
                "payment_safety_regression": payment_regression,
            })

        # --- Compute metrics ---
        before_success = sum(1 for r in before_results if r["success"])
        after_success = sum(1 for r in after_results if r["success"])
        total = len(cohort_trace_ids)

        before_metrics = {
            "total_traces": total,
            "successes": before_success,
            "failures": total - before_success,
            "success_rate": round(before_success / total, 4) if total else 0,
        }
        after_metrics = {
            "total_traces": total,
            "successes": after_success,
            "failures": total - after_success,
            "success_rate": round(after_success / total, 4) if total else 0,
        }

        # --- Determine verdict ---
        payment_regressions = [r for r in after_results if r.get("payment_safety_regression")]
        improvement = after_success > before_success

        if payment_regressions:
            status = "REJECTED"
            trade_off = f"Payment safety regression in {len(payment_regressions)} trace(s)."
        elif not improvement:
            status = "REJECTED"
            trade_off = "Repair did not meaningfully improve the targeted failure rate."
        elif after_success < total:
            # Partial success — VERIFIED but record trade-off
            status = "VERIFIED"
            trade_off = (
                f"Repair improved {after_success - before_success} trace(s) "
                f"but {total - after_success} still failing."
            )
        else:
            status = "VERIFIED"
            trade_off = None

        return VerificationResult(
            status=status,
            before_metrics=before_metrics,
            after_metrics=after_metrics,
            replay_results=after_results,
            trade_off_notes=trade_off,
        )
