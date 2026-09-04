import pytest
from app.analytics.prioritizer import RepairPrioritizer

def make_repair(repair_id, traces, per_trace_val, cost, stage="COMMERCE", code="PRICE_MISMATCH"):
    total = sum(per_trace_val[t] for t in traces)
    return {
        "repair_id": repair_id,
        "stage": stage,
        "reason_code": code,
        "recovered_traces": traces,
        "per_trace_value_paise": per_trace_val,
        "recovered_value_paise": total,
        "repair_cost_paise": cost,
    }


def test_no_overlap_three_repairs():
    """3 repairs with completely disjoint traces — scores computed independently."""
    repairs = [
        make_repair("r1", ["t1", "t2"], {"t1": 5000, "t2": 5000}, cost=1000),   # score=10
        make_repair("r2", ["t3"],       {"t3": 8000},              cost=400),    # score=20 (best)
        make_repair("r3", ["t4"],       {"t4": 2000},              cost=1000),   # score=2
    ]
    p = RepairPrioritizer()
    result = p.top_k(repairs, k=3)

    assert len(result["top_repairs"]) == 3
    assert result["overlap_adjustments"] == []
    # Best score first (r2 = 20)
    assert result["top_repairs"][0]["repair_id"] == "r2"
    assert result["cumulative_recovered_value_paise"] == 5000 + 5000 + 8000 + 2000


def test_overlapping_repairs_deduplication():
    """
    Two repairs share trace t1.
    r2 scores higher initially (13000/300 ≈ 43) than r1 (15000/500 = 30),
    so r2 is selected first by the greedy algorithm.
    When r1 is then selected, t1 is already covered — only t2's value counts.
    """
    per_trace_r1 = {"t1": 10000, "t2": 5000}
    per_trace_r2 = {"t1": 10000, "t3": 3000}   # t1 also in r1

    repairs = [
        make_repair("r1", ["t1", "t2"], per_trace_r1, cost=500),  # initial score=30
        make_repair("r2", ["t1", "t3"], per_trace_r2, cost=300),  # initial score≈43 → selected first
    ]
    p = RepairPrioritizer()
    result = p.top_k(repairs, k=2)

    # r2 is selected first (highest score), it covers t1 and t3 fully
    r2_entry = result["top_repairs"][0]
    assert r2_entry["repair_id"] == "r2"
    assert r2_entry["incremental_recovered_value_paise"] == 13000  # t1+t3 = 10000+3000

    # r1 is selected second — t1 already covered, only t2 counts
    r1_entry = result["top_repairs"][1]
    assert r1_entry["repair_id"] == "r1"
    assert r1_entry["incremental_recovered_value_paise"] == 5000   # only t2
    assert "t1" not in r1_entry["new_traces_covered"]

    # Overlap adjustment recorded for r1
    assert len(result["overlap_adjustments"]) == 1
    assert result["overlap_adjustments"][0]["repair_id"] == "r1"
    assert result["overlap_adjustments"][0]["deducted_value_paise"] == 10000

    # Cumulative must NOT double-count t1
    assert result["cumulative_recovered_value_paise"] == 13000 + 5000  # 18000, not 28000


def test_k_equals_one():
    """K=1 returns only the single highest-scoring repair."""
    repairs = [
        make_repair("r_low",  ["t1"], {"t1": 1000}, cost=1000),
        make_repair("r_high", ["t2"], {"t2": 9000}, cost=300),
    ]
    p = RepairPrioritizer()
    result = p.top_k(repairs, k=1)

    assert len(result["top_repairs"]) == 1
    assert result["top_repairs"][0]["repair_id"] == "r_high"


def test_method_label_is_greedy():
    """Output must honestly label itself as a greedy approximation."""
    p = RepairPrioritizer()
    result = p.top_k([], k=3)
    assert result["method"] == "greedy_approximation"
