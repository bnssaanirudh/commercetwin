from app.analytics.metrics import MetricsEngine

def test_metrics_calculation():
    traces = [
        {"trace_id": "TRC-1", "is_impossible_intent": False, "final_classification": "COMPLETED", "final_amount_paise": 1000, "intent_integrity_ok": True, "journey_start_ms": 100, "journey_end_ms": 200},
        {"trace_id": "TRC-2", "is_impossible_intent": False, "final_classification": "FAILED", "recovered": True, "journey_start_ms": 100, "journey_end_ms": 300},
        {"trace_id": "TRC-3", "is_impossible_intent": True, "journey_start_ms": 100, "journey_end_ms": 400},
        {"trace_id": "TRC-4", "is_impossible_intent": False, "constraint_violated": True, "journey_start_ms": 100, "journey_end_ms": 500},
    ]
    
    engine = MetricsEngine()
    metrics = engine.compute(traces)
    
    assert metrics["RTY"] == 0.3333 # 1 completed / 3 eligible
    assert metrics["II"] == 0.3333  # 1 ok / 3 eligible
    assert metrics["FRR"] == 1.0    # 1 recovered / 1 failed
    assert metrics["ARC_paise_SYNTHETIC"] == 1000
    assert metrics["CVR"] == 0.25   # 1 violated / 4 total
