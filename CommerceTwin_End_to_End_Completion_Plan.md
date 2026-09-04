# CommerceTwin — End-to-End Completion Plan

> **Repository:** `bnssaanirudh/commercetwin`  
> **Goal:** Turn the current MVP into a technically credible, reproducible, judge-ready Visa internship/buildathon submission.  
> **Core principle:** **No mocked success, no hardcoded metrics, no placeholder evidence. Every claim in the README/demo must be reproducible from executable code.**

---

# 0. Final Target

CommerceTwin should end up as a complete closed-loop agentic-commerce reliability platform:

```text
Merchant Twin
    │
    ├── Catalog
    ├── Inventory
    ├── Pricing
    └── Merchant Policies
            │
            ▼
Synthetic / AI Buyer Cohort
            │
            ▼
Intent Compiler
            │
            ▼
Deterministic Intent Oracle
            │
            ▼
Commerce State Machine
            │
      ┌─────┴─────┐
      │           │
      ▼           ▼
Chaos Engine   Trace Recorder
      │           │
      └─────┬─────┘
            ▼
      Failure Detection
            │
            ▼
      Causal Localizer
            │
            ▼
  Value-at-Risk Calculator
            │
            ▼
      Repair Generator
            │
            ▼
      Repair Guardrails
            │
            ▼
      Sandbox Replay
        ┌───┴────┐
        │        │
      REJECT   VERIFIED
                 │
                 ▼
        READY_FOR_PAYMENT
                 │
                 ▼
         Payment Operation
                 │
                 ▼
            Razorpay
                 │
                 ▼
         PAYMENT_PENDING
           ┌─────┴─────┐
           ▼           ▼
      SUCCEEDED      FAILED
           │
           ▼
       COMPLETED
```

The entire product, demo, metrics, UI, and documentation must use this same path.

---

# 1. Non-Negotiable Release Rules

Before submission, all of the following must be true:

- [ ] GitHub Actions backend workflow is green.
- [ ] GitHub Actions frontend workflow is green.
- [ ] Regression/evaluation workflow is green.
- [ ] No `requirements.txt` references remain unless an actual file exists.
- [ ] Python version is consistent across `pyproject.toml`, local docs, Docker, and CI.
- [ ] No hardcoded evaluation numbers such as `0.85`, `0.40`, `0.92` are used as product/evaluation outputs.
- [ ] No UI silently substitutes fake metrics when the backend fails.
- [ ] No page contains placeholder text such as `This is the X view`.
- [ ] No security test passes only because a boolean defaults to `True`.
- [ ] No README claim is stronger than the executable evidence.
- [ ] The demo script runs the same real service layer used by the API.
- [ ] Razorpay payment amount is calculated server-side.
- [ ] Razorpay order creation does not mean payment completion.
- [ ] Webhook idempotency survives process restarts.
- [ ] All benchmark numbers are generated from committed/raw evaluation traces.
- [ ] The project can be started from a clean clone with documented commands.
- [ ] The repository contains a valid LICENSE.
- [ ] README includes actual screenshots, architecture, benchmark table, setup, and demo steps.

---

# 2. Phase 1 — Make the Repository Build Reliably

## 2.1 Standardize Python

Current project metadata and CI must use the same Python version.

### Target

Use:

```text
Python 3.12
```

### Files to update

- `.github/workflows/test.yml`
- `.github/workflows/commercetwin.yml`
- `README.md`
- `DEMO_RUNBOOK.md`
- `backend/pyproject.toml`
- Docker files when added later

### Acceptance criteria

```bash
python --version
```

must show Python 3.12.x in local setup and CI.

---

## 2.2 Fix Backend Installation

The current CI expects `requirements.txt`, but the project uses `pyproject.toml`.

### Required change

Use editable installation:

