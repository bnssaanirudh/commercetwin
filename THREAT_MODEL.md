# Threat Model

## Actors
- **Synthetic AI Buyer**: Generates natural language intent (Untrusted).
- **Chaos Engine**: Mutates the catalog and intercepts webhooks (Untrusted).
- **Commerce Runner**: Manages the state machine (Trusted).

## Assets
- **Razorpay Secrets**: Stored only in backend configuration.
- **Transaction Traces**: Immutable logs of agent actions.
- **Financial Balances**: Computed purely from persisted raw data in paise.

## Trust Boundaries
- **LLM Boundary**: Context strings and prompts are scrubbed of secrets. The LLM can propose actions but the `CommerceStateMachine` executes them.
- **Repair Boundary**: The `RepairSynthesizer` can only generate JSON patches. It cannot deploy them to production. The `RepairVerifier` tests them strictly in memory.

## Red-Team Matrix
| Scenario | Threat | Mitigation |
|----------|--------|------------|
| Prompt Injection | Buyer intent attempts to override shipping policy. | Agent parses intent purely for constraints; State Machine enforces policy. |
| Arithmetic Bypass | Floating-point injection attempts to underpay. | All financial fields strictly `conint(ge=0)` in paise. |
| Duplicate Execution | Webhook repeats `payment.captured`. | `WebhookProcessor` idempotency blocks duplicate transitions. |
| Log Leakage | Razorpay secrets dump into LLM trace. | Secrets are never injected into context or state traces. |
