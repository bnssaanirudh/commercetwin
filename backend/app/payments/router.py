import json
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from app.payments.razorpay_client import RazorpayService, RazorpayClientError
from app.payments.config import settings
from app.commerce.runner import CommerceRunner
from app.commerce.state import CommerceState
from app.models import Product

router = APIRouter(prefix="/api/payments", tags=["payments"])
razorpay_service = RazorpayService()

class OrderCreateRequest(BaseModel):
    amount_paise: int
    receipt_id: str
    
class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

@router.post("/order")
async def create_payment_order(req: OrderCreateRequest):
    """
    Creates an order on Razorpay for checkout.
    This should ideally happen AFTER running CommerceRunner validation.
    For this test mode integration, we assume validation is done.
    """
    try:
        order = razorpay_service.create_order(
            amount_paise=req.amount_paise,
            receipt=req.receipt_id
        )
        return {
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": settings.razorpay_key_id  # Safe to return public key to client
        }
    except RazorpayClientError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify")
async def verify_payment(req: PaymentVerifyRequest):
    """
    Verifies the signature from Razorpay checkout.
    """
    is_valid = razorpay_service.verify_payment_signature(
        razorpay_order_id=req.razorpay_order_id,
        razorpay_payment_id=req.razorpay_payment_id,
        razorpay_signature=req.razorpay_signature
    )
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid payment signature")
        
    return {"status": "success", "message": "Payment verified successfully"}

@router.get("/order/{order_id}/reconcile")
async def reconcile_order(order_id: str):
    """
    Fetches the remote order for reconciliation.
    """
    try:
        order = razorpay_service.fetch_order(order_id)
        return {"status": order.get("status"), "amount_paid": order.get("amount_paid")}
    except RazorpayClientError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/webhook")
async def razorpay_webhook(request: Request):
    """
    Webhook handler. Safely validates signature and processes events monotonically.
    """
    from app.payments.webhook_handler import webhook_processor
    
    raw_body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
        
    is_valid = razorpay_service.verify_webhook_signature(raw_body, signature)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid signature")
        
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Malformed payload")
        
    event_id = request.headers.get("X-Razorpay-Event-Id") or payload.get("id")
    event_type = payload.get("event")
    
    success = webhook_processor.process(event_id, event_type, payload)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to process webhook safely")
        
    return {"status": "ok"}
