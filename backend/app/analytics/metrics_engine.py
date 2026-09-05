import datetime
import random
from typing import Any


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = (p / 100) * (len(sorted_vals) - 1)
    lo, hi = int(idx), min(int(idx) + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])


def bootstrap_ci(values: list[float], n_boot: int = 2000, ci: float = 0.95, rng: random.Random = None) -> tuple[float, float]:
    """Bootstrap confidence interval for a list of 0/1 values or floats."""
    if not values:
        return 0.0, 0.0
    if rng is None:
        rng = random.Random(42)
    means = []
    n = len(values)
    for _ in range(n_boot):
        sample = [values[rng.randint(0, n - 1)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo_idx = int((1 - ci) / 2 * n_boot)
    hi_idx = int((1 + ci) / 2 * n_boot)
    return means[lo_idx], means[min(hi_idx, n_boot - 1)]


class MetricsEngine:
    """
    Unified metrics calculator. Used by both the live CommerceService and run_benchmark.py
    to prevent divergence in logic (e.g. RTY, Intent Integrity, AVaR, REV).
    """

    @staticmethod
    def compute_metrics(
        traces: list[dict[str, Any]], 
        seed: int = 42
    ) -> dict[str, Any]:
        """
        Expects traces as a list of dicts with:
        - eligible (bool)
        - success (bool)
        - intent_preserved (bool)
        - recovered (bool)
        - canonical_price (int)
        - latency_ms (float)
        """
        rng = random.Random(seed)
        eligible_traces = [t for t in traces if t.get("eligible", True)]
        ineligible_traces = [t for t in traces if not t.get("eligible", True)]
        
        total_eligible = len(eligible_traces)
        successful = [t for t in eligible_traces if t.get("success", False)]
        failed = [t for t in eligible_traces if not t.get("success", False)]

        # RTY: Successful / Total Eligible
        rty = len(successful) / total_eligible if total_eligible > 0 else 0.0
        
        # Intent Integrity: Successful transactions that preserved intent / Total Successful
        ii = sum(1 for t in successful if t.get("intent_preserved", False)) / len(successful) if successful else 0.0
        
        # Constraint Violation Rate: Successful transactions that violated intent / Total Successful
        cvr = sum(1 for t in successful if not t.get("intent_preserved", False)) / len(successful) if successful else 0.0

        # AVaR: Canonical value of failed eligible traces
        avar = sum(t.get("canonical_price", 0) for t in failed)
        
        # REV: Recovered Eligible Value (canonical value of traces that were successfully recovered)
        rev = sum(t.get("canonical_price", 0) for t in successful if t.get("recovered", False))

        # Bootstrap 95% CI for RTY
        success_bits = [1.0 if t.get("success", False) else 0.0 for t in eligible_traces]
        rty_lo, rty_hi = bootstrap_ci(success_bits, rng=rng)

        # Latency statistics
        latencies = [t.get("latency_ms", 0.0) for t in traces]
        mean_lat = sum(latencies) / len(latencies) if latencies else 0.0
        median_lat = percentile(latencies, 50)
        p95_lat = percentile(latencies, 95)
        
        recovered_count = sum(1 for t in successful if t.get("recovered", False))

        return {
            "Robust_Transaction_Yield": round(rty, 4),
            "RTY_CI_95_lo": round(rty_lo, 4),
            "RTY_CI_95_hi": round(rty_hi, 4),
            "Intent_Integrity": round(ii, 4),
            "Constraint_Violation_Rate": round(cvr, 4),
            "Agentic_Value_at_Risk_Paise": avar,
            "Recovered_Eligible_Value_Paise": rev,
            "Latency_Mean_ms": round(mean_lat, 2),
            "Latency_Median_ms": round(median_lat, 2),
            "Latency_P95_ms": round(p95_lat, 2),
            "Total_Scenarios": len(traces),
            "Total_Eligible": total_eligible,
            "Total_Ineligible": len(ineligible_traces),
            "Total_Successful": len(successful),
            "Total_Failed": len(failed),
            "Total_Recovered": recovered_count,
        }