```bash
cd backend
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### Update `backend/pyproject.toml`

Ensure dependencies contain at least:

```toml
dependencies = [
    "fastapi",
    "uvicorn[standard]",
    "sqlalchemy",
    "alembic",
    "pydantic",
    "pydantic-settings",
    "requests",
    "razorpay",
    "httpx"
]
```

Development extras should include:

```toml
[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "ruff",
    "mypy"
]
```

Use pinned or bounded versions after verifying compatibility.

### Acceptance criteria

From a clean environment:

```bash
cd backend
pip install -e ".[dev]"
pytest -q
```

must install and execute without missing-module errors.

---

## 2.3 Fix Frontend Build

In:

```text
frontend/src/context/AuthContext.tsx
```

change type import usage.

Use:

```ts
import React, { createContext, useState, useContext } from 'react';
import type { ReactNode } from 'react';
```

### Acceptance criteria

```bash
cd frontend
npm ci
npm run build
npm run lint
```

must all pass.

Do not suppress fatal lint/build problems.

---

## 2.4 Fix CI

Create three clear jobs:

### Backend

```text
install
lint
unit tests
integration tests
coverage
```

### Frontend

```text
npm ci
lint
typecheck
build
```

### Regression

```text
install backend
run frozen benchmark
verify generated output
```

### Acceptance gate

GitHub must show:

```text
backend-tests     PASS
frontend-build    PASS
regression        PASS
```

Do not proceed to submission while CI is red.

---

# 3. Phase 2 — Remove False, Mocked, and Stale Evidence

This phase is mandatory because judge trust is more important than the quantity of documentation.

---

## 3.1 Delete or Rewrite Stale Audit Files

### Remove or completely rewrite

```text
REPO_AUDIT.md
IMPLEMENTATION_STATUS.md
RELEASE_CHECKLIST.md
FINAL_RED_TEAM_AUDIT.md
RED_TEAM_REPORT.md
```

Any rewritten file must reflect the current repository exactly.

---

## 3.2 Remove Mock Benchmark Numbers

Inspect:

```text
backend/app/evals/benchmark.py
```

Remove code such as:

```python
"RTY": 0.85 if system_name == "commercetwin" else 0.40
```

### Preferred solution

Either:

1. delete the test-double benchmark module, or
2. clearly rename it to `benchmark_stub.py` and never use it in production/evaluation.

The only submission-facing metrics must come from the real evaluator.

---

## 3.3 Remove Frontend Fake Metrics

Inspect:

```text
frontend/src/api/client.ts
```

Delete fallback objects such as:

```ts
return {
  RTY: 0.85,
  ...
}
```

### Replace with explicit failure

```ts
throw new Error("Metrics API unavailable");
```

The UI should show:

```text
Backend unavailable
No metrics available
```

Never show successful metrics if the backend is down.

---

## 3.4 Remove Simulated Experiment Output

Inspect:

```text
frontend/src/pages/RunExperiment.tsx
```

Remove:

- `setTimeout` success simulation
- hardcoded trace output
- hardcoded failure localization
- hardcoded repair
- hardcoded replay result

The page must call the real backend.

---

## 3.5 Replace Mock Red-Team Test

Current pattern to remove:

```python
RedTeamScenario(..., passed=True)
assert scenario.passed
```

Every listed security scenario must execute actual system logic.

If a scenario is not implemented, mark it:

```text
NOT IMPLEMENTED
```

rather than `PASS`.

---

# 4. Phase 3 — Repair the Domain Model and Agent Pipeline

---

## 4.1 Fix `ProductAttribute` Usage Everywhere

The SQLAlchemy model defines:

```text
key
value
type
```

Find and replace incompatible use of:

```text
attribute_key
attribute_value
```

### Files to inspect

- `evals/run_benchmark.py`
- `backend/app/buyers/llm_agent.py`
- tests
- scripts
- dataset loaders

### Acceptance criteria

Search repository for:

```text
attribute_key
attribute_value
```

and verify every usage is intentional or removed.

---

## 4.2 Remove Duplicate Discovery/Evaluation

Current orchestration risks calling discovery twice.

Refactor buyer API into:

```python
candidates = agent.discover_candidates()
valid_candidates = agent.evaluate_candidates(candidates)
cart = agent.select_cart(valid_candidates)
```

Change:

```python
select_cart()
```

to accept validated candidates instead of rediscovering.

### Benefit

- one model call per discovery stage;
- deterministic trace;
- no duplicate LLM cost;
- no inconsistent candidate sets.

---

## 4.3 Add Real Optional LLM Adapter

Keep `FakeModelAdapter` for tests.

Add a real provider abstraction such as:

```text
OpenAIAdapter
GeminiAdapter
GroqAdapter
OllamaAdapter
```

Only one real provider is necessary.

### Environment

```env
LLM_PROVIDER=
LLM_API_KEY=
LLM_MODEL=
```

### Requirements

- structured JSON output;
- timeout;
- retry limit;
- schema validation;
- token usage;
- latency;
- failure-safe behavior;
- no secret logging.

### Important

The deterministic oracle must still validate all LLM decisions.

---

# 5. Phase 4 — Build One Real Commerce Orchestration Service

Do not have separate logic in the API, demo, evaluator, and payment code.

Create one orchestration layer.

Suggested file:

```text
backend/app/services/commerce_service.py
```

Suggested responsibilities:

```python
create_experiment(...)
run_trace(...)
inject_chaos(...)
localize_failure(...)
generate_repair(...)
verify_repair(...)
prepare_payment(...)
```

The following must call this service:

- REST API
- demo script
- evaluation runner
- frontend through API

This prevents demo-only behavior.

---

# 6. Phase 5 — Persist the Full Experiment Lifecycle

The database models already exist. Use them.

Persist:

- Merchant
- MerchantTwinVersion
- Product
- ProductAttribute
- InventorySnapshot
- PricingSnapshot
- MerchantPolicy
- BuyerProfile
- BuyerIntent
- Experiment
- ExperimentRun
- TransactionTrace
- TraceEvent
- ChaosInjection
- FailureCluster
- RepairProposal
- ReplayResult
- PaymentOperation
- ProcessedWebhookEvent

---

## 6.1 Required Relationships

Ensure every important record is traceable:

```text
Merchant
  └── Experiment
       └── ExperimentRun
            └── TransactionTrace
                 ├── TraceEvent
                 ├── ChaosInjection
                 ├── FailureCluster
                 ├── ReplayResult
                 └── PaymentOperation
