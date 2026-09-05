# Limitations

CommerceTwin is built as an engineering prototype for agentic commerce reliability. In the spirit of rigorous engineering transparency, the following limitations are explicitly documented:

1. **Synthetic Evaluation**: All benchmark metrics, products, and intents are synthetic; the reported metrics do not demonstrate real-world revenue uplift.
2. **Evaluation Scope**: The 100-scenario benchmark measures checkout readiness up to `READY_FOR_PAYMENT`; it does not execute a Razorpay transaction for every benchmark scenario. Razorpay Test Mode is tested as a separate payment-integration pathway.
3. **No Automatic Recovery in Held-Out Benchmark**: The held-out benchmark produced **0 automatic recoveries** (FRR = 0.000, REV = ₹0). Recovery capability is instead demonstrated through a controlled deterministic regression scenario where authoritative same-SKU evidence is available.
4. **Bounded Failure Taxonomy & Repair Class**: Automatic repair currently supports a bounded set of failure classes (such as `MISSING_TYPED_ATTRIBUTE`) and requires authoritative same-SKU evidence. If trustworthy evidence is unavailable, the system safely falls back to manual review rather than hallucinating fixes.
5. **Razorpay Test Mode**: The payment integration operates against Razorpay Test Mode and serves as an engineering demonstration of server-authoritative gating and idempotency, not as a production payment-processing guarantee.
6. **Payment Reconciliation & Concurrency**: Production-grade ambiguous payment reconciliation (e.g. handling network timeouts during remote order capture), distributed concurrency handling, and live merchant system adapters remain future hardening.
