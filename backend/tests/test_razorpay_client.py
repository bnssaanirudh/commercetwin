import pytest
import responses
from app.payments.razorpay_client import RazorpayService, RazorpayClientError
from app.payments.config import settings

@pytest.fixture
def mock_service():
    # Ensure test environment uses test keys
    settings.razorpay_key_id = "rzp_test_mock"
    settings.razorpay_key_secret = "mock_secret"
    return RazorpayService()

def test_live_mode_prohibited():
    original = settings.razorpay_key_id
    settings.razorpay_key_id = "rzp_live_mock"
    
    with pytest.raises(ValueError, match="Live Mode is strictly prohibited"):
        RazorpayService()
        
    settings.razorpay_key_id = original

@responses.activate
def test_create_order_success(mock_service):
    responses.add(
        responses.POST,
        "https://api.razorpay.com/v1/orders",
        json={"id": "order_123", "amount": 10000, "currency": "INR", "receipt": "rcpt_1"},
        status=200
    )
    
    order = mock_service.create_order(amount_paise=10000, receipt="rcpt_1")
    assert order["id"] == "order_123"
    assert order["amount"] == 10000

@responses.activate
def test_create_order_invalid_amount(mock_service):
    with pytest.raises(ValueError, match="Amount must be a positive integer in paise"):
        mock_service.create_order(amount_paise=10.50, receipt="rcpt_1")
        
    with pytest.raises(ValueError):
        mock_service.create_order(amount_paise=-100, receipt="rcpt_1")

def test_verify_signature_success(mock_service):
    # Mocking verify_payment_signature locally since it doesn't do an HTTP call
    # The signature logic is: hmac_sha256(order_id + "|" + payment_id, secret)
    import hmac
    import hashlib
    
    order_id = "order_123"
    payment_id = "pay_456"
    msg = f"{order_id}|{payment_id}"
    valid_signature = hmac.new(
        settings.razorpay_key_secret.encode(),
        msg.encode(),
        hashlib.sha256
    ).hexdigest()
    
    assert mock_service.verify_payment_signature(order_id, payment_id, valid_signature) is True

def test_verify_signature_failure(mock_service):
    assert mock_service.verify_payment_signature("order_123", "pay_456", "invalid_sig") is False
