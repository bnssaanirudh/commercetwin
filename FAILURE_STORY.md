# Failure Story

This document captures the two most critical failures we discovered during our automated stress tests, and how the CommerceTwin architecture fundamentally solved them.

## 1. The Missing Wattage Catalog Leak
**What broke**: A buyer wanted a 65W USB-C charger. The catalog data was corrupted (via Chaos engine), dropping the strongly typed `power_watts` key but leaving "65W" in the unstructured description.
**Assumption**: The semantic AI buyer would "figure it out."
**Reality**: The AI buyer rejected the product because it lacked a verifiable safety schema. The trace aborted.
**Exact Architectural Fix**: The `FailureLocalizer` mapped this to `MISSING_TYPED_ATTRIBUTE`. The `RepairSynthesizer` proposed a patch to inject `key="power_watts", value="65"`.
**Proof Test**: The `RepairVerifier` applied the patch in a sandbox, re-ran the exact intent, and the transaction succeeded.

## 2. The Idempotency Webhook Failure
**What broke**: Razorpay processed a successful transaction, but the network connection died before the server received the 200 OK.
**Assumption**: The client would just retry the payment.
**Reality**: Retrying the payment would double-charge the user if the backend didn't track state properly.
**Exact Architectural Fix**: The system transitioned to `AMBIGUOUS_REMOTE_STATE`. The deterministic `WebhookProcessor` explicitly deduplicates events via `razorpay_event_id` and checks the monotonic order.
**Proof Test**: A duplicate webhook simulation was triggered in `run_demo.py` (Stage 10). The duplicate was safely ignored (idempotent), preventing double-charging.
