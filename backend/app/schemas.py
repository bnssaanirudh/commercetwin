from pydantic import BaseModel, Field, conint, ConfigDict
from typing import Any, Dict, List, Optional
from datetime import datetime

# Domain Schemas with strict financial boundaries (no floats)

class PaymentOperationBase(BaseModel):
    trace_id: str
    amount_paise: conint(ge=0) # type: ignore
    currency: str = "INR"
    state: str
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
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
    description: Optional[str] = None
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
    proposed_patch: Dict[str, Any]
    confidence: Optional[int] = Field(None, ge=0, le=100)
    estimated_repair_cost_paise: Optional[conint(ge=0)] = None # type: ignore
    status: str = "proposed"

class TraceEventCreate(BaseModel):
    event_type: str
    payload: Dict[str, Any]
