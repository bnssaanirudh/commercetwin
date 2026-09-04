from typing import Dict, Set

# Monotonic state hierarchy: Higher value = later state.
# Once a higher state is reached, lower states are ignored.
STATE_HIERARCHY = {
    "created": 1,
    "authorized": 2,
    "captured": 3,
    "failed": 3  # Terminal state
}

class WebhookProcessor:
    def __init__(self):
        # Store processed razorpay-event-id to achieve idempotency
        self.processed_events: Set[str] = set()
        # Track monotonic state per payment/order. Key: payment_id, Value: highest state reached
        self.payment_states: Dict[str, str] = {}

    def process(self, event_id: str, event_type: str, payload: dict) -> bool:
        """
        Processes a webhook event idempotently and monotonically using the database.
        Returns True if processed or safely ignored (e.g. duplicate or out-of-order),
        Returns False if malformed.
        """
        if not event_id:
            return False

        # Map razorpay events to our internal states
        event_state_map = {
            "payment.authorized": "authorized",
            "payment.captured": "captured",
            "payment.failed": "failed",
        }

        target_state = event_state_map.get(event_type)
        if not target_state:
            return True

        from app.db import SessionLocal
        from app.models import ProcessedWebhookEvent
        from sqlalchemy.exc import IntegrityError
        
        db = SessionLocal()
        try:
            # Idempotency check via unique constraint
            event = ProcessedWebhookEvent(
                razorpay_event_id=event_id,
                event_type=event_type,
                processed_state=target_state
            )
            db.add(event)
            db.commit()
        except IntegrityError:
            db.rollback()
            # Idempotency: already processed, safe to return success
            return True
        finally:
            db.close()

        # Try to process monotonic state transition
        try:
            payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
            payment_id = payment_entity.get("id")
            order_id = payment_entity.get("order_id")
            
            if not order_id:
                return False
                
            db = SessionLocal()
            try:
                from app.models import PaymentOperation
                op = db.query(PaymentOperation).filter(PaymentOperation.razorpay_order_id == order_id).first()
                if op:
                    current_state = op.state
                    current_level = STATE_HIERARCHY.get(current_state, 0)
                    target_level = STATE_HIERARCHY.get(target_state, 0)
                    
                    if target_level > current_level:
                        op.state = target_state
                        if payment_id:
                            op.razorpay_payment_id = payment_id
                        db.commit()
                return True
            finally:
                db.close()
            
        except Exception:
            return False

# Global instance for the router to use
webhook_processor = WebhookProcessor()