```

A judge should be able to click from metric → trace → failure → repair → replay → payment.

---

# 7. Phase 6 — Make Trace Logging Production-Grade

Current trace logic is conceptually useful but should become persisted and tamper-evident.

---

## 7.1 Persist Trace Events

Each trace event should contain:

```text
event_id
trace_id
sequence_no
timestamp
event_type
state
payload
previous_event_hash
event_hash
```

Hash:

```text
SHA256(trace_id || sequence_no || timestamp || event_type || payload || previous_event_hash)
```

This allows the project to honestly say:

```text
tamper-evident trace chain
```

not immutable unless backed by stronger storage guarantees.

---

## 7.2 Trace Events to Support

At minimum:

```text
INTENT_RECEIVED
INTENT_COMPILED
MODEL_CALL
CANDIDATES_DISCOVERED
CANDIDATE_REJECTED
CART_FINALIZED
STATE_ENTERED
CHAOS_INJECTED
PRECHECK_FAILED
PAYMENT_VALIDATED
PAYMENT_ORDER_CREATED
PAYMENT_WEBHOOK_RECEIVED
PAYMENT_RECONCILED
FAILURE_LOCALIZED
REPAIR_PROPOSED
REPAIR_VERIFIED
REPLAY_COMPLETED
```

---

## 7.3 Secret Redaction

Keep current redaction idea and expand patterns to include:

- Razorpay key IDs
- secrets
- bearer tokens
- API keys
- authorization headers
- cookies
- environment-style secret values

Add tests proving secrets are absent from exported traces.

---

# 8. Phase 7 — Finish the Chaos Engine

Support explicit, deterministic fault profiles.

---

## 8.1 Catalog Chaos

Implement:

- missing typed attribute;
- corrupted attribute format;
- stale product description;
- mismatched category;
- invalid compatibility metadata.

Example:

```json
{
  "type": "DROP_ATTRIBUTE",
  "target_sku": "CHG-65W-01",
  "attribute": "power_watts",
  "seed": 42
}
```

---

## 8.2 Inventory Chaos

Implement:

- inventory goes to zero after cart selection;
- inventory version becomes stale;
- conflicting snapshot.

---

## 8.3 Pricing Chaos

Implement:

- price changes between selection and checkout;
- stale agent-visible price;
- malformed price source.

---

## 8.4 Merchant Policy Chaos

Implement:

- shipping destination becomes unavailable;
- expired promotion;
- incompatible shipping class.

---

## 8.5 Payment Chaos

Keep and complete:

```text
TIMEOUT
DROP_RESPONSE_AFTER_SUCCESS
5XX_ERROR
DUPLICATE_WEBHOOK
OUT_OF_ORDER_WEBHOOK
REPLAYED_WEBHOOK
INVALID_SIGNATURE
```

Every fault must be reproducible from a seed/profile.

---

# 9. Phase 8 — Finish Causal Failure Localization

The hero case must not contain `pass`.

---

## 9.1 Localize Missing Attribute

For:

```text
NO_VALID_PRODUCTS_FOUND
MISSING_REQUIRED_ATTRIBUTE
MISSING_MIN_ATTRIBUTE
```

perform controlled counterfactual replay.

Example process:

```text
Original:
power_watts missing
→ buyer rejects
→ ABORTED

Counterfactual:
restore power_watts from authoritative merchant source
→ same buyer
→ same seed
→ same catalog except one field
→ READY_FOR_PAYMENT
```

Then output:

```json
{
  "hypothesis": "missing_typed_attribute",
  "sku": "CHG-65W-01",
  "attribute": "power_watts",
  "before": "ABORTED",
  "after": "READY_FOR_PAYMENT",
  "confidence": 0.98,
  "intervention_count": 1
}
```

---

## 9.2 Localize Other Failure Classes

Support at least:

```text
stale_inventory
price_drift
shipping_policy_change
missing_typed_attribute
compatibility_metadata_error
payment_timeout
payment_ambiguous_remote_state
```

---

## 9.3 Avoid Overclaiming Causality

Call it:

```text
controlled counterfactual localization
```

rather than universal causal discovery.

Document supported intervention classes.

---

# 10. Phase 9 — Replace “Revenue Leak” With a Defensible Metric

Do not equate buyer budget with actual lost revenue.

Use:

# Agentic Value at Risk (AVaR)

Suggested definition:

```text
AVaR = Σ eligible transaction value for failed traces attributable to a tested failure
```

Also compute:

```text
Recovered Eligible Value (REV)
Verified Capturable Value (VCV)
```

Use `SYNTHETIC` labels everywhere in synthetic experiments.

---

## 10.1 Required Dashboard Metrics

```text
Robust Transaction Yield (RTY)
Intent Integrity (II)
Agentic Value at Risk (AVaR)
Recovered Eligible Value (REV)
Failure Recovery Rate (FRR)
Repair Verification Rate (RVR)
Constraint Violation Rate (CVR)
Median Latency
P95 Latency
LLM Calls
LLM Token Count
```

---

# 11. Phase 10 — Build a Real Repair Generator

The current synthesizer mostly validates caller-provided patches.

Separate responsibilities.

---

## 11.1 `RepairGenerator`

Suggested input:

```json
{
  "failure_cluster": {...},
  "merchant_twin": {...},
  "localized_cause": {...},
  "supporting_traces": [...]
}
```

Suggested output:

```json
{
  "repair_type": "CATALOG_SCHEMA_PATCH",
  "target": {
    "sku": "CHG-65W-01"
  },
  "operations": [
    {
      "op": "add",
      "path": "/attributes/power_watts",
      "value": "65"
    }
  ],
  "value_source": "authoritative_catalog_field",
  "confidence": 0.96
}
```

Do not invent missing factual product values.

If the value cannot be obtained from authoritative merchant data, return:

```text
MANUAL_REVIEW_REQUIRED
```

---

## 11.2 `RepairGuardrail`

Keep rules such as:

- cannot modify buyer constraints;
- cannot invent product facts;
- cannot increase price based on inferred willingness to pay;
- cannot auto-target production;
- supported operation whitelist only;
- schema validation required.

---

## 11.3 Repair Status

Use:

```text
PROPOSED
REJECTED
VERIFIED
MANUAL_REVIEW_REQUIRED
```

Do not auto-mark repairs verified.

---

# 12. Phase 11 — Make Repair Verification Real

Repair replay must use:

```text
same buyer intent
same random seed
same merchant snapshot
same chaos profile
one controlled repair difference
```

---

## 12.1 Success Condition

For a catalog/commerce repair, verification should normally stop at:

```text
READY_FOR_PAYMENT
```

Do not execute a financial action merely to verify a catalog patch.

---

## 12.2 Verification Conditions

A repair is `VERIFIED` only if:

- targeted failure rate improves;
- no buyer hard constraint is violated;
- no merchant hard constraint is violated;
- no new payment-safety issue is introduced;
- replay is deterministic;
- all affected traces are recorded.

---

## 12.3 Report

Example:

```text
Before success rate: 12/100
After success rate: 83/100
Recovered traces: 71
New constraint violations: 0
Payment regressions: 0
Verdict: VERIFIED
```

---

# 13. Phase 12 — Rebuild Evaluation From Raw Evidence

This is required before quoting any performance number.

---

## 13.1 Fix `evals/run_benchmark.py`

Support:

```text
keyword
semantic
llm_only
commercetwin
```

The `commercetwin` option must actually execute the closed loop.

---

## 13.2 Evaluation Systems

Recommended systems:

### Baseline A

Structured / keyword buyer.

### Baseline B

Semantic buyer.

### Baseline C

LLM-only buyer.

### Main system

LLM/semantic buyer protected by CommerceTwin:

```text
agent
+ deterministic oracle
+ state machine
+ chaos detection
+ localization
+ repair
+ replay
```

---

## 13.3 Dataset Split

Keep frozen:

```text
dev.jsonl
val.jsonl
held_out.jsonl
```

Never tune on held-out.

Store dataset hashes.

---

## 13.4 Raw Results

Every run must save:

```text
data/evaluations/<run_id>/
    config.json
    traces.jsonl
    failures.jsonl
    repairs.jsonl
    replay_results.jsonl
    metrics.json
    summary.md
