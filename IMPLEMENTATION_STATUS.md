# CommerceTwin Implementation Status

## 1. Required Capabilities Mapping

| Capability | Status | Notes |
| :--- | :--- | :--- |
| **Synthetic Merchant (Electronics)** | Missing | To be built |
| **Catalog (120-150 products)** | Missing | To be generated |
| **Buyer Agents (3 configs)** | Missing | To be built |
| **Normal Buyer Intent Scenarios** | Missing | To be generated |
| **Chaos/Adversarial Scenarios** | Missing | To be built |
| **Chaos Families (5 types)** | Missing | To be implemented |
| **Razorpay Test Mode Integration** | Missing | To be integrated |
| **Deterministic Transaction Trace** | Missing | To be implemented |
| **Agentic Revenue Leak Localization** | Missing | To be implemented |
| **Repair Types (3)** | Missing | To be implemented |
| **Counterfactual Replay** | Missing | To be implemented |
| **Before-vs-After Metrics** | Missing | To be implemented |
| **CI Test Command** | Missing | To be setup |
| **Clean Dashboard** | Missing | To be built |

## 2. Precise Ordered Implementation Plan

Based on the Playbook requirements, the following is the ordered plan:

1. **Prompt 01 — Architecture Contract and Scope Lock**: Define ARCHITECTURE.md, THREAT_MODEL.md, LIMITATIONS.md, `.env.example`, config layer, and typed interface protocols for ModelAdapter, MerchantTwinRepository, BuyerAgent, ChaosInjector, TraceRecorder, FailureLocalizer, RepairSynthesizer, PaymentAdapter. Boot skeleton.
2. **Prompt 02 — Database and Core Domain Models**: Set up database schemas, models, migrations, and repository layers for persistence. Ensure integer paise parsing and validations.
3. **Prompt 03 — Build the Synthetic Merchant and Catalog**: Generate the synthetic product catalog (PC and accessories) and configure the merchant twin.
4. **Prompt 04 — Build the Buyer Intents and Generation**: Define buyer personas, constraints, and valid SKU sets. Seed held-out intent datasets.
5. **Prompt 05 — The AI Buyer Agent and Runner**: Implement the AI agent loop, tool integration (cart, discovery), state machine, and trace recording.
6. **Prompt 06 — Payments and Razorpay Test Mode**: Implement server-side Razorpay order creation, webhook handling, deduplication, signature checking, and reconciliation states.
7. **Prompt 07 — Chaos Injector**: Implement the 5 chaos families for controlled perturbations before/during transactions.
8. **Prompt 08 — Evaluation and Metrics Engine**: Implement evaluation runner and metric aggregation (Robust Transaction Yield, Intent Integrity, Agentic Revenue Capture, Agentic Revenue Leak).
9. **Prompt 09 — The Diagnoser and Localizer**: Implement localization of failures and revenue leaks by analyzing traces against taxonomy.
10. **Prompt 10 — The Repair Synthesizer and Verifier**: Synthesize catalog/policy/schema repairs and verify them via counterfactual replay sandbox.
11. **Prompt 11 — The Frontend Dashboard**: Build a clean Next.js frontend to visualize the trace state, metrics, charts, and agent repairs.
