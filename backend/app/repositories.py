import uuid
from typing import Any

from sqlalchemy.orm import Session

from . import models, schemas


class BaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db


class MerchantRepository(BaseRepository):
    def get_merchant(self, merchant_id: str) -> models.Merchant | None:
        return self.db.query(models.Merchant).filter(
            models.Merchant.merchant_id == merchant_id
        ).first()

    def get_product(self, sku: str) -> models.Product | None:
        return self.db.query(models.Product).filter(
            models.Product.sku == sku
        ).first()

    def get_pricing(self, sku: str) -> models.PricingSnapshot | None:
        return (
            self.db.query(models.PricingSnapshot)
            .filter(models.PricingSnapshot.sku == sku)
            .order_by(models.PricingSnapshot.version.desc())
            .first()
        )

    def get_inventory(self, sku: str) -> models.InventorySnapshot | None:
        return (
            self.db.query(models.InventorySnapshot)
            .filter(models.InventorySnapshot.sku == sku)
            .order_by(models.InventorySnapshot.version.desc())
            .first()
        )


class PaymentRepository(BaseRepository):
    def create_payment_operation(self, op: schemas.PaymentOperationCreate) -> models.PaymentOperation:
        db_op = models.PaymentOperation(
            operation_id=str(uuid.uuid4()),
            **op.model_dump(),
        )
        self.db.add(db_op)
        self.db.commit()
        self.db.refresh(db_op)
        return db_op

    def process_webhook_event(
        self, event_id: str, event_type: str, payload: dict[str, Any]
    ) -> models.ProcessedWebhookEvent:
        db_event = models.ProcessedWebhookEvent(
            razorpay_event_id=event_id,
            event_type=event_type,
            processed_state="PROCESSED",
        )
        self.db.add(db_event)
        self.db.commit()
        self.db.refresh(db_event)
        return db_event


class TraceRepository(BaseRepository):
    def add_event(self, trace_id: str, event: schemas.TraceEventCreate) -> models.TraceEvent:
        db_event = models.TraceEvent(
            trace_id=trace_id,
            **event.model_dump(),
        )
        self.db.add(db_event)
        self.db.commit()
        self.db.refresh(db_event)
        return db_event
