"""
Webhook handler for Razorpay payment events.

Design principles:
- Fully DB-authoritative: no in-memory state survives process restart
- Atomic idempotency: idempotency check and state update in a single transaction
- Monotonic state: payment state only advances, never regresses
- HMAC verification: validates webhook signature when secret is configured
"""
import hashlib
import hmac
import logging
from typing import ClassVar

from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

# Monotonic state hierarchy — higher value = later/more-final state.
STATE_HIERARCHY: dict[str, int] = {
    "created": 1,
    "authorized": 2,
    "captured": 3,
    "failed": 3,  # Terminal — same level as captured, cannot un-fail
}

# Map Razorpay event types to internal state tokens
EVENT_STATE_MAP: dict[str, str] = {
    "payment.authorized": "authorized",
    "payment.captured": "captured",
    "payment.failed": "failed",
}


class WebhookProcessor:
    """
    Stateless processor — all state lives in the DB.
    Safe to instantiate per-request or as a singleton.
    """

    # Kept as ClassVar for documentation only — no instance state
    _KNOWN_EVENTS: ClassVar[set[str]] = set(EVENT_STATE_MAP.keys())

    def verify_signature(self, raw_body: bytes, signature: str, secret: str) -> bool:
        """Verify Razorpay HMAC-SHA256 webhook signature."""
        if not secret:
            logger.warning("Webhook verification skipped (no secret configured).")
            return True  # No secret configured — skip verification (dev mode)
        expected = hmac.new(
            secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def process(
        self,
        event_id: str,
        event_type: str,
        payload: dict,
        raw_body: bytes = b"",
        signature: str = "",
    ) -> bool:
        """
        Process a single Razorpay webhook event.

        Returns True  → event accepted and processed (or safely deduplicated)
        Returns False → event rejected (malformed, unknown type, invalid sig)
        """
        if not event_id:
            logger.warning("Webhook rejected: missing event_id")
            return False

        target_state = EVENT_STATE_MAP.get(event_type)
        if not target_state:
            # Unknown event type — silently accept (don't break Razorpay delivery)
            return True

        # Verify HMAC signature when both raw_body and signature are provided
        from app.config import settings
        webhook_secret = getattr(settings, "razorpay_webhook_secret", "")
        if webhook_secret and (
            not raw_body
            or not signature
            or not self.verify_signature(raw_body, signature, webhook_secret)
        ):
            logger.warning("Webhook rejected: invalid HMAC signature event_id=%s", event_id)
            return False

        from app.db import SessionLocal
        from app.models import PaymentOperation, ProcessedWebhookEvent

        db = SessionLocal()
        try:
            # ── ATOMIC BLOCK ─────────────────────────────────────────────
            # Insert the idempotency record. If unique constraint fires,
            # we've already processed this event — return True (safe dup).
            event_record = ProcessedWebhookEvent(
                razorpay_event_id=event_id,
                event_type=event_type,
                processed_state=target_state,
            )
            db.add(event_record)

            # Extract payment details from Razorpay payload
            payment_entity = (
                payload.get("payload", {})
                .get("payment", {})
                .get("entity", {})
            )
            payment_id = payment_entity.get("id")
            order_id = payment_entity.get("order_id")
            remote_amount = payment_entity.get("amount")

            if order_id:
                op = db.query(PaymentOperation).filter(
                    PaymentOperation.razorpay_order_id == order_id
                ).first()

                if op:
                    current_level = STATE_HIERARCHY.get(op.state, 0)
                    target_level = STATE_HIERARCHY.get(target_state, 0)

                    if target_level > current_level:
                        # Legal monotonic advancement
                        op.state = target_state
                        if payment_id:
                            op.razorpay_payment_id = payment_id

                        if remote_amount is not None and remote_amount != op.amount_paise:
                            logger.error(
                                "AMOUNT_MISMATCH order_id=%s expected=%d got=%d",
                                order_id, op.amount_paise, remote_amount,
                            )
                            # Tampering detected — transition to failed state
                            op.state = "failed"
                            db.commit()
                            return False
                else:
                    # Quarantine unknown operations
                    import uuid
                    logger.warning("Quarantining unknown webhook order_id=%s", order_id)
                    quarantine_op = PaymentOperation(
                        operation_id=str(uuid.uuid4()),
                        trace_id="UNKNOWN",
                        amount_paise=remote_amount or 0,
                        state="QUARANTINED",
                        razorpay_order_id=order_id,
                        razorpay_payment_id=payment_id,
                    )
                    db.add(quarantine_op)

            db.commit()
            # ── END ATOMIC BLOCK ─────────────────────────────────────────
            return True

        except IntegrityError:
            db.rollback()
            # Duplicate event_id — safe idempotent return
            logger.debug("Duplicate webhook ignored event_id=%s", event_id)
            return True
        except (OSError, ValueError) as e:
            db.rollback()
            logger.error("Webhook processing error event_id=%s: %s", event_id, e)
            return False
        finally:
            db.close()


# Module-level singleton for use by the FastAPI router
webhook_processor = WebhookProcessor()
