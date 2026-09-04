"""
Metrics Engine — computes all CommerceTwin metrics from raw persisted run data.
All financial metrics are explicitly labeled SYNTHETIC / TEST MODE.
No hardcoded percentages.
"""
import statistics
from typing import List, Dict, Any, Optional


def _pct(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


class MetricsEngine:
    def compute(
        self,
        traces: List[Dict[str, Any]],
        failure_clusters: List[Dict[str, Any]] = None,
        repair_proposals: List[Dict[str, Any]] = None,
        trace_events_by_id: Dict[str, List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Compute all standard CommerceTwin metrics from raw data.

        Args:
            traces: list of TransactionTrace dicts with fields:
                    trace_id, final_classification, final_amount_paise,
                    buyer_id, is_impossible_intent (bool), constraint_violated (bool),
                    recovered (bool), intent_integrity_ok (bool),
                    journey_start_ms, journey_end_ms, llm_call_count
            failure_clusters: list of FailureCluster dicts with estimated_lost_value_paise
            repair_proposals: list of RepairProposal dicts with status
            trace_events_by_id: dict mapping trace_id -> list of events (for latency)
        """
        failure_clusters = failure_clusters or []
        repair_proposals = repair_proposals or []
        trace_events_by_id = trace_events_by_id or {}

        # Split traces
        impossible = [t for t in traces if t.get("is_impossible_intent")]
        eligible = [t for t in traces if not t.get("is_impossible_intent")]
        completed = [t for t in eligible if t.get("final_classification") == "COMPLETED"]
        failed = [t for t in eligible if t.get("final_classification") == "FAILED"]
        constraint_violated = [t for t in traces if t.get("constraint_violated")]
        recovered = [t for t in failed if t.get("recovered")]
        intent_ok = [t for t in eligible if t.get("intent_integrity_ok")]
        verified_repairs = [r for r in repair_proposals if r.get("status") == "VERIFIED"]

        # --- Core Metrics ---
        rty = _pct(len(completed), len(eligible))

        arc_paise = sum(t.get("final_amount_paise", 0) or 0 for t in completed)
        arl_paise = sum(f.get("estimated_lost_value_paise", 0) or 0 for f in failure_clusters)

        cvr = _pct(len(constraint_violated), len(traces))
        rvr = _pct(len(verified_repairs), len(repair_proposals))
        frr = _pct(len(recovered), len(failed))
        ii = _pct(len(intent_ok), len(eligible))

        # --- Latency (from trace durations if provided) ---
        latencies_ms = []
        for t in traces:
            start = t.get("journey_start_ms")
            end = t.get("journey_end_ms")
            if start is not None and end is not None:
                latencies_ms.append(end - start)

        median_latency_ms = round(statistics.median(latencies_ms), 2) if latencies_ms else None
        p95_latency_ms = None
        if latencies_ms:
            sorted_lat = sorted(latencies_ms)
            idx = min(int(0.95 * len(sorted_lat)), len(sorted_lat) - 1)
            p95_latency_ms = sorted_lat[idx]

        # --- LLM call count ---
        total_llm_calls = sum(t.get("llm_call_count", 0) or 0 for t in traces)

        return {
            "note": "All financial metrics are SYNTHETIC and computed from Test Mode data only. Not production revenue.",
            "population": {
                "total_traces": len(traces),
                "eligible_traces": len(eligible),
                "impossible_intent_traces": len(impossible),
            },
            "RTY": rty,
            "II": ii,
            "ARC_paise_SYNTHETIC": arc_paise,
            "ARL_paise_SYNTHETIC": arl_paise,
            "CVR": cvr,
            "RVR": rvr,
            "FRR": frr,
            "latency": {
                "median_ms": median_latency_ms,
                "p95_ms": p95_latency_ms,
                "sample_count": len(latencies_ms),
            },
            "llm": {
                "total_calls": total_llm_calls,
            },
        }
