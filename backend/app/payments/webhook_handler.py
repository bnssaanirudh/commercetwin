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

        # Try to process monotonic state transition (in a real system, update payment operation)
        try:
            payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
            payment_id = payment_entity.get("id")
            
            if not payment_id:
                return False
                
            current_state = self.payment_states.get(payment_id, "created")
            
            current_level = STATE_HIERARCHY.get(current_state, 0)
            target_level = STATE_HIERARCHY.get(target_state, 0)
            
            if target_level > current_level:
                # Monotonic progression: only advance if the new state is strictly greater
                self.payment_states[payment_id] = target_state
                
            return True
            
        except Exception:
            return False

# Global instance for the router to use
webhook_processor = WebhookProcessor()