```

---

## 13.5 Reproducibility Metadata

Store:

```json
{
  "git_commit": "...",
  "dataset_hash": "...",
  "seed": 42,
  "system": "commercetwin",
  "split": "held_out",
  "python_version": "...",
  "timestamp": "...",
  "model_provider": "...",
  "model_name": "..."
}
```

---

## 13.6 Statistical Reporting

For major percentage metrics, add:

```text
95% bootstrap confidence interval
```

Do not say “proved” when the evidence is a synthetic benchmark.

Use:

```text
observed
measured
achieved on the frozen synthetic benchmark
```

---

## 13.7 Replace EVALUATION.md

`EVALUATION.md` must include:

```text
dataset size
split policy
systems tested
failure profiles
metrics
exact commands
raw artifact locations
limitations
results table
confidence intervals
```

---

# 14. Phase 13 — Fix Payment Architecture Properly

This is one of the highest-value improvements for Visa.

---

## 14.1 Never Accept Client Amount as Authoritative

Remove payment creation that accepts arbitrary:

```json
{
  "amount_paise": 10000
}
```

Preferred API:

```http
POST /api/v1/payments/order
```

Request:

```json
{
  "trace_id": "TR-..."
}
```

Backend then:

1. retrieves trace;
2. verifies state == `READY_FOR_PAYMENT`;
3. retrieves canonical cart;
4. revalidates inventory;
5. revalidates pricing;
6. revalidates policy;
7. calculates amount;
8. creates `PaymentOperation`;
9. creates Razorpay order.

---

## 14.2 Correct State Lifecycle

Replace:

```text
PAYMENT → COMPLETED
```

with:

```text
READY_FOR_PAYMENT
→ PAYMENT
→ PAYMENT_PENDING
→ PAYMENT_SUCCEEDED
→ COMPLETED
```

Failure:

```text
PAYMENT_PENDING
→ PAYMENT_FAILED
→ ABORTED
```

Ambiguity:

```text
PAYMENT
→ AMBIGUOUS_REMOTE_STATE
→ RECONCILIATION_REQUIRED
→ RECOVERED_SUCCESS
→ COMPLETED
```

---

## 14.3 Persist Payment Operation

Each payment must record:

```text
operation_id
trace_id
amount_paise
currency
state
razorpay_order_id
razorpay_payment_id
fingerprint
created_at
updated_at
```

---

## 14.4 Payment Fingerprint

Generate idempotency fingerprint from immutable logical operation fields, for example:

```text
SHA256(trace_id || cart_version || final_amount || merchant_id)
```

Use a unique database constraint.

---

# 15. Phase 14 — Make Webhooks Persistently Idempotent

Do not depend on in-memory sets.

---

## 15.1 Database-backed Event Deduplication

Use `ProcessedWebhookEvent`.

Make:

```text
razorpay_event_id UNIQUE
```

Processing:

```text
receive webhook
→ validate HMAC
→ begin DB transaction
→ try insert razorpay_event_id
→ if duplicate: return 200 safely
→ validate monotonic state transition
→ update payment operation
→ commit
```

---

## 15.2 Out-of-order Logic

Explicitly define accepted transitions.

Examples:

```text
authorized → captured
created → failed
captured must never go backward to authorized
```

---

## 15.3 Webhook Test Matrix

Real tests must cover:

- [ ] valid signature
- [ ] invalid signature
- [ ] malformed JSON
- [ ] duplicate event
- [ ] replayed old event
- [ ] out-of-order event
- [ ] unknown event
- [ ] DB restart persistence
- [ ] concurrent duplicate processing
- [ ] terminal-state protection

---

# 16. Phase 15 — Rebuild the API Around Real Services

Current placeholder routes must be replaced.

Recommended routes:

```text
GET    /health
GET    /ready

GET    /api/v1/merchants/{merchant_id}
GET    /api/v1/products
POST   /api/v1/experiments
GET    /api/v1/experiments/{id}
POST   /api/v1/experiments/{id}/run

