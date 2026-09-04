import pytest
from app.analytics.metrics import MetricsEngine
from app.analytics.reporter import MetricsReporter

# -------------------------------------------------------------------
# Fixture: 3 completed + 2 failed + 1 impossible intent
# Hand-calculated expected values documented inline.
# -------------------------------------------------------------------

def make_trace(tid, classification, amount=0, impossible=False,
               constraint_violated=False, recovered=False,
               intent_ok=True, start_ms=0, end_ms=100, llm_calls=1):
    return {
        "trace_id": tid,
        "final_classification": classification,
        "final_amount_paise": amount,
        "buyer_id": f"buyer_{tid}",
        "is_impossible_intent": impossible,
        "constraint_violated": constraint_violated,
        "recovered": recovered,
        "intent_integrity_ok": intent_ok,
        "journey_start_ms": start_ms,
        "journey_end_ms": end_ms,
        "llm_call_count": llm_calls,
    }

TRACES = [
    make_trace("t1", "COMPLETED",  amount=5000,  start_ms=0,   end_ms=200,  llm_calls=2),
    make_trace("t2", "COMPLETED",  amount=10000, start_ms=0,   end_ms=300,  llm_calls=3),
    make_trace("t3", "COMPLETED",  amount=7500,  start_ms=0,   end_ms=250,  llm_calls=1),
    make_trace("t4", "FAILED",                   start_ms=0,   end_ms=100,  llm_calls=1, intent_ok=False),
    make_trace("t5", "FAILED",                   start_ms=0,   end_ms=150,  llm_calls=2, recovered=True),
    make_trace("t6", "COMPLETED",  amount=0, impossible=True,  start_ms=0,   end_ms=50,   llm_calls=0),
]

FAILURE_CLUSTERS = [
    {"estimated_lost_value_paise": 5000},
    {"estimated_lost_value_paise": 3000},
]

REPAIR_PROPOSALS = [
    {"status": "VERIFIED"},
    {"status": "REJECTED"},
    {"status": "proposed"},
]


def test_rty():
    # Eligible = 5 (t1-t5; t6 is impossible)
    # Completed among eligible = 3 (t1, t2, t3)
    # RTY = 3/5 = 0.6
    metrics = MetricsEngine().compute(TRACES, FAILURE_CLUSTERS, REPAIR_PROPOSALS)
    assert metrics["RTY"] == 0.6


def test_arc_and_arl_labeled_synthetic():
    metrics = MetricsEngine().compute(TRACES, FAILURE_CLUSTERS, REPAIR_PROPOSALS)
    # ARC = 5000 + 10000 + 7500 = 22500 (t6 is impossible + completed, but impossible intents
    # are still counted here since they did complete — reporter should note synthetic)
    assert metrics["ARC_paise_SYNTHETIC"] == 22500
    # ARL = 5000 + 3000 = 8000
    assert metrics["ARL_paise_SYNTHETIC"] == 8000
    assert "SYNTHETIC" in next(k for k in metrics if "ARC" in k)
    assert "note" in metrics
    assert "SYNTHETIC" in metrics["note"]


def test_cvr():
    # No constraint violations in fixture → CVR = 0
    metrics = MetricsEngine().compute(TRACES, FAILURE_CLUSTERS, REPAIR_PROPOSALS)
    assert metrics["CVR"] == 0.0

    # Add one violated
    traces_with_violation = TRACES + [
        make_trace("t7", "FAILED", constraint_violated=True)
    ]
    metrics2 = MetricsEngine().compute(traces_with_violation, FAILURE_CLUSTERS, REPAIR_PROPOSALS)
    # 1 violated / 7 total = 0.1429
    assert round(metrics2["CVR"], 4) == round(1/7, 4)


def test_rvr():
    # 1 VERIFIED / 3 total = 0.3333
    metrics = MetricsEngine().compute(TRACES, FAILURE_CLUSTERS, REPAIR_PROPOSALS)
    assert round(metrics["RVR"], 4) == round(1/3, 4)


def test_frr():
    # 1 recovered (t5) / 2 failed (t4, t5) = 0.5
    metrics = MetricsEngine().compute(TRACES, FAILURE_CLUSTERS, REPAIR_PROPOSALS)
    assert metrics["FRR"] == 0.5


def test_intent_integrity():
    # Eligible = 5. intent_ok=True for t1,t2,t3,t5 (4); t4 has intent_ok=False
    # II = 4/5 = 0.8
    metrics = MetricsEngine().compute(TRACES, FAILURE_CLUSTERS, REPAIR_PROPOSALS)
    assert metrics["II"] == 0.8


def test_impossible_excluded_from_eligible():
    metrics = MetricsEngine().compute(TRACES, FAILURE_CLUSTERS, REPAIR_PROPOSALS)
    assert metrics["population"]["eligible_traces"] == 5
    assert metrics["population"]["impossible_intent_traces"] == 1


def test_latency():
    # Latencies: t1=200, t2=300, t3=250, t4=100, t5=150, t6=50
    # sorted: [50, 100, 150, 200, 250, 300]
    # median of 6 = (150+200)/2 = 175.0
    # p95 idx = int(0.95*6)=5 → value=300
    metrics = MetricsEngine().compute(TRACES)
    assert metrics["latency"]["median_ms"] == 175.0
    assert metrics["latency"]["p95_ms"] == 300


def test_llm_call_total():
    metrics = MetricsEngine().compute(TRACES)
    # 2+3+1+1+2+0 = 9
    assert metrics["llm"]["total_calls"] == 9


def test_reporter_json():
    metrics = MetricsEngine().compute(TRACES, FAILURE_CLUSTERS, REPAIR_PROPOSALS)
    j = MetricsReporter.to_json(metrics)
    import json; data = json.loads(j)
    assert data["RTY"] == 0.6


def test_reporter_csv():
    metrics = MetricsEngine().compute(TRACES, FAILURE_CLUSTERS, REPAIR_PROPOSALS)
    csv_out = MetricsReporter.to_csv(metrics)
    assert "RTY" in csv_out
    assert "0.6" in csv_out


def test_reporter_markdown():
    metrics = MetricsEngine().compute(TRACES, FAILURE_CLUSTERS, REPAIR_PROPOSALS)
    md = MetricsReporter.to_markdown(metrics)
    assert "# CommerceTwin Metrics Report" in md
    assert "RTY" in md
    assert "SYNTHETIC" in md
