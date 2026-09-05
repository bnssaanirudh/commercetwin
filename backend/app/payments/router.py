import hashlib
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.payments.razorpay_client import RazorpayClientError, RazorpayService

router = APIRouter(prefix="/api/payments", tags=["payments"])
razorpay_service = RazorpayService()


class OrderCreateRequest(BaseModel):
    trace_id: str


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.post("/order")
async def create_payment_order(req: OrderCreateRequest, db: Session = Depends(get_db)):
    """
    Creates an order on Razorpay for checkout based on authoritative backend cart.
    Amount is read from the DB-persisted cart for this trace — never from the client.
    """
    try:
        trace_id = req.trace_id

        # Look up trace and check final state
        from app.models import PaymentOperation, PricingSnapshot, TraceEvent, TransactionTrace

        trace = db.query(TransactionTrace).filter(TransactionTrace.trace_id == trace_id).first()
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")

        if trace.final_classification != "READY_FOR_PAYMENT":
            raise ValueError("Trace is not in READY_FOR_PAYMENT state")

        # Extract cart from TraceEvent
        cart_event = db.query(TraceEvent).filter(
            TraceEvent.trace_id == trace_id,
            TraceEvent.event_type == "CART_CREATED"
        ).order_by(TraceEvent.event_id.desc()).first()

        if not cart_event:
            raise ValueError("No CART_CREATED event found for trace")

        skus = cart_event.payload.get("details", {}).get("skus", [])
        if not skus:
            raise ValueError("Cart is empty")

        # Get canonical pricing from PricingSnapshot
        calculated_amount_paise = 0
        for sku in skus:
            price = db.query(PricingSnapshot).filter(PricingSnapshot.sku == sku).order_by(PricingSnapshot.created_at.desc()).first()
            if price:
                calculated_amount_paise += price.price_paise
            else:
                raise ValueError(f"Pricing not found for {sku}")

        # Generate Idempotent Fingerprint
        # In a real setup, we might also hash the cart skus or versions
        cart_hash = hashlib.sha256(",".join(sorted(skus)).encode()).hexdigest()
        merchant_id = "merchant_1" # mock
        fingerprint_data = f"{merchant_id}||{trace_id}||{cart_hash}||{calculated_amount_paise}||INR"
        fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()

        # Check for existing PaymentOperation
        existing_op = db.query(PaymentOperation).filter(
            PaymentOperation.payment_operation_fingerprint == fingerprint
        ).first()

        if existing_op:
            if existing_op.razorpay_order_id:
                return {
                    "order_id": existing_op.razorpay_order_id,
                    "amount": existing_op.amount_paise,
                    "currency": existing_op.currency,
                    "key_id": settings.razorpay_key_id,
                    "operation_id": existing_op.operation_id,
                    "fingerprint": existing_op.payment_operation_fingerprint,
                }
            # If it exists but no order id, it might be stuck in creation, we'll just continue and retry creation
            operation_id = existing_op.operation_id
            op = existing_op
        else:
            operation_id = str(uuid.uuid4())
            op = PaymentOperation(
                operation_id=operation_id,
                trace_id=trace_id,
                amount_paise=calculated_amount_paise,
                state="created",
                payment_operation_fingerprint=fingerprint,
                # We don't have order_id yet
            )
            db.add(op)
            db.commit()
            db.refresh(op)

        order = razorpay_service.create_order(
            amount_paise=calculated_amount_paise,
            receipt=trace_id,
        )

        # Now update with the real order ID
        op.razorpay_order_id = order["id"]
        db.commit()

        return {
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": settings.razorpay_key_id,
            "operation_id": operation_id,
            "fingerprint": fingerprint,
        }
    except RazorpayClientError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/verify")
async def verify_payment(req: PaymentVerifyRequest):
    """Verifies the HMAC SHA256 signature returned from Razorpay Checkout."""
    is_valid = razorpay_service.verify_payment_signature(
        razorpay_order_id=req.razorpay_order_id,
        razorpay_payment_id=req.razorpay_payment_id,
        razorpay_signature=req.razorpay_signature,
    )

    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    return {"status": "success", "message": "Payment verified successfully"}


@router.get("/order/{order_id}/reconcile")
async def reconcile_order(order_id: str, db: Session = Depends(get_db)):
    """Fetches the remote order state for reconciliation after ambiguous timeout."""
    from app.models import PaymentOperation
    try:
        order = razorpay_service.fetch_order(order_id)

        # Verify against PaymentOperation
        op = db.query(PaymentOperation).filter(PaymentOperation.razorpay_order_id == order_id).first()
        if not op:
            raise HTTPException(status_code=404, detail="Order not found in database")

        status = order.get("status")
        amount_paid = order.get("amount_paid")

        # Semantic check: Razorpay order exists != Payment Succeeded
        # Must be matching amount and appropriate state
        if status in ("paid", "captured", "authorized"):
            if amount_paid == op.amount_paise:
                op.state = status
                db.commit()
                return {"status": status, "amount_paid": amount_paid, "reconciled": True}
            else:
                return {"status": status, "amount_paid": amount_paid, "reconciled": False, "reason": "Amount mismatch"}

        return {"status": status, "amount_paid": amount_paid, "reconciled": False}
    except RazorpayClientError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/webhook")
async def razorpay_webhook(request: Request):
    """
    Webhook handler. Validates HMAC signature, then routes to the DB-authoritative processor.
    All events are idempotent. State only advances monotonically.
    """
    from app.payments.webhook_handler import webhook_processor

    raw_body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    # Signature verification is delegated to webhook_processor (it knows the secret)
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Malformed payload") from exc

    event_id = request.headers.get("X-Razorpay-Event-Id") or payload.get("id")
    event_type = payload.get("event")

    success = webhook_processor.process(
        event_id, event_type, payload, raw_body=raw_body, signature=signature
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to process webhook safely")

    return {"status": "ok"}