GET    /api/v1/traces
GET    /api/v1/traces/{trace_id}

GET    /api/v1/failures
GET    /api/v1/failures/{failure_id}

POST   /api/v1/failures/{failure_id}/repairs
GET    /api/v1/repairs
GET    /api/v1/repairs/{repair_id}
POST   /api/v1/repairs/{repair_id}/verify

POST   /api/v1/replays
GET    /api/v1/replays/{id}

GET    /api/v1/metrics

POST   /api/v1/payments/order
POST   /api/v1/payments/verify
POST   /api/v1/payments/webhook
GET    /api/v1/payments/{operation_id}
```

---

# 17. Phase 16 — Improve Health and Configuration

---

## 17.1 Single Settings System

Remove duplicate configuration classes.

Create one:

```text
backend/app/config.py
```

with:

```text
APP_ENV
APP_DEBUG
DATABASE_URL
CORS_ORIGINS
LLM_PROVIDER
LLM_API_KEY
LLM_MODEL
RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET
RAZORPAY_WEBHOOK_SECRET
```

---

## 17.2 Test-mode Safety

Reject live Razorpay credentials unless an explicit future production flag is added.

For this project:

```text
live mode must remain disabled
```

---

## 17.3 CORS

Do not use wildcard origin with credentials.

Use:

```env
CORS_ORIGINS=http://localhost:5173
```

and parse a list.

---

## 17.4 Health Endpoints

`/health`:

```text
process alive
```

`/ready`:

```text
database available
required configuration valid
```

Return 503 when dependencies fail.

---

# 18. Phase 17 — Database Reproducibility

Do not depend on committed `commercetwin.db`.

---

## 18.1 Remove Runtime DB File From Git

Add:

```gitignore
*.db
*.sqlite
*.sqlite3
```

---

## 18.2 Initialization

Clean clone flow:

```bash
cd backend
alembic upgrade head
python ../scripts/seed_catalog.py
```

---

## 18.3 Seed Command Must Be Idempotent

Running twice should not duplicate records or fail.

---

# 19. Phase 18 — Build the Judge-Facing Frontend

Do not create many weak pages.

Build five excellent workflows.

---

# Screen 1 — Overview

Display real API-backed metrics:

```text
Transactions Tested
RTY
Intent Integrity
Agentic Value at Risk
Verified Recovered Value
Failures
Verified Repairs
P95 latency
```

Add:

```text
Synthetic benchmark
Razorpay Test Mode
```

badges where relevant.

No hidden mock fallback.

---

# Screen 2 — Live Experiment

Controls:

```text
Buyer configuration
Merchant twin version
Chaos profile
Seed
Number of buyers
```

Button:

```text
Run Experiment
```

Output live state progression:

```text
INTENT_RECEIVED
DISCOVERY
EVALUATION
SELECTION
PRECHECK
ABORTED
```

or success path.

Prefer polling every 0.5–1.0 second or SSE/WebSocket if simple.

---

# Screen 3 — Trace Explorer

Table:

```text
Trace ID
Buyer
Experiment
Final State
Failure Reason
Amount / Eligible Value
Latency
```

Trace detail timeline:

```text
event timestamp
event type
state
safe payload
```

Include chaos injection marker.

---

# Screen 4 — Failure / Repair / Replay

Show:

```text
Failure cluster
Affected traces
Value at risk
Localized cause
Proposed patch
Guardrail status
Replay result
```

Before / after comparison:

```text
BEFORE                      AFTER
MISSING power_watts         power_watts = 65
ABORTED                     READY_FOR_PAYMENT
```

---

# Screen 5 — Payment Safety

Display:

```text
trace_id
payment operation ID
Razorpay order ID
amount
current payment state
webhook history
reconciliation result
```

Include a controlled test-mode action for the hero demo.

---

# 20. Phase 19 — UX Cleanup

- [ ] Remove fake login or implement real auth.
- [ ] Replace “Access Secure Lab” if authentication is not real.
- [ ] Fix “View Documentation” URL.
- [ ] Remove template `frontend/README.md`.
- [ ] Remove unused React/Vite starter assets.
- [ ] Add clear loading states.
- [ ] Add error states.
- [ ] Add empty states.
- [ ] Add retry action.
- [ ] Make tables responsive.
- [ ] Add accessible labels.
- [ ] Preserve keyboard navigation.
- [ ] Use consistent currency formatting.
- [ ] Use one date/time format.
- [ ] Never call synthetic value “production revenue”.

---

# 21. Phase 20 — Replace the Demo Script With a Real Hero Workflow

`scripts/run_demo.py` must call the real orchestration service.

It should execute:

---

## Stage 1 — Clean Transaction

```text
Load clean merchant twin
Run buyer
Reach READY_FOR_PAYMENT
```

---

## Stage 2 — Inject Chaos

```text
DROP_ATTRIBUTE power_watts
```

---

## Stage 3 — Observe Failure

```text
same buyer
same seed
ABORTED
reason = MISSING_MIN_ATTRIBUTE or equivalent
```

---

## Stage 4 — Localize

Run real counterfactual localizer.

Output:

```text
Cause: missing typed attribute power_watts
Confidence: ...
```

---

## Stage 5 — Quantify

Compute AVaR from actual affected eligible traces.

---

## Stage 6 — Generate Repair

Generate patch using authoritative merchant data.

---

## Stage 7 — Guardrail Check

Demonstrate:

```text
production mutation blocked
buyer constraint mutation blocked
unverified invented value blocked
```

---

## Stage 8 — Replay

Apply patch to sandbox twin.

Replay exact failed cohort.

Output real before/after metrics.

---

## Stage 9 — Test-mode Payment

Select one verified trace.

Create Razorpay test order through the real state-machine payment path.

---

## Stage 10 — Payment Chaos

Simulate:

```text
DROP_RESPONSE_AFTER_SUCCESS
```

Reconcile without creating duplicate logical order/payment operation.

---

# 22. Phase 21 — Real Security Test Suite

Replace the fake 24-pass test with real executable tests.

Recommended categories:

---

## Prompt / Model Safety

- [ ] prompt injection in product description
- [ ] buyer tries to override merchant policy
- [ ] hallucinated SKU
- [ ] malformed structured response
- [ ] LLM timeout
- [ ] secret leakage attempt

---

## Commerce Integrity

- [ ] budget exceeded
- [ ] forbidden category
- [ ] incompatible item
- [ ] stale inventory
- [ ] stale pricing
- [ ] unavailable shipping
- [ ] cart mutation after validation

---

## Repair Safety

- [ ] repair modifies buyer constraint
- [ ] repair invents missing product fact
- [ ] repair targets production
- [ ] repair increases price improperly
- [ ] repair creates new constraint violation
- [ ] repair does not improve target cohort

---

## Payment Safety

- [ ] client-supplied amount cannot override canonical amount
- [ ] duplicate logical payment request
- [ ] invalid webhook signature
- [ ] duplicate webhook
- [ ] webhook replay after restart
- [ ] out-of-order event
- [ ] remote success + lost response
- [ ] network timeout before server success
- [ ] duplicate order prevention
- [ ] terminal state cannot regress

---

## Multi-Tenant Safety

- [ ] merchant A cannot read merchant B product
- [ ] merchant A trace cannot be used to create merchant B payment
- [ ] repair cannot mutate another merchant twin

---

# 23. Phase 22 — Automated Quality Gates

Backend:

```bash
ruff check .
mypy app
pytest --cov=app --cov-report=term-missing
```

Target:

```text
critical modules >= 85% coverage
overall >= 75–80%
```

Critical modules:

```text
commerce
payments
analytics/repair
analytics/verifier
analytics/causal
buyers/oracle
chaos
```

Frontend:

```bash
npm run lint
npm run build
```

Optional:

```text
Vitest
React Testing Library
Playwright
```

At minimum add Playwright smoke tests for:

```text
landing
overview
run experiment
trace explorer
repair view
```

---

# 24. Phase 23 — Containerization

Add:

```text
Dockerfile.backend
frontend/Dockerfile
docker-compose.yml
```

Suggested services:

```text
backend
frontend
postgres
```

Optional Redis is not necessary unless genuinely used.

---

## One-command startup

```bash
docker compose up --build
```

Must start the system.

---

# 25. Phase 24 — Deployment

Recommended low-cost deployment:

```text
Frontend: Vercel / Netlify
Backend: Render / Railway / Fly.io
Database: managed PostgreSQL free/low-cost tier
```

Use only Razorpay Test Mode.

Environment secrets must never be committed.

---

# 26. Phase 25 — Repository Cleanup

Remove:

- stale generated audit files;
- unused starter assets;
- duplicate docs;
- dead code;
- unused imports;
- commented prototype code;
- committed runtime DB;
- build outputs;
- logs;
- fake demos.

Add:

```text
LICENSE
CONTRIBUTING.md
SECURITY.md
```

Optional but useful.

---

# 27. Phase 26 — README Structure

Final README should contain this exact information order:

---

## CommerceTwin

One sentence:

> A closed-loop reliability lab for agentic commerce that injects merchant-side failures, traces transaction breakage, proposes bounded repairs, verifies them through deterministic replay, and safely gates Razorpay Test Mode payment execution.

---

## Why

Explain:

```text
AI-readable ≠ AI-transactable.
```

---

## Demo GIF / Screenshot

Show hero path.

---

## Architecture

Include real diagram.

---

## Core Workflow

```text
Simulate → Break → Trace → Localize → Repair → Replay → Pay
```

---

## Key Safety Properties

- deterministic hard-constraint oracle;
- server-calculated amount;
- payment state machine;
- test-mode-only financial execution;
- persistent webhook idempotency;
- bounded repair scope;
- sandbox verification before payment readiness.

---

## Benchmark

Only measured values generated from committed artifacts.

Example table structure:

| System | RTY | Intent Integrity | CVR | P95 Latency |
|---|---:|---:|---:|---:|
| Keyword | measured | measured | measured | measured |
| Semantic | measured | measured | measured | measured |
| LLM-only | measured | measured | measured | measured |
| CommerceTwin | measured | measured | measured | measured |

---

## Reproduce

Exact commands.

---

## Run Locally

Exact commands.

---

## Razorpay Test Mode

Explain setup.

---

## Security

Link actual test files.

---

## Limitations

Explicitly say:

- synthetic merchant catalog;
- test-mode transactions;
- no production revenue claims;
- limited supported causal interventions;
- limited model matrix if applicable.

---

# 28. Phase 27 — Judge Demo Script

Keep demo under five minutes.

---

## 0:00–0:30 — Problem

Say:

> AI shopping agents can find products, but transaction reliability breaks when merchant metadata, prices, inventory, or payment state changes. CommerceTwin tests those failures before they affect production.

---

## 0:30–1:00 — Architecture

Show:

```text
Buyer → State Machine → Chaos → Trace → Repair → Replay → Razorpay
```

Explain:

> The LLM never controls money. Deterministic code validates every hard constraint and the final payment amount.

---

## 1:00–1:45 — Run Failure

Inject:

```text
missing power_watts
```

Show:

```text
ABORTED
MISSING_MIN_ATTRIBUTE
```

---

## 1:45–2:30 — Localize + Value at Risk

Open trace.

Show exact evidence and affected cohort.

---

## 2:30–3:15 — Repair

Show generated bounded patch.

Show that production mutation is prohibited.

---

## 3:15–4:00 — Replay

Show before/after.

Example:

```text
Before: X/Y
After: A/B
Constraint violations: 0
```

Use real measured values.

---

## 4:00–4:45 — Razorpay Safety

Create one test-mode order.

Show:

```text
PAYMENT_PENDING
```

Then verify payment or demonstrate payment chaos reconciliation.

---

## 4:45–5:00 — Closing

Say:

> CommerceTwin does not ask AI agents to be perfectly reliable. It makes the merchant side measurable, repairable, and safe under agentic failure.

---

# 29. Phase 28 — Evidence Package

Create:

```text
evidence/
    architecture.png
    benchmark_summary.md
    benchmark_results.json
    security_matrix.md
    ci_screenshot.png
    demo_trace.json
    repair_before_after.json
    razorpay_test_receipt_sanitized.json
