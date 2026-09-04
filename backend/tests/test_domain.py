import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError
import uuid

from app.models import Base, InventorySnapshot, PricingSnapshot, PaymentOperation, ProcessedWebhookEvent, Experiment
from app.schemas import PaymentOperationCreate, PricingSnapshotBase

# Setup test DB in memory
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_pydantic_amount_validation():
    # Should fail due to float (if strict) or cast, but schema ensures int >= 0
    # Let's test negative value rejection by Pydantic
    with pytest.raises(ValidationError):
        PricingSnapshotBase(sku="TEST1", price_paise=-100, cost_paise=50)

def test_db_inventory_bounds(db):
    # Setup dummy merchant and product first due to foreign keys, or disable FK for sqlite temporarily
    # SQLite in-memory default doesn't enforce FKs unless PRAGMA foreign_keys=ON is run.
    # We will test the CheckConstraint.
    
    # Positive inventory works
    inv = InventorySnapshot(sku="TEST1", merchant_id="M1", quantity=10, version=1)
    db.add(inv)
    db.commit()

    # Negative inventory fails CheckConstraint
    inv_neg = InventorySnapshot(sku="TEST2", merchant_id="M1", quantity=-5, version=1)
    db.add(inv_neg)
    with pytest.raises(IntegrityError):
        db.commit()

def test_db_payment_amount_negative(db):
    payment = PaymentOperation(
        operation_id="op1",
        trace_id="t1",
        amount_paise=-500,
        state="created",
        payment_operation_fingerprint="f1"
    )
    db.add(payment)
    with pytest.raises(IntegrityError):
        db.commit()

def test_duplicate_operation_fingerprints(db):
    op1 = PaymentOperation(
        operation_id="op1",
        trace_id="t1",
        amount_paise=1000,
        state="created",
        payment_operation_fingerprint="f1"
    )
    db.add(op1)
    db.commit()

    op2 = PaymentOperation(
        operation_id="op2",
        trace_id="t1",
        amount_paise=1000,
        state="created",
        payment_operation_fingerprint="f1" # Duplicate fingerprint
    )
    db.add(op2)
    with pytest.raises(IntegrityError):
        db.commit()

def test_duplicate_webhook_ids(db):
    evt1 = ProcessedWebhookEvent(razorpay_event_id="evt_123", event_type="payment.captured", processed_state="DONE")
    db.add(evt1)
    db.commit()

    evt2 = ProcessedWebhookEvent(razorpay_event_id="evt_123", event_type="payment.failed", processed_state="DONE")
    db.add(evt2)
    with pytest.raises(IntegrityError):
        db.commit()

def test_experiment_seed_persistence(db):
    exp = Experiment(
        experiment_id="exp1",
        merchant_version=1,
        buyer_cohort_version="v1",
        chaos_profile="none",
        seed=12345
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    assert exp.seed == 12345
