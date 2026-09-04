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
        Processes a webhook event idempotently and monotonically.
        Returns True if processed or safely ignored (e.g. duplicate or out-of-order),
        Returns False if malformed.
        """
        if not event_id:
            # If no event ID, we can't safely deduplicate. Reject or treat as malformed.
            return False

        if event_id in self.processed_events:
            # Idempotency: already processed, safe to return success
            return True

        # Map razorpay events to our internal states
        event_state_map = {
            "payment.authorized": "authorized",
            "payment.captured": "captured",
            "payment.failed": "failed",
        }

        target_state = event_state_map.get(event_type)
        if not target_state:
            # Unknown event, safely ignore
            self.processed_events.add(event_id)
            return True

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
                # Here we would normally emit a domain event or update a database
                
            # Mark event as processed regardless of whether it mutated state
            self.processed_events.add(event_id)
            return True
            
        except Exception:
            return False

# Global instance for the router to use
webhook_processor = WebhookProcessor()
