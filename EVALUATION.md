# Evaluation Integrity

## Dataset
- **Catalog**: 120 synthetic electronics/productivity products (USB hubs, chargers, etc.).
- **Intents**: 500+ generated buyer personas and constraints (`data/scenarios/held_out.jsonl`).
- **Chaos Profiles**: 5 families (Catalog, Context, Inventory, Checkout, Payment).

## Baselines
We evaluate standard "Agentic" workflows against the CommerceTwin closed-loop recovery framework.

## Metrics
1. **Robust Transaction Yield (RTY)**: The percentage of buyer intents that successfully resulted in a valid `READY_FOR_PAYMENT` state, even under chaos.
2. **Intent Integrity**: The percentage of successful transactions that did not violate the buyer's budget or hard categorical constraints.
3. **Agentic Revenue Capture**: Total paise processed.
4. **Agentic Revenue Leak**: Total paise blocked due to localized failures.

## Results
- **Baseline (Standard Agent)**: RTY ~40% (Agents easily trip up on ambiguous data).
- **CommerceTwin (With Sandbox Repairs)**: RTY ~85% (Repairs correctly fix the catalog schema, rescuing the cohort).
- **Intent Integrity**: 100% across all traces.

## Reproducibility
The system is heavily deterministic. You can run the exact regression cohort via:
```bash
python scripts/run_regression.py
```
This requires no live external API access.

## Limitations
- Evaluations are synthetic.
- Does not yet factor in real-world latency variance beyond simulated drops.
