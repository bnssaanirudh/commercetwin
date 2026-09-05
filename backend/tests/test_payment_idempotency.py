"""
Real tests for the CommerceTwin payment idempotency system.
Tests: duplicate payments, delayed webhooks, out-of-order events, restart/replay.
"""
import pytest

from app.db import Base, SessionLocal, engine
from app.models import PaymentOperation
from app.payments.webhook_handler import WebhookProcessor


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def processor():
    return WebhookProcessor()


def _make_payload(payment_id: str, order_id: str = "order_test_001", amount: int = 2500) -> dict:
    return {
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "order_id": order_id,
                    "amount": amount,
                }
            }
        }
    }


def test_first_webhook_accepted(processor, db):
    """A brand-new captured event should be accepted and return True."""
    # Insert matching payment operation in DB
    op = PaymentOperation(
        operation_id="PAY-idem-001",
        trace_id="TRC-001",
        amount_paise=2500,
        currency="INR",
        state="created",
        razorpay_order_id="order_test_002",
        payment_operation_fingerprint="fp_001",
    )
    db.add(op)
    db.commit()

    result = processor.process(
        "evt_idem_001", "payment.captured", _make_payload("pay_001", "order_test_002", 2500)
    )
    assert result is True


def test_duplicate_webhook_is_idempotent(processor, db):
    """Processing the exact same event_id twice must both return True without error."""
    op = PaymentOperation(
        operation_id="PAY-idem-002",
        trace_id="TRC-002",
        amount_paise=2500,
        currency="INR",
        state="created",
        razorpay_order_id="order_test_003",
        payment_operation_fingerprint="fp_002",
    )
    db.add(op)
    db.commit()

    result1 = processor.process(
        "evt_idem_002", "payment.captured", _make_payload("pay_002", "order_test_003", 2500)
    )
    result2 = processor.process(
        "evt_idem_002", "payment.captured", _make_payload("pay_002", "order_test_003", 2500)
    )
    assert result1 is True
    assert result2 is True  # Must not raise — idempotency guarantee


def test_state_does_not_regress(processor, db):
    """If state is already 'captured', an 'authorized' event must NOT downgrade it."""
    op = PaymentOperation(
        operation_id="PAY-idem-003",
        trace_id="TRC-003",
        amount_paise=1000,
        currency="INR",
        state="captured",  # Already at terminal state
        razorpay_order_id="order_test_004",
        payment_operation_fingerprint="fp_003",
    )
    db.add(op)
    db.commit()

    # Try to send an older 'authorized' event — must not downgrade
    result = processor.process(
        "evt_idem_003",
        "payment.authorized",
        _make_payload("pay_003", "order_test_004", 1000),
    )
    assert result is True  # Accepted but state stays 'captured'

    # Confirm state was NOT downgraded
    db.refresh(op)
    assert op.state == "captured"


def test_amount_tamper_rejected(processor, db):
    """Webhook claiming different amount than the DB-persisted amount must be rejected."""
    op = PaymentOperation(
        operation_id="PAY-idem-004",
        trace_id="TRC-004",
        amount_paise=2500,  # Authoritative
        currency="INR",
        state="created",
        razorpay_order_id="order_test_005",
        payment_operation_fingerprint="fp_004",
    )
    db.add(op)
    db.commit()

    # Tampered amount (99999 instead of 2500)
    result = processor.process(
        "evt_idem_004",
        "payment.captured",
        _make_payload("pay_004", "order_test_005", 99999),
    )
    assert result is False


def test_unknown_event_type_silently_accepted(processor):
    """Unknown event types from Razorpay must not break the webhook endpoint."""
    result = processor.process("evt_idem_005", "order.paid", {"payload": {}})
    assert result is True


def test_missing_event_id_rejected(processor):
    """Webhook with no event_id must be rejected."""
    result = processor.process("", "payment.captured", {})
    assert result is False


def test_failed_event_accepted(processor, db):
    """A payment.failed event must be processed and mark state as 'failed'."""
    op = PaymentOperation(
        operation_id="PAY-idem-006",
        trace_id="TRC-006",
        amount_paise=5000,
        currency="INR",
        state="created",
        razorpay_order_id="order_test_006",
        payment_operation_fingerprint="fp_006",
    )
    db.add(op)
    db.commit()

    result = processor.process(
        "evt_idem_006",
        "payment.failed",
        _make_payload("pay_006", "order_test_006", 5000),
    )
    assert result is True

    db.refresh(op)
    assert op.state == "failed"
