import hashlib
import json
import re
from typing import Any

_SECRET_TERMS = frozenset(
    ["secret", "api_key", "authorization", "cookie", "password", "token", "rzp_test", "rzp_live"]
)


def redact_secrets(payload: Any) -> Any:
    """Recursively redacts secrets like API keys, authorization headers, and cookies from payloads."""
    if isinstance(payload, dict):
        redacted: dict[str, Any] = {}
        for k, v in payload.items():
            k_lower = str(k).lower()
            if any(term in k_lower for term in _SECRET_TERMS):
                redacted[k] = "[REDACTED]"
            else:
                redacted[k] = redact_secrets(v)
        return redacted
    if isinstance(payload, list):
        return [redact_secrets(item) for item in payload]
    if isinstance(payload, str):
        if re.search(r"rzp_(test|live)_[a-zA-Z0-9]+", payload):
            return "[REDACTED]"
        if re.search(r"Bearer [a-zA-Z0-9_\-\.]+", payload):
            return "[REDACTED]"
        return payload
    return payload


def hash_trace_event(
    trace_id: str,
    sequence_no: int,
    timestamp: str,
    event_type: str,
    payload: dict[str, Any],
    previous_event_hash: str,
) -> str:
    """Computes a SHA256 hash for a trace event for tamper evidence."""
    redacted_payload = redact_secrets(payload)
    payload_str = json.dumps(redacted_payload, sort_keys=True)
    hash_str = f"{trace_id}||{sequence_no}||{timestamp}||{event_type}||{payload_str}||{previous_event_hash}"
    return hashlib.sha256(hash_str.encode("utf-8")).hexdigest()
