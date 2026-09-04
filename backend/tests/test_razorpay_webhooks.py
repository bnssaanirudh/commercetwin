import pytest
import hmac
import hashlib
import json
from fastapi.testclient import TestClient
from app.main import app
from app.payments.config import settings
from app.payments.webhook_handler import webhook_processor

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_webhook_processor():
    """Reset the in-memory state before each test."""
    webhook_processor.processed_events.clear()
    webhook_processor.payment_states.clear()
    settings.razorpay_webhook_secret = "test_secret"

def generate_signature(raw_body: bytes) -> str:
    return hmac.new(
        settings.razorpay_webhook_secret.encode('utf-8'),
        raw_body,
        hashlib.sha256
    ).hexdigest()

def test_webhook_valid_signature_authorized():
    raw_body = json.dumps({
        "id": "evt_1",
        "event": "payment.authorized",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_1"
                }
            }
        }
    }).encode('utf-8')
    
    headers = {
        "X-Razorpay-Signature": generate_signature(raw_body),
        "Content-Type": "application/json"
    }
    
    response = client.post("/api/payments/webhook", content=raw_body, headers=headers)
    assert response.status_code == 200
    assert webhook_processor.payment_states["pay_1"] == "authorized"
    assert "evt_1" in webhook_processor.processed_events

def test_webhook_invalid_signature():
    raw_body = json.dumps({"id": "evt_2", "event": "payment.authorized"}).encode('utf-8')
    headers = {
        "X-Razorpay-Signature": "invalid_sig",
        "Content-Type": "application/json"
    }
    
    response = client.post("/api/payments/webhook", content=raw_body, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid signature"

def test_webhook_duplicate_event():
    raw_body = json.dumps({
        "id": "evt_3",
        "event": "payment.authorized",
        "payload": {"payment": {"entity": {"id": "pay_3"}}}
    }).encode('utf-8')
    
    headers = {
        "X-Razorpay-Signature": generate_signature(raw_body),
        "Content-Type": "application/json"
    }
    
    # Send first time
    response1 = client.post("/api/payments/webhook", content=raw_body, headers=headers)
    assert response1.status_code == 200
    assert webhook_processor.payment_states["pay_3"] == "authorized"
    
    # Send second time (duplicate)
    # Change the state manually to prove it doesn't get mutated again
    webhook_processor.payment_states["pay_3"] = "captured"
    response2 = client.post("/api/payments/webhook", content=raw_body, headers=headers)
    assert response2.status_code == 200
    # State should remain captured, proving the duplicate was ignored monotonically/idempotently
    assert webhook_processor.payment_states["pay_3"] == "captured"

def test_webhook_out_of_order_events():
    # 1. Send captured first
    raw_body_cap = json.dumps({
        "id": "evt_cap",
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": "pay_4"}}}
    }).encode('utf-8')
    
    headers_cap = {
        "X-Razorpay-Signature": generate_signature(raw_body_cap),
        "Content-Type": "application/json"
    }
    response_cap = client.post("/api/payments/webhook", content=raw_body_cap, headers=headers_cap)
    assert response_cap.status_code == 200
    assert webhook_processor.payment_states["pay_4"] == "captured"
    
    # 2. Send authorized later
    raw_body_auth = json.dumps({
        "id": "evt_auth",
        "event": "payment.authorized",
        "payload": {"payment": {"entity": {"id": "pay_4"}}}
    }).encode('utf-8')
    
    headers_auth = {
        "X-Razorpay-Signature": generate_signature(raw_body_auth),
        "Content-Type": "application/json"
    }
    response_auth = client.post("/api/payments/webhook", content=raw_body_auth, headers=headers_auth)
    assert response_auth.status_code == 200
    # The state should strictly remain captured, ignoring the stale authorized event
    assert webhook_processor.payment_states["pay_4"] == "captured"

def test_webhook_replayed_old_event():
    # Exactly identical to duplicate event essentially, but explicitly showing idempotency
    raw_body = json.dumps({
        "id": "evt_replay",
        "event": "payment.failed",
        "payload": {"payment": {"entity": {"id": "pay_5"}}}
    }).encode('utf-8')
    
    headers = {
        "X-Razorpay-Signature": generate_signature(raw_body),
        "Content-Type": "application/json"
    }
    client.post("/api/payments/webhook", content=raw_body, headers=headers)
    assert len(webhook_processor.processed_events) == 1
    
    client.post("/api/payments/webhook", content=raw_body, headers=headers)
    assert len(webhook_processor.processed_events) == 1  # No duplicate inserts

def test_webhook_unknown_event_type():
    raw_body = json.dumps({
        "id": "evt_unk",
        "event": "payment.refunded", # Unknown to our processor
        "payload": {"payment": {"entity": {"id": "pay_6"}}}
    }).encode('utf-8')
    
    headers = {
        "X-Razorpay-Signature": generate_signature(raw_body),
        "Content-Type": "application/json"
    }
    response = client.post("/api/payments/webhook", content=raw_body, headers=headers)
    
    # Should safely return 200 without mutating any order state
    assert response.status_code == 200
    assert "pay_6" not in webhook_processor.payment_states
    # But it is marked processed
    assert "evt_unk" in webhook_processor.processed_events

def test_webhook_malformed_payload():
    # Valid signature but broken json (FastAPI testclient will encode it, so we mock it manually)
    malformed_raw = b"{invalid_json"
    sig = hmac.new(
        settings.razorpay_webhook_secret.encode('utf-8'),
        malformed_raw,
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        "X-Razorpay-Signature": sig,
        "Content-Type": "application/json"
    }
    
    response = client.post("/api/payments/webhook", content=malformed_raw, headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Malformed payload"
