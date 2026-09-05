
class RepairPrioritizer:
    """
    Greedy minimum-repair-set prioritizer.

    Score: recoverable_value_paise / estimated_repair_cost_paise.

    Avoids double-counting overlapping recovered traces — the incremental
    value of a repair is the value recoverable from traces NOT already
    covered by a higher-ranked repair in the selected set.

    NOTE: This is a greedy approximation. It is NOT guaranteed to be the
    mathematically optimal repair set.
    """

    def top_k(self, repairs: list[dict], k: int) -> dict:
        """
        Args:
            repairs: List of verified repair dicts. Each must contain:
                - repair_id: str
                - stage: str
                - reason_code: str
                - recovered_traces: list[str]  — trace IDs this repair recovers
                - recovered_value_paise: int   — total value across covered traces
                - per_trace_value_paise: dict  — trace_id -> value (for dedup)
                - repair_cost_paise: int
            k: Number of repairs to select.

        Returns:
            dict with ranked repairs, cumulative value, covered clusters, overlap notes.
        """
        if k <= 0:
            return {"top_repairs": [], "cumulative_recovered_value_paise": 0,
                    "covered_failure_clusters": [], "overlap_adjustments": [],
                    "method": "greedy_approximation"}

        covered_traces: set = set()
        selected = []
        overlap_adjustments = []

        # Score each repair using full value before de-duplication (for initial sorting)
        def initial_score(r: dict) -> float:
            cost = r.get("repair_cost_paise", 1)
            if cost <= 0:
                cost = 1
            return r.get("recovered_value_paise", 0) / cost

        sorted_repairs = sorted(repairs, key=initial_score, reverse=True)

        for repair in sorted_repairs:
            if len(selected) >= k:
                break

            trace_values: dict = repair.get("per_trace_value_paise", {})
            all_traces = set(repair.get("recovered_traces", []))

            # Only count traces NOT already covered by a prior selected repair
            new_traces = all_traces - covered_traces
            overlapping_traces = all_traces & covered_traces

            incremental_value = sum(trace_values.get(t, 0) for t in new_traces)

            if overlapping_traces:
                overlap_adjustments.append({
                    "repair_id": repair["repair_id"],
                    "overlapping_trace_count": len(overlapping_traces),
                    "deducted_value_paise": sum(trace_values.get(t, 0) for t in overlapping_traces),
                })

            cost = max(repair.get("repair_cost_paise", 1), 1)
            incremental_score = incremental_value / cost

            selected.append({
                "repair_id": repair["repair_id"],
                "stage": repair.get("stage", "UNKNOWN"),
                "reason_code": repair.get("reason_code", "UNKNOWN"),
                "incremental_recovered_value_paise": incremental_value,
                "repair_cost_paise": repair.get("repair_cost_paise", 0),
                "incremental_score": round(incremental_score, 4),
                "new_traces_covered": sorted(new_traces),
            })

            covered_traces.update(new_traces)

        cumulative_value = sum(r["incremental_recovered_value_paise"] for r in selected)
        covered_clusters = list({r["stage"] + "/" + r["reason_code"] for r in selected})

        return {
            "method": "greedy_approximation",
            "top_repairs": selected,
            "cumulative_recovered_value_paise": cumulative_value,
            "covered_failure_clusters": covered_clusters,
            "overlap_adjustments": overlap_adjustments,
        }
