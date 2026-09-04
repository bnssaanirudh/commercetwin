import pytest
from app.commerce.tracer import TraceRecorder
from app.commerce.timeline import TraceTimelineRenderer

@pytest.fixture
def tracer():
    return TraceRecorder(
        trace_id="TR-1",
        experiment_id="EXP-1",
        buyer_config="HybridBuyer",
        intent_version="1.0",
        merchant_version=1,
        catalog_version=1
    )

def test_trace_completeness_and_ordering(tracer):
    tracer.record_event("STATE_ENTERED", {"state": "DISCOVERY"})
    tracer.record_event("CANDIDATE_REJECTED", {"sku": "SKU-1", "reason_code": "MIN_ATTRIBUTE_NOT_MET"})
    tracer.record_event("STATE_ENTERED", {"state": "ABORTED", "details": {"reason": "NO_VALID_PRODUCTS"}})
    
    data = tracer.export()
    
    assert data["trace_id"] == "TR-1"
    assert data["final_state"] == "ABORTED"
    assert len(data["events"]) == 3
    
    # Ordering
    assert data["events"][0]["event_type"] == "STATE_ENTERED"
    assert data["events"][1]["event_type"] == "CANDIDATE_REJECTED"
    assert data["events"][2]["event_type"] == "STATE_ENTERED"
    
    # Timestamps exist and are ordered
    assert data["events"][0]["timestamp"] <= data["events"][1]["timestamp"]

def test_secret_redaction(tracer):
    tracer.record_event("PAYMENT_PENDING", {
        "order_id": "order_123",
        "signature": "rzp_test_secret1234567890",
        "live_signature": "rzp_live_abc123"
    })
    
    data = tracer.export()
    payload = data["events"][0]["payload"]
    
    assert payload["order_id"] == "order_123"
    assert payload["signature"] == "[REDACTED]"
    assert payload["live_signature"] == "[REDACTED]"

def test_chain_of_thought_removal(tracer):
    tracer.record_event("MODEL_CALL", {
        "model": "gpt-4",
        "thought": "I should reject this item because the budget is exceeded.",
        "chain_of_thought": "Step 1... Step 2...",
        "structured_decision": {"action": "reject"}
    })
    
    data = tracer.export()
    payload = data["events"][0]["payload"]
    
    assert "model" in payload
    assert "structured_decision" in payload
    assert "thought" not in payload
    assert "chain_of_thought" not in payload

def test_timeline_rendering(tracer):
    tracer.record_event("STATE_ENTERED", {"state": "DISCOVERY"})
    tracer.record_event("CANDIDATE_REJECTED", {"sku": "SKU-1", "reason_code": "MIN_ATTRIBUTE_NOT_MET"})
    tracer.record_event("STATE_ENTERED", {"state": "ABORTED", "details": {"reason": "NO_VALID_PRODUCTS"}})
    
    data = tracer.export()
    output = TraceTimelineRenderer.render(data)
    
    assert "Trace ID: TR-1" in output
    assert "[STATE] DISCOVERY" in output
    assert "[EVALUATION] Rejected SKU-1 (MIN_ATTRIBUTE_NOT_MET)" in output
    assert "[STATE] ABORTED" in output
    assert "Reason: NO_VALID_PRODUCTS" in output
    assert "Final State: ABORTED" in output
