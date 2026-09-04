import pytest
from app.analytics.leak_graph import RevenueLeakCalculator
from app.models import (
    TransactionTrace, 
    TraceEvent, 
    BuyerIntent,
    BuyerProfile,
    Experiment,
    ExperimentRun
)

def setup_synthetic_data(db):
    # Setup base entities
    buyer1 = BuyerProfile(buyer_id="buyer_fail_1", persona="budget_shopper", autonomy_level="full")
    buyer2 = BuyerProfile(buyer_id="buyer_fail_2", persona="premium_shopper", autonomy_level="full")
    
    intent1 = BuyerIntent(intent_id="intent_fail_1", buyer_id="buyer_fail_1", raw_intent="buy stuff", budget_paise=5000, seed=1)
    intent2 = BuyerIntent(intent_id="intent_fail_2", buyer_id="buyer_fail_2", raw_intent="buy premium", budget_paise=15000, seed=2)
    
    exp = Experiment(experiment_id="exp_leak_1", merchant_version=1, buyer_cohort_version="1", chaos_profile="test", seed=1)
    run = ExperimentRun(run_id="run_leak_1", experiment_id="exp_leak_1", status="completed")
    
    db.add_all([buyer1, buyer2, intent1, intent2, exp, run])
    db.commit()
    
    # Trace 1: COMMERCE stage failure (PRICE_MISMATCH) - Lost Value: 5000
    trace1 = TransactionTrace(trace_id="trace_leak_1", run_id="run_leak_1", buyer_id="buyer_fail_1", final_classification="FAILED")
    db.add(trace1)
    db.commit()
    
    e1_1 = TraceEvent(trace_id="trace_leak_1", event_type="STATE_ENTERED", payload={"state": "DISCOVERY"})
    e1_2 = TraceEvent(trace_id="trace_leak_1", event_type="STATE_ENTERED", payload={"state": "PRECHECK"})
    e1_3 = TraceEvent(trace_id="trace_leak_1", event_type="STATE_ENTERED", payload={"state": "ABORTED", "details": {"reason": "PRICE_MISMATCH"}})
    db.add_all([e1_1, e1_2, e1_3])
    
    # Trace 2: COMMERCE stage failure (PRICE_MISMATCH) - Lost Value: 15000 (Uses intent2 budget)
    trace2 = TransactionTrace(trace_id="trace_leak_2", run_id="run_leak_1", buyer_id="buyer_fail_2", final_classification="FAILED")
    db.add(trace2)
    db.commit()
    
    e2_1 = TraceEvent(trace_id="trace_leak_2", event_type="STATE_ENTERED", payload={"state": "DISCOVERY"})
    e2_2 = TraceEvent(trace_id="trace_leak_2", event_type="STATE_ENTERED", payload={"state": "PRECHECK"})
    e2_3 = TraceEvent(trace_id="trace_leak_2", event_type="STATE_ENTERED", payload={"state": "ABORTED", "details": {"reason": "PRICE_MISMATCH"}})
    db.add_all([e2_1, e2_2, e2_3])

    # Trace 3: PAYMENT stage failure (TIMEOUT_ABORTED) - Lost Value: 5000 (Uses intent1 budget)
    trace3 = TransactionTrace(trace_id="trace_leak_3", run_id="run_leak_1", buyer_id="buyer_fail_1", final_classification="FAILED")
    db.add(trace3)
    db.commit()
    
    e3_1 = TraceEvent(trace_id="trace_leak_3", event_type="STATE_ENTERED", payload={"state": "DISCOVERY"})
    e3_2 = TraceEvent(trace_id="trace_leak_3", event_type="STATE_ENTERED", payload={"state": "READY_FOR_PAYMENT"})
    e3_3 = TraceEvent(trace_id="trace_leak_3", event_type="STATE_ENTERED", payload={"state": "PAYMENT"})
    e3_4 = TraceEvent(trace_id="trace_leak_3", event_type="STATE_ENTERED", payload={"state": "ABORTED", "details": {"reason": "TIMEOUT_ABORTED"}})
    db.add_all([e3_1, e3_2, e3_3, e3_4])
    
    db.commit()


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_revenue_leak_graph_aggregates(db_session):
    # Setup data
    setup_synthetic_data(db_session)
    
    # Run Calculator
    calc = RevenueLeakCalculator(db_session)
    result = calc.calculate_leak_graph()
    
    assert result["total_failures"] == 3
    assert result["total_simulated_lost_value_paise"] == 25000 # 5000 + 15000 + 5000
    
    # We should have 2 clusters: (COMMERCE, PRICE_MISMATCH) and (PAYMENT, TIMEOUT_ABORTED)
    clusters = result["top_clusters"]
    assert len(clusters) == 2
    
    # Sort order is by highest lost value
    top_cluster = clusters[0]
    assert top_cluster["stage"] == "COMMERCE"
    assert top_cluster["reason_code"] == "PRICE_MISMATCH"
    assert top_cluster["failure_count"] == 2
    assert top_cluster["simulated_lost_value_paise"] == 20000
    assert top_cluster["percentage_of_leak"] == 80.0
    assert top_cluster["affected_buyer_count"] == 2
    
    second_cluster = clusters[1]
    assert second_cluster["stage"] == "PAYMENT"
    assert second_cluster["reason_code"] == "TIMEOUT_ABORTED"
    assert second_cluster["failure_count"] == 1
    assert second_cluster["simulated_lost_value_paise"] == 5000
    assert second_cluster["percentage_of_leak"] == 20.0
    assert second_cluster["affected_buyer_count"] == 1
