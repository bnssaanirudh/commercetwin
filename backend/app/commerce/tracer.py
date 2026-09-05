import re
from datetime import UTC, datetime
from typing import Any


class TraceRecorder:
    def __init__(self, trace_id: str, experiment_id: str, buyer_config: str,
                 intent_version: str, merchant_version: int, catalog_version: int):
        self.trace_id = trace_id
        self.experiment_id = experiment_id
        self.buyer_config = buyer_config
        self.intent_version = intent_version
        self.merchant_version = merchant_version
        self.catalog_version = catalog_version
        self.current_state = "INTENT_RECEIVED"
        self.events: list[dict[str, Any]] = []

        # Secret patterns to redact
        self._secret_patterns = [
            re.compile(r'rzp_(?:test|live)_[a-zA-Z0-9]+')
        ]

        # Keys that imply chain-of-thought which we must strip
        self._forbidden_keys = {'thought', 'thinking', 'chain_of_thought', 'reasoning'}

    def _redact_string(self, text: str) -> str:
        redacted = text
        for pattern in self._secret_patterns:
            redacted = pattern.sub('[REDACTED]', redacted)
        return redacted

    def _clean_payload(self, payload: Any) -> Any:
        if isinstance(payload, str):
            return self._redact_string(payload)
        elif isinstance(payload, dict):
            cleaned = {}
            for k, v in payload.items():
                if k.lower() in self._forbidden_keys:
                    continue # Strip this key entirely
                cleaned[k] = self._clean_payload(v)
            return cleaned
        elif isinstance(payload, list):
            return [self._clean_payload(item) for item in payload]
        else:
            return payload

    def record_event(self, event_type: str, payload: dict[str, Any]):
        if event_type == "STATE_ENTERED" and "state" in payload:
            self.current_state = payload["state"]

        cleaned_payload = self._clean_payload(payload)

        self.events.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "payload": cleaned_payload
        })

    def export(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "experiment_id": self.experiment_id,
            "buyer_config": self.buyer_config,
            "intent_version": self.intent_version,
            "merchant_version": self.merchant_version,
            "catalog_version": self.catalog_version,
            "final_state": self.current_state,
            "events": self.events
        }