```

Every important application claim should have an evidence path.

---

# 30. Phase 29 — Final Application Claims

Use careful language.

Good:

```text
On our frozen synthetic held-out benchmark, CommerceTwin achieved X RTY versus Y for baseline Z while preserving Q intent integrity.
```

Good:

```text
All payments were executed exclusively in Razorpay Test Mode.
```

Good:

```text
Repairs were verified through deterministic sandbox replay before a transaction was allowed to reach READY_FOR_PAYMENT.
```

Avoid:

```text
We mathematically proved revenue growth.
```

Avoid:

```text
Guaranteed no duplicate payments.
```

Prefer:

```text
The system enforces idempotent logical payment operations and database-backed webhook deduplication under the tested failure scenarios.
```

Avoid:

```text
24/24 security attacks passed
```

unless all 24 are real executable tests.

---

# 31. Phase 30 — File-by-File Worklist

## Root

### `.env.example`

Add:

```text
DATABASE_URL
APP_ENV
APP_DEBUG
CORS_ORIGINS
LLM_PROVIDER
LLM_API_KEY
LLM_MODEL
RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET
RAZORPAY_WEBHOOK_SECRET
```

### `.gitignore`

Add:

```text
*.db
*.sqlite
*.sqlite3
.coverage
htmlcov/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.env.*
!.env.example
```

### `README.md`

Rewrite after metrics are real.

### `EVALUATION.md`

Rewrite with reproducible benchmark.

### `LIMITATIONS.md`

Keep, expand, ensure consistency.

### `THREAT_MODEL.md`

Update after persistent payment/idempotency changes.

### `RED_TEAM_REPORT.md`

Generate from real tests only.

### `RELEASE_CHECKLIST.md`

Keep every box unchecked until CI/evidence verifies it.

---

## Backend

### `backend/pyproject.toml`

Fix dependencies/dev extras/version.

### `backend/app/config.py`

Make single configuration source.

### `backend/app/main.py`

Fix CORS, health/readiness, router wiring.

### `backend/app/models.py`

Validate relationships, constraints, indexes.

### `backend/app/repositories.py`

Complete merchant-scoped repository operations.

### `backend/app/buyers/agent.py`

Refactor cart selection to avoid rediscovery.

### `backend/app/buyers/configurations.py`

Keep baselines but clearly label Jaccard as lexical baseline.

### `backend/app/buyers/llm_agent.py`

Fix attribute schema and model metadata.

### `backend/app/buyers/oracle.py`

Keep as deterministic authority; add edge-case tests.

### `backend/app/adapters/llm.py`

Add one real provider adapter.

### `backend/app/commerce/state.py`

Correct payment lifecycle.

### `backend/app/commerce/runner.py`

Separate prepayment readiness from payment completion.

### `backend/app/commerce/tracer.py`

Persist + hash chain.

### `backend/app/chaos/*`

Finish all deterministic chaos profiles.

### `backend/app/analytics/causal.py`

Implement missing-attribute counterfactual.

### `backend/app/analytics/leak_graph.py`

Rename/rework around AVaR.

### `backend/app/analytics/repair.py`

Split generator from guardrail validator.

### `backend/app/analytics/verifier.py`

Verify to `READY_FOR_PAYMENT`.

### `backend/app/analytics/metrics.py`

Keep and wire to persisted runs.

### `backend/app/payments/razorpay_client.py`

Keep test-mode protection and signature functions.

### `backend/app/payments/router.py`

Require verified trace, not arbitrary amount.

### `backend/app/payments/webhook_handler.py`

Move dedupe/state to database.

### `backend/app/api/routers.py`

Replace all mocked API responses.

---

## Evaluation

### `evals/run_benchmark.py`

Fix schemas and implement `commercetwin`.

### `backend/app/evals/benchmark.py`

Remove from submission path or convert to a real runner.

### New

```text
evals/metrics.py
evals/bootstrap.py
evals/report.py
```

Optional but recommended.

---

## Scripts

### `scripts/run_demo.py`

Rewrite to use real service.

### Add

```text
scripts/run_regression.py
scripts/init_db.py
scripts/generate_evidence.py
```

If `run_regression.py` is documented, it must exist.

---

## Frontend

### `frontend/src/api/client.ts`

No fake fallback.

### `frontend/src/context/AuthContext.tsx`

Fix type import; later remove fake auth if unnecessary.

### `frontend/src/pages/Overview.tsx`

Real metrics.

### `frontend/src/pages/RunExperiment.tsx`

Real run API.

### `frontend/src/pages/Experiments.tsx`

Real experiment history.

### `frontend/src/pages/Traces.tsx`

Real trace explorer.

### `frontend/src/pages/RevenueLeak.tsx`

Real AVaR/failure clusters.

### `frontend/src/pages/Repairs.tsx`

Real proposals + replay result.

### `frontend/src/pages/ChaosLab.tsx`

Real chaos controls.

### `frontend/src/pages/Payments.tsx`

Real payment operation timeline.

### `frontend/src/pages/Landing.tsx`

Fix documentation link and claim wording.

---

# 32. Final Real Red-Team Questions

Before release, answer all of these by demonstration:

1. What happens if the LLM invents a SKU?
2. What happens if the LLM proposes a price?
3. What happens if inventory changes after cart creation?
4. What happens if price changes after selection?
5. What happens if shipping becomes unavailable?
6. What happens if the client edits the payment amount?
7. What happens if Razorpay receives the order but your client loses the response?
8. What happens if the same webhook arrives twice?
9. What happens if the server restarts before the duplicate webhook arrives?
10. What happens if webhooks arrive out of order?
11. What happens if the webhook signature is invalid?
12. What happens if an AI-generated repair modifies buyer constraints?
13. What happens if a repair invents product metadata?
14. What happens if a repair helps one trace but harms another?
15. What happens if the database is down?
16. What happens if the LLM provider times out?
17. What happens if the frontend cannot reach the backend?
18. What happens if two payment requests are submitted simultaneously?
19. What happens if a trace belongs to another merchant?
20. Can every number in the dashboard be traced to raw stored evidence?

Submission-ready answer:

```text
There is a real automated test and/or visible deterministic demo for each relevant supported scenario.
```

---

# 33. Definition of Done

The project is complete only when this exact sequence works from a clean clone:

```bash
git clone https://github.com/bnssaanirudh/commercetwin
cd commercetwin
```

Backend:

```bash
cd backend
python -m venv .venv
# activate venv
pip install -e ".[dev]"
alembic upgrade head
cd ..
python scripts/seed_catalog.py
```

Run API:

```bash
cd backend
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm ci
npm run dev
```

Tests:

```bash
cd backend
pytest -q
```

Frontend build:

```bash
cd frontend
npm run build
```

Regression:

```bash
python scripts/run_regression.py
```

Hero demo:

```bash
python scripts/run_demo.py
```

And all of the following happen with real outputs:

```text
experiment created
buyer run executed
chaos injected
failure recorded
trace persisted
cause localized
value-at-risk computed
repair generated
repair guardrails checked
sandbox patch applied
cohort replayed
before/after metrics generated
verified trace reaches READY_FOR_PAYMENT
Razorpay Test Mode order created
payment remains pending until verified
webhook/signature processed
payment state completes correctly
duplicate event ignored persistently
```

---

# 34. Recommended Implementation Order

Use this exact order to avoid repeatedly breaking the project.

```text
01. Fix Python version
02. Fix dependencies
03. Fix frontend TS build
04. Fix CI
05. Delete stale/misleading docs
06. Remove fake frontend metrics
07. Remove fake run simulation
08. Fix ProductAttribute schema inconsistencies
09. Refactor buyer single-pass pipeline
10. Create central commerce service
11. Persist experiments and traces
12. Finish trace recorder
13. Finish chaos engine
14. Finish causal localizer
15. Replace revenue leak with AVaR
16. Build actual repair generator
17. Finish repair guardrails
18. Correct repair replay
19. Replace mock API endpoints
20. Fix payment state lifecycle
21. Derive amounts server-side
22. Persist payment operations
23. Persist webhook deduplication
24. Add concurrency/idempotency tests
25. Fix benchmark runner
26. Implement CommerceTwin benchmark system
27. Generate raw evaluation artifacts
28. Compute confidence intervals
29. Rebuild EVALUATION.md
30. Build Overview page
31. Build Experiment page
32. Build Trace Explorer
33. Build Repair/Replay page
34. Build Payment Safety page
35. Rewrite hero demo using real service
36. Replace fake red-team suite with executable tests
37. Add Docker
38. Deploy test-mode demo
39. Record demo video
40. Rewrite README using only verified evidence
41. Run final release checklist
42. Tag release
```

---

# 35. Final Submission Gate

Do not submit until:

```text
[ ] CI all green
[ ] clean clone works
[ ] no placeholders
[ ] no hardcoded metrics
[ ] no fake security passes
[ ] real held-out CommerceTwin results
[ ] real before/after replay
[ ] real Razorpay Test Mode order
[ ] correct payment state machine
[ ] persistent webhook idempotency
[ ] real trace explorer
[ ] real repair page
[ ] honest limitations
[ ] actual LICENSE
[ ] screenshots
[ ] 5-minute demo video
[ ] application text matches repository evidence exactly
```

---

# 36. Target End State

When finished, a reviewer should be able to:

1. clone the repository;
2. run the tests;
3. see green CI;
4. reproduce the benchmark;
5. run the application;
6. intentionally break a merchant twin;
7. watch an AI buyer fail;
8. inspect the transaction trace;
9. see the system localize the cause;
10. inspect a bounded repair;
11. replay the same failed cohort;
12. verify recovery without new constraint violations;
13. proceed to Razorpay Test Mode only after server-side validation;
14. simulate a payment network ambiguity;
15. observe persistent reconciliation/idempotency;
16. trace every displayed number back to raw evidence.

That is the version of CommerceTwin that should be submitted.
