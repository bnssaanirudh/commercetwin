from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, conint

# Domain Schemas with strict financial boundaries (no floats)

class PaymentOperationBase(BaseModel):
    trace_id: str
    amount_paise: conint(ge=0) # type: ignore
    currency: str = "INR"
    state: str
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    razorpay_signature: str | None = None
    payment_operation_fingerprint: str

class PaymentOperationCreate(PaymentOperationBase):
    pass

class PaymentOperationResponse(PaymentOperationBase):
    operation_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProductBase(BaseModel):
    sku: str
    title: str
    category: str
    description: str | None = None
    catalog_version: int = 1

class PricingSnapshotBase(BaseModel):
    sku: str
    price_paise: conint(ge=0) # type: ignore
    cost_paise: conint(ge=0) # type: ignore
    currency: str = "INR"

class InventorySnapshotBase(BaseModel):
    sku: str
    quantity: conint(ge=0) # type: ignore

class RepairProposalBase(BaseModel):
    failure_id: str
    repair_type: str
    proposed_patch: dict[str, Any]
    confidence: int | None = Field(None, ge=0, le=100)
    estimated_repair_cost_paise: conint(ge=0) | None = None # type: ignore
    status: str = "proposed"

class TraceEventCreate(BaseModel):
    event_type: str
    payload: dict[str, Any]
