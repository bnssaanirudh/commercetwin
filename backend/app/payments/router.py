import hashlib
import json
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.payments.config import settings
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
async def create_payment_order(req: OrderCreateRequest):
    """
    Creates an order on Razorpay for checkout based on authoritative backend cart.
    Amount is read from the DB-persisted cart for this trace — never from the client.
    """
    try:
        trace_id = req.trace_id

        # Authoritative amount from DB (mock: 2500 paise = ₹25 for demo)
        # In production: query TransactionTrace → cart → sum canonical prices
        calculated_amount_paise = 2500

        fingerprint_data = f"{trace_id}||v1||{calculated_amount_paise}||merchant_1"
        fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()

        order = razorpay_service.create_order(
            amount_paise=calculated_amount_paise,
            receipt=trace_id,
        )
        return {
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": settings.razorpay_key_id,
            "operation_id": str(uuid.uuid4()),
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
async def reconcile_order(order_id: str):
    """Fetches the remote order state for reconciliation after ambiguous timeout."""
    try:
        order = razorpay_service.fetch_order(order_id)
        return {"status": order.get("status"), "amount_paid": order.get("amount_paid")}
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
