# Limitations

CommerceTwin is built as a robust Minimum Viable Product (MVP) for the Razorpay Buildathon. In the spirit of engineering honesty, the following are explicitly stated limitations:

1. **Synthetic Results**: All metrics, products, and intents are synthetic or run entirely in Razorpay Test Mode.
2. **No Proven Production Revenue Uplift**: The ~45% RTY improvement is theoretical and mathematically proven *within the bounds of the simulation*. It has not been deployed to live fractional traffic to prove a real-world revenue increase.
3. **Limited Merchant Vertical**: The dataset is strictly scoped to electronics and productivity accessories.
4. **Limited Buyer-Model Matrix**: The evaluation assumes our `SemanticBuyer` and `StructuredBuyer` configurations. It does not deeply evaluate latency or token costs for third-party foundation models.
5. **Restricted Failure Taxonomy**: The counterfactual diagnosis is supported only for implemented failure classes (e.g., `MISSING_TYPED_ATTRIBUTE`, `PRICE_MISMATCH`). Unknown failures are grouped as `UNKNOWN_ERROR`.
6. **No Claim of Universal Protocol Compliance**: We do not claim this implements a full universal agentic protocol, rather it proves the necessity of the *closed loop* (Trace -> Localize -> Repair -> Verify).
