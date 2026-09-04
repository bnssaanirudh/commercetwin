import razorpay
from app.payments.config import settings

class RazorpayClientError(Exception):
    pass

class RazorpayService:
    def __init__(self):
        # Always run in test mode logic; assert that we are not using live keys
        if settings.razorpay_key_id.startswith("rzp_live"):
            raise ValueError("Live Mode is strictly prohibited. Please use Test Mode keys.")
            
        self.client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))

    def create_order(self, amount_paise: int, receipt: str, notes: dict = None) -> dict:
        """
        Creates an order securely on the server.
        Amount must be integer currency subunit (paise).
        """
        if not isinstance(amount_paise, int) or amount_paise <= 0:
            raise ValueError("Amount must be a positive integer in paise.")

        data = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "notes": notes or {}
        }
        
        try:
            order = self.client.order.create(data=data)
            return order
        except Exception as e:
            raise RazorpayClientError(f"Failed to create order: {str(e)}")

    def verify_payment_signature(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
        """
        Verifies the HMAC SHA256 signature returned from Checkout.
        """
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except razorpay.errors.SignatureVerificationError:
            return False

    def fetch_order(self, order_id: str) -> dict:
        """
        Fetches remote order state for reconciliation.
        """
        try:
            return self.client.order.fetch(order_id)
        except Exception as e:
            raise RazorpayClientError(f"Failed to fetch order: {str(e)}")
            
    def fetch_orders_by_receipt(self, receipt_id: str) -> list:
        """
        Fetches a list of orders matching the provided receipt ID.
        Used during ambiguous state reconciliation to find orphaned orders.
        """
        try:
            # fetch_all returns a dictionary with 'items' as the list of orders
            result = self.client.order.fetch_all({"receipt": receipt_id})
            return result.get("items", [])
        except Exception as e:
            raise RazorpayClientError(f"Failed to fetch orders by receipt: {str(e)}")

    def verify_webhook_signature(self, raw_body: bytes, signature: str) -> bool:
        """
        Verifies the HMAC SHA256 signature of an incoming webhook payload.
        """
        import hmac
        import hashlib
        
        expected_signature = hmac.new(
            settings.razorpay_webhook_secret.encode('utf-8'),
            raw_body,
            hashlib.sha256
        ).hexdigest()
        
        # hmac.compare_digest avoids timing attacks
        return hmac.compare_digest(expected_signature, signature)
