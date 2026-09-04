# Architecture Contract

## Trust Zones
1. **Agent Zone (Untrusted)**: Runs the LLM/Semantic logic. Can make requests but cannot mutate the core database.
2. **State Machine Zone (Trusted)**: Enforces monotonic state transitions (e.g., `DISCOVERY` -> `CART_CREATED` -> `PRECHECK` -> `PAYMENT`).
3. **Core Financial Zone (Strict)**: Validates constraints, handles integer paise arithmetic, and connects to Razorpay.

## Monotonic State Machine
CommerceTwin enforces a one-way state machine. 
Once a transaction enters `READY_FOR_PAYMENT`, it can only transition to `PAYMENT`, `COMPLETED`, `AMBIGUOUS_REMOTE_STATE`, or `ABORTED`. Lower states cannot be re-entered.

## Payment Flow
1. **Pre-check**: Inventory, Price, and Shipping constraints are validated.
2. **Order Creation**: A server-side call creates a Razorpay Test Mode order.
3. **Reconciliation**: A deterministic webhook handler (`WebhookProcessor`) manages idempotency. If a webhook drops or times out, the system enters `AMBIGUOUS_REMOTE_STATE` and queries the remote state directly to avoid duplicates.

## Replay Flow
1. **Trace Isolation**: Failed traces are exported into a sandbox.
2. **Patch Application**: The `RepairSynthesizer` applies a JSON diff to the sandbox catalog/policy.
3. **Replay**: The exact same buyer intent (with fixed seed) is replayed through the sandbox.
4. **Validation**: Only if the state reaches `READY_FOR_PAYMENT` is the repair marked as verified.
