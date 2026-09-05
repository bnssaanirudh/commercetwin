# Evaluation

This document outlines the evaluation methodology for the CommerceTwin architecture on the synthetic commerce benchmark.

## Dataset
- **Size**: 500 synthetic buyer intents paired with a simulated catalog.
- **Splits**: 
  - `dev.jsonl`: 300 intents
  - `val.jsonl`: 100 intents
  - `held_out.jsonl`: 100 intents
- **Split Policy**: The system is only tuned against the `val` split. `held_out` is frozen and strictly used for final reported metrics.

## Systems Tested
1. **Baseline A (Keyword)**: A deterministic keyword-matching heuristic agent.
2. **Baseline B (Semantic)**: An embedding-based vector search agent without strict rule evaluation.
3. **Baseline C (LLM-only)**: A standard LLM agent operating directly on the schema without safety constraints.
4. **CommerceTwin**: Our closed-loop architecture featuring deterministic oracles, trace logging, chaos injection, causal failure localization, and autonomous repair synthesis.

## Failure Profiles
The benchmark subjects the agent to the following chaos profiles:
- Inventory exhaustion after discovery
- Dynamic price hikes before checkout
- Missing typed attributes (catalog corruption)
- Merchant policy changes (shipping unvailability)

## Metrics
- **AVaR (Agentic Value at Risk)**: Sum of eligible transaction value blocked by failed traces attributable to the tested faults.
- **REV (Recovered Eligible Value)**: The actual transaction value saved when the repair successfully patches the failure.
- **RTY (Robust Transaction Yield)**: Percentage of intents that correctly completed the transaction.
- **Intent Integrity (II)**: Metric measuring alignment with the buyer's hard constraints.
- **CVR (Constraint Violation Rate)**: Rate at which hard constraints are broken.

## Raw Evidence Locations
Raw artifacts for every run are persisted locally:
- Configs, Traces, Failures, Repairs: `data/evaluations/<run_id>/`
- Metrics: `data/evaluations/<run_id>/metrics.json`

## Execution
To reproduce the evaluation results on the held-out split, run:
```bash
python evals/run_benchmark.py --system commercetwin --split held_out --seed 42
```

## Results Table

| System | RTY (95% CI) | II | CVR | FRR | AVaR | Latency (p95) |
|---|---|---|---|---|---|---|
| CommerceTwin | 0.930 [0.880, 0.980] | 0.914 | 0.086 | 0.000 | ₹38,716.88 | 89.01ms |

**Commit SHA:** `070d5a35437ea9138fe876d6c452f3d4b2615bfb`

## Limitations
- This is a synthetic benchmark and does not represent real-world live traffic.
- The models used are assumed to be static; upstream LLM provider API changes can drift these metrics.
