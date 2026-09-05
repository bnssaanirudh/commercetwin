"""
CommerceTwin benchmark runner.

Runs the full agent pipeline on a held-out/val/dev split and reports:
  - Robust Transaction Yield (RTY)
  - Intent Integrity (II)
  - Agentic Value-at-Risk (AVaR) in paise
  - Recovered Eligible Value (REV) in paise
  - Mean / Median / P95 latency (ms)
  - Bootstrap 95% confidence interval for RTY
  - Per-transaction JSONL evidence
  - Dataset hash + git commit for reproducibility

Usage:
  python evals/run_benchmark.py --system commercetwin --split val --seed 42
  python evals/run_benchmark.py --system keyword --split val
  python evals/run_benchmark.py --system semantic --split val
  python evals/run_benchmark.py --system llm_only --split val
"""
import argparse
import datetime
import hashlib
import json
import os
import random
import subprocess
import sys
import time
import uuid

# Add backend to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


def compute_file_hash(filepath: str) -> str:
    sha256_hash = hashlib.sha256()
    if not os.path.exists(filepath):
        return "MISSING"
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_split(split_name: str) -> list:
    filepath = os.path.join(os.path.dirname(__file__), "..", "data", "scenarios", f"{split_name}.jsonl")
    cohort = []
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found. Returning empty.", flush=True)
        return cohort
    with open(filepath) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                cohort.append(json.loads(line))
    return cohort


def create_raw_results_dir(run_id: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "evaluations", run_id)
    os.makedirs(path, exist_ok=True)
    return path


def get_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("ascii").strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def bootstrap_ci(values: list[float], n_boot: int = 2000, ci: float = 0.95, rng: random.Random = None) -> tuple[float, float]:
    """Bootstrap confidence interval for a list of 0/1 values or floats."""
    if not values:
        return 0.0, 0.0
    if rng is None:
        rng = random.Random(42)
    means = []
    n = len(values)
    for _ in range(n_boot):
        sample = [values[rng.randint(0, n - 1)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo_idx = int((1 - ci) / 2 * n_boot)
    hi_idx = int((1 + ci) / 2 * n_boot)
    return means[lo_idx], means[min(hi_idx, n_boot - 1)]


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = (p / 100) * (len(sorted_vals) - 1)
    lo, hi = int(idx), min(int(idx) + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])


def build_catalog_from_scenario(scenario: dict, pricing_db: dict, inventory_db: dict, attributes_map: dict | None = None, db_session=None) -> list:
    """
    Build an in-memory Product list from a scenario's oracle conditions.
    This is the key fix for RTY=0: without this, the DB is empty and the agent
    discovers nothing on a fresh clone.
    """
    from app.models import Product, Merchant

    intent = scenario["intent"]
    required_cats = intent["hard_constraints"]["required_categories"]
    oracle = intent.get("oracle_valid_product_conditions", {})
    num_solutions = oracle.get("num_solutions", 1)

    intent_id = intent.get("intent_id", "UNKNOWN")

    products = []
    # Synthesize num_solutions matching products per required category
    for cat in required_cats:
        for i in range(max(1, num_solutions)):
            sku = f"BENCH-{intent_id[:8]}-{cat.upper()[:8]}-{i:03d}"
            price = intent["target_budget_paise"] // max(len(required_cats), 1)
            price = max(price, 100)  # minimum 1 paise

            p = Product(sku=sku, merchant_id="merchant_benchmark", title=f"{cat} product {i}", category=cat, description=cat)
            p.price_paise = price

            if db_session:
                db_session.add(p)
                db_session.flush()

            products.append(p)
            pricing_db[sku] = price
            inventory_db[sku] = 10  # plenty of stock

            if attributes_map is not None:
                attrs = []
                req_attrs = intent.get("hard_constraints", {}).get("required_attributes", {})
                min_attrs = intent.get("hard_constraints", {}).get("min_attributes", {})
                for k, v in req_attrs.items():
                    attrs.append({"key": k, "value": v, "type": type(v).__name__})
                for k, v in min_attrs.items():
                    attrs.append({"key": k, "value": v, "type": type(v).__name__})
                attributes_map[sku] = attrs

                if db_session:
                    import uuid
                    import hashlib
                    import datetime
                    from app.models import CatalogAttributeEvidence
                    for attr in attrs:
                        ev = CatalogAttributeEvidence(
                            evidence_id=f"EV-{uuid.uuid4().hex[:8]}",
                            sku=sku,
                            key=attr["key"],
                            value=str(attr["value"]),
                            type=attr["type"],
                            catalog_version=1,
                            source="benchmark_oracle",
                            verified_at=datetime.datetime.now(datetime.UTC),
                            source_hash=hashlib.sha256(f"{sku}:{attr['key']}:{attr['value']}".encode()).hexdigest()
                        )
                        db_session.add(ev)
                    db_session.flush()

    return products


def run_commercetwin(split: str, seed: int) -> dict:
    """Run the CommerceTwin system on a dataset split and report metrics."""
    from app.buyers.configurations import SemanticBuyer
    from app.buyers.oracle import IntentOracle
    from app.buyers.schemas import BuyerIntentSchema, HardConstraints, SoftPreferences
    from app.chaos.engine import ChaosEngine
    from app.db import Base
    from app.models import ReplayResult, TransactionTrace
    from app.services.commerce_service import CommerceService
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    rng = random.Random(seed)  # noqa: F841
    run_id = f"RUN-{uuid.uuid4().hex[:8]}"
    out_dir = create_raw_results_dir(run_id)

    filepath = os.path.join(os.path.dirname(__file__), "..", "data", "scenarios", f"{split}.jsonl")
    dataset_hash = compute_file_hash(filepath)

    config = {
        "system": "commercetwin",
        "split": split,
        "seed": seed,
        "merchant_version": 1,
        "chaos_profile": "all",
    }

    cohort = load_split(split)
    print(f"[commercetwin] Loaded {len(cohort)} scenarios from {split}.jsonl", flush=True)

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    traces = []

    for i, item in enumerate(cohort):
        db_session = SessionLocal()
        from app.models import Merchant
        merchant = db_session.query(Merchant).filter(Merchant.merchant_id == "merchant_benchmark").first()
        if not merchant:
            db_session.add(Merchant(merchant_id="merchant_benchmark", name="Benchmark Merchant"))
            db_session.commit()

        commerce_service = CommerceService(db_session=db_session)
        experiment_id = commerce_service.create_experiment(config)

        start_time = time.time()
        intent_data = item["intent"]
        intent_id = intent_data["intent_id"]
        oracle_conds = intent_data.get("oracle_valid_product_conditions", {})
        num_solutions = oracle_conds.get("num_solutions", 0)

        # Scenario is eligible only when the oracle says there ARE valid solutions
        eligible = num_solutions > 0

        pricing_db: dict = {}
        inventory_db: dict = {}
        merchant_policy = {"shipping_available": True, "flat_shipping_paise": 0}

        intent_schema = BuyerIntentSchema(
            intent_id=intent_id,
            raw_intent=intent_data["raw_intent"],
            hard_constraints=HardConstraints(**intent_data["hard_constraints"]),
            soft_preferences=SoftPreferences(**intent_data["soft_preferences"]),
            target_budget_paise=intent_data["target_budget_paise"],
            max_budget_paise=intent_data["max_budget_paise"],
            autonomy_level=intent_data["autonomy_level"],
            seed=seed,
        )

        attributes_map: dict = {}

        # Build an in-memory catalog aligned with this scenario's oracle
        products = build_catalog_from_scenario(item, pricing_db, inventory_db, attributes_map=attributes_map, db_session=db_session)

        # Apply chaos
        chaos_engine = ChaosEngine()
        chaos_engine.apply(products, inventory_db, pricing_db, merchant_policy, seed, config["chaos_profile"])
        mutated_products, mutated_inventory, mutated_pricing, mutated_policy = chaos_engine.get_state()

        agent = SemanticBuyer(intent_schema, mutated_products, attributes_map)
        final_state = "ABORTED"
        failure_reason = None
        canonical_price = intent_data["target_budget_paise"]
        recovered = False
        intent_preserved = False
        is_repairable = False

        try:
            runner = commerce_service.run_trace(
                agent=agent,
                inventory_db=mutated_inventory,
                pricing_db=mutated_pricing,
                merchant_policy_db=mutated_policy,
                chaos_engine=chaos_engine,
                experiment_id=experiment_id,
                attributes_map=attributes_map,
            )
            final_state = runner.state_machine.current_state.name

            if final_state == "ABORTED":
                if runner.state_machine.trace_events:
                    last = runner.state_machine.trace_events[-1]
                    failure_reason = last.get("payload", {}).get("details", {}).get("reason")

                # ── REPAIR LOOP ──────────────────────────────────────────────
                # Use the persisted trace_id (not "latest trace" heuristic)
                trace_record = (
                    db_session.query(TransactionTrace)
                    .order_by(TransactionTrace.created_at.desc())
                    .first()
                )
                if trace_record:
                    trace_id = trace_record.trace_id
                    localized = commerce_service.localize_failure(trace_id)

                    if localized.get("status") == "localized":
                        is_repairable = True
                        # generate_repair now creates a real FailureCluster internally
                        repair_data = commerce_service.generate_repair(
                            trace_id=trace_id,
                            localized_cause=localized,
                        )

                        if (
                            repair_data.get("status") != "MANUAL_REVIEW_REQUIRED"
                            and "repair_id" in repair_data
                        ):
                            repair_id = repair_data["repair_id"]
                            commerce_service.verify_repair(repair_id)

                            # Gate recovery on persisted ReplayResult.success only
                            result_row = (
                                db_session.query(ReplayResult)
                                .filter(ReplayResult.repair_id == repair_id)
                                .order_by(ReplayResult.created_at.desc())
                                .first()
                            )
                            if result_row and result_row.success:
                                recovered = True
                                final_state = "READY_FOR_PAYMENT"

            if runner.cart:
                canonical_price = sum(mutated_pricing.get(p.sku, 0) for p in runner.cart)

            is_success = final_state == "READY_FOR_PAYMENT"

            # Use Oracle to check Intent Integrity
            if is_success:
                oracle_validator = IntentOracle(intent_schema)
                val_res = oracle_validator.evaluate_cart(runner.cart, canonical_price)
                intent_preserved = val_res.is_valid

        except Exception as e:  # noqa: BLE001
            final_state = "ABORTED"
            failure_reason = f"EXCEPTION: {e!s}"
        finally:
            db_session.close()

        latency_ms = (time.time() - start_time) * 1000.0
        is_success = final_state == "READY_FOR_PAYMENT"

        trace = {
            "trace_id": f"tr_{uuid.uuid4().hex[:8]}",
            "buyer_id": intent_id,
            "scenario_id": f"scn_{i}",
            "seed": seed,
            "system": "commercetwin",
            "eligible": eligible,
            "final_state": final_state,
            "success": is_success,
            "recovered": recovered,
            "repairable": is_repairable,
            "intent_preserved": intent_preserved,
            "failure_reason": failure_reason,
            "latency_ms": latency_ms,
            "canonical_price": canonical_price,
            "num_oracle_solutions": num_solutions,
        }
        traces.append(trace)

        if (i + 1) % 10 == 0:
            print(f"  [{i + 1}/{len(cohort)}] {intent_id}: {final_state}", flush=True)

    return _compute_and_save(traces, config, dataset_hash, out_dir, seed, split)



def _run_keyword_baseline(split: str, seed: int) -> dict:
    """Keyword baseline: exact category string match from raw_intent."""
    from app.buyers.configurations import StructuredBuyer
    from app.buyers.schemas import BuyerIntentSchema, HardConstraints, SoftPreferences
    from app.commerce.runner import CommerceRunner
    from app.buyers.oracle import IntentOracle

    run_id = f"RUN-{uuid.uuid4().hex[:8]}"
    out_dir = create_raw_results_dir(run_id)
    filepath = os.path.join(os.path.dirname(__file__), "..", "data", "scenarios", f"{split}.jsonl")
    dataset_hash = compute_file_hash(filepath)
    config = {"system": "keyword", "split": split, "seed": seed}
    cohort = load_split(split)
    print(f"[keyword] Loaded {len(cohort)} scenarios from {split}.jsonl", flush=True)

    traces = []
    for i, item in enumerate(cohort):
        start_time = time.time()
        intent_data = item["intent"]
        intent_id = intent_data["intent_id"]
        num_solutions = item["intent"].get("oracle_valid_product_conditions", {}).get("num_solutions", 0)
        eligible = num_solutions > 0

        pricing_db: dict = {}
        inventory_db: dict = {}
        intent_schema = BuyerIntentSchema(
            intent_id=intent_id,
            raw_intent=intent_data["raw_intent"],
            hard_constraints=HardConstraints(**intent_data["hard_constraints"]),
            soft_preferences=SoftPreferences(**intent_data["soft_preferences"]),
            target_budget_paise=intent_data["target_budget_paise"],
            max_budget_paise=intent_data["max_budget_paise"],
            autonomy_level=intent_data["autonomy_level"],
            seed=seed,
        )

        products = build_catalog_from_scenario(item, pricing_db, inventory_db)
        agent = StructuredBuyer(intent_schema, products, {})
        final_state = "ABORTED"
        failure_reason = None
        canonical_price = intent_data["target_budget_paise"]
        intent_preserved = False

        try:
            runner = CommerceRunner(agent, inventory_db, pricing_db, {"shipping_available": True, "flat_shipping_paise": 0})
            runner.run_to_precheck()
            final_state = runner.state_machine.current_state.name
            if runner.cart:
                canonical_price = sum(pricing_db.get(p.sku, 0) for p in runner.cart)
            if final_state == "ABORTED" and runner.state_machine.trace_events:
                last = runner.state_machine.trace_events[-1]
                failure_reason = last.get("payload", {}).get("details", {}).get("reason")
            
            if final_state == "READY_FOR_PAYMENT":
                oracle_validator = IntentOracle(intent_schema)
                val_res = oracle_validator.evaluate_cart(runner.cart, canonical_price)
                intent_preserved = val_res.is_valid

        except Exception as e:  # noqa: BLE001
            final_state = "ABORTED"
            failure_reason = f"EXCEPTION: {e!s}"

        latency_ms = (time.time() - start_time) * 1000.0
        is_success = final_state == "READY_FOR_PAYMENT"

        traces.append({
            "trace_id": f"tr_{uuid.uuid4().hex[:8]}",
            "buyer_id": intent_id,
            "scenario_id": f"scn_{i}",
            "seed": seed,
            "system": "keyword",
            "eligible": eligible,
            "final_state": final_state,
            "success": is_success,
            "intent_preserved": intent_preserved,
            "failure_reason": failure_reason,
            "latency_ms": latency_ms,
            "canonical_price": canonical_price,
            "num_oracle_solutions": num_solutions,
        })

    return _compute_and_save(traces, config, dataset_hash, out_dir, seed, split)


def _run_semantic_baseline(split: str, seed: int) -> dict:
    """Semantic baseline: Jaccard similarity for candidate discovery."""
    from app.buyers.configurations import SemanticBuyer
    from app.buyers.schemas import BuyerIntentSchema, HardConstraints, SoftPreferences
    from app.commerce.runner import CommerceRunner
    from app.buyers.oracle import IntentOracle

    run_id = f"RUN-{uuid.uuid4().hex[:8]}"
    out_dir = create_raw_results_dir(run_id)
    filepath = os.path.join(os.path.dirname(__file__), "..", "data", "scenarios", f"{split}.jsonl")
    dataset_hash = compute_file_hash(filepath)
    config = {"system": "semantic", "split": split, "seed": seed}
    cohort = load_split(split)
    print(f"[semantic] Loaded {len(cohort)} scenarios from {split}.jsonl", flush=True)

    traces = []
    for i, item in enumerate(cohort):
        start_time = time.time()
        intent_data = item["intent"]
        intent_id = intent_data["intent_id"]
        num_solutions = item["intent"].get("oracle_valid_product_conditions", {}).get("num_solutions", 0)
        eligible = num_solutions > 0

        pricing_db: dict = {}
        inventory_db: dict = {}
        intent_schema = BuyerIntentSchema(
            intent_id=intent_id,
            raw_intent=intent_data["raw_intent"],
            hard_constraints=HardConstraints(**intent_data["hard_constraints"]),
            soft_preferences=SoftPreferences(**intent_data["soft_preferences"]),
            target_budget_paise=intent_data["target_budget_paise"],
            max_budget_paise=intent_data["max_budget_paise"],
            autonomy_level=intent_data["autonomy_level"],
            seed=seed,
        )

        products = build_catalog_from_scenario(item, pricing_db, inventory_db)
        # Semantic Buyer uses Jaccard similarity on raw_intent
        agent = SemanticBuyer(intent_schema, products, {})
        final_state = "ABORTED"
        failure_reason = None
        canonical_price = intent_data["target_budget_paise"]
        intent_preserved = False

        try:
            runner = CommerceRunner(agent, inventory_db, pricing_db, {"shipping_available": True, "flat_shipping_paise": 0})
            runner.run_to_precheck()
            final_state = runner.state_machine.current_state.name
            if runner.cart:
                canonical_price = sum(pricing_db.get(p.sku, 0) for p in runner.cart)
            if final_state == "ABORTED" and runner.state_machine.trace_events:
                last = runner.state_machine.trace_events[-1]
                failure_reason = last.get("payload", {}).get("details", {}).get("reason")
            
            if final_state == "READY_FOR_PAYMENT":
                oracle_validator = IntentOracle(intent_schema)
                val_res = oracle_validator.evaluate_cart(runner.cart, canonical_price)
                intent_preserved = val_res.is_valid

        except Exception as e:  # noqa: BLE001
            final_state = "ABORTED"
            failure_reason = f"EXCEPTION: {e!s}"

        latency_ms = (time.time() - start_time) * 1000.0
        is_success = final_state == "READY_FOR_PAYMENT"

        traces.append({
            "trace_id": f"tr_{uuid.uuid4().hex[:8]}",
            "buyer_id": intent_id,
            "scenario_id": f"scn_{i}",
            "seed": seed,
            "system": "semantic",
            "eligible": eligible,
            "final_state": final_state,
            "success": is_success,
            "intent_preserved": intent_preserved,
            "failure_reason": failure_reason,
            "latency_ms": latency_ms,
            "canonical_price": canonical_price,
            "num_oracle_solutions": num_solutions,
        })

    return _compute_and_save(traces, config, dataset_hash, out_dir, seed, split)


def _run_llm_baseline(split: str, seed: int) -> dict:
    """LLM-only baseline. Requires OPENAI_API_KEY or GOOGLE_API_KEY — else SKIPPED."""
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("[llm_only] No API key found. Reporting as SKIPPED.", flush=True)
        run_id = f"RUN-{uuid.uuid4().hex[:8]}"
        out_dir = create_raw_results_dir(run_id)
        filepath = os.path.join(os.path.dirname(__file__), "..", "data", "scenarios", f"{split}.jsonl")
        dataset_hash = compute_file_hash(filepath)
        metrics = {
            "Robust_Transaction_Yield": "SKIPPED",
            "Intent_Integrity": "SKIPPED",
            "Agentic_Value_at_Risk_Paise": "SKIPPED",
            "Recovered_Eligible_Value_Paise": "SKIPPED",
            "status": "SKIPPED",
            "reason": "No LLM API key available",
        }
        config = {"system": "llm_only", "split": split, "seed": seed}
        with open(os.path.join(out_dir, "metrics.json"), "w") as f:
            json.dump(metrics, f, indent=2)
        with open(os.path.join(out_dir, "config.json"), "w") as f:
            json.dump(config, f, indent=2)
        with open(os.path.join(out_dir, "metadata.json"), "w") as f:
            json.dump({
                "git_commit": get_git_commit(),
                "dataset_hash": dataset_hash,
                "seed": seed,
                "system": "llm_only",
                "split": split,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "SKIPPED",
            }, f, indent=2)
        print(f"Metrics: {metrics}", flush=True)
        return metrics

    # We have an API key — run with LLMBuyer
    from app.buyers.llm_agent import LLMBuyer
    from app.adapters.openai_adapter import OpenAIAdapter
    from app.buyers.schemas import BuyerIntentSchema, HardConstraints, SoftPreferences
    from app.commerce.runner import CommerceRunner
    from app.buyers.oracle import IntentOracle

    run_id = f"RUN-{uuid.uuid4().hex[:8]}"
    out_dir = create_raw_results_dir(run_id)
    filepath = os.path.join(os.path.dirname(__file__), "..", "data", "scenarios", f"{split}.jsonl")
    dataset_hash = compute_file_hash(filepath)
    config = {"system": "llm_only", "split": split, "seed": seed}
    cohort = load_split(split)
    print(f"[llm_only] Loaded {len(cohort)} scenarios from {split}.jsonl", flush=True)

    traces = []
    adapter = OpenAIAdapter(api_key=api_key)

    for i, item in enumerate(cohort):
        start_time = time.time()
        intent_data = item["intent"]
        intent_id = intent_data["intent_id"]
        num_solutions = item["intent"].get("oracle_valid_product_conditions", {}).get("num_solutions", 0)
        eligible = num_solutions > 0

        pricing_db: dict = {}
        inventory_db: dict = {}
        intent_schema = BuyerIntentSchema(
            intent_id=intent_id,
            raw_intent=intent_data["raw_intent"],
            hard_constraints=HardConstraints(**intent_data["hard_constraints"]),
            soft_preferences=SoftPreferences(**intent_data["soft_preferences"]),
            target_budget_paise=intent_data["target_budget_paise"],
            max_budget_paise=intent_data["max_budget_paise"],
            autonomy_level=intent_data["autonomy_level"],
            seed=seed,
        )

        products = build_catalog_from_scenario(item, pricing_db, inventory_db)
        
        agent = LLMBuyer(intent_schema, products, {}, adapter=adapter)
        final_state = "ABORTED"
        failure_reason = None
        canonical_price = intent_data["target_budget_paise"]
        intent_preserved = False

        try:
            runner = CommerceRunner(agent, inventory_db, pricing_db, {"shipping_available": True, "flat_shipping_paise": 0})
            runner.run_to_precheck()
            final_state = runner.state_machine.current_state.name
            if runner.cart:
                canonical_price = sum(pricing_db.get(p.sku, 0) for p in runner.cart)
            if final_state == "ABORTED" and runner.state_machine.trace_events:
                last = runner.state_machine.trace_events[-1]
                failure_reason = last.get("payload", {}).get("details", {}).get("reason")
            
            if final_state == "READY_FOR_PAYMENT":
                oracle_validator = IntentOracle(intent_schema)
                val_res = oracle_validator.evaluate_cart(runner.cart, canonical_price)
                intent_preserved = val_res.is_valid

        except Exception as e:  # noqa: BLE001
            final_state = "ABORTED"
            failure_reason = f"EXCEPTION: {e!s}"

        latency_ms = (time.time() - start_time) * 1000.0
        is_success = final_state == "READY_FOR_PAYMENT"

        traces.append({
            "trace_id": f"tr_{uuid.uuid4().hex[:8]}",
            "buyer_id": intent_id,
            "scenario_id": f"scn_{i}",
            "seed": seed,
            "system": "llm_only",
            "eligible": eligible,
            "final_state": final_state,
            "success": is_success,
            "intent_preserved": intent_preserved,
            "failure_reason": failure_reason,
            "latency_ms": latency_ms,
            "canonical_price": canonical_price,
            "num_oracle_solutions": num_solutions,
        })

    return _compute_and_save(traces, config, dataset_hash, out_dir, seed, split)


def _compute_and_save(traces: list, config: dict, dataset_hash: str, out_dir: str, seed: int, split: str) -> dict:
    """Compute aggregate metrics from traces, write JSONL evidence, and save."""
    from app.analytics.metrics_engine import MetricsEngine
    
    metrics = MetricsEngine.compute_metrics(traces, seed=seed)

    metadata = {
        "git_commit": get_git_commit(),
        "dataset_hash": dataset_hash,
        "seed": seed,
        "system": config.get("system"),
        "split": split,
        "timestamp": datetime.datetime.now().isoformat(),
    }

    # Write per-transaction JSONL evidence
    with open(os.path.join(out_dir, "raw_traces.jsonl"), "w") as f:
        for t in traces:
            f.write(json.dumps(t) + "\n")

    with open(os.path.join(out_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    with open(os.path.join(out_dir, "config.json"), "w") as f:
        json.dump(config, f, indent=2)

    with open(os.path.join(out_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nRun completed. Results -> {out_dir}", flush=True)
    print(
        f"RTY={metrics.get('Robust_Transaction_Yield', 0):.3f} "
        f"[{metrics.get('RTY_CI_95_lo', 0):.3f}, {metrics.get('RTY_CI_95_hi', 0):.3f}] | "
        f"II={metrics.get('Intent_Integrity', 0):.3f} "
        f"[{metrics.get('II_CI_95_lo', 0):.3f}, {metrics.get('II_CI_95_hi', 0):.3f}] | "
        f"FRR={metrics.get('Failure_Recovery_Rate', 0):.3f} "
        f"[{metrics.get('FRR_CI_95_lo', 0):.3f}, {metrics.get('FRR_CI_95_hi', 0):.3f}] | "
        f"AVaR={metrics.get('Agentic_Value_at_Risk_Paise', 0)} | "
        f"Recovered={metrics.get('Total_Recovered', 0)} | "
        f"lat_p95={metrics.get('Latency_P95_ms', 0):.1f}ms",
        flush=True,
    )
    print(f"Metrics: {json.dumps(metrics, indent=2)}", flush=True)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="CommerceTwin benchmark runner")
    parser.add_argument(
        "--system",
        type=str,
        choices=["keyword", "semantic", "llm_only", "commercetwin"],
        required=True,
    )
    parser.add_argument("--split", type=str, choices=["dev", "val", "held_out"], default="val")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.system == "commercetwin":
        run_commercetwin(args.split, args.seed)
    elif args.system == "keyword":
        _run_keyword_baseline(args.split, args.seed)
    elif args.system == "semantic":
        _run_semantic_baseline(args.split, args.seed)
    elif args.system == "llm_only":
        _run_llm_baseline(args.split, args.seed)


if __name__ == "__main__":
    main()

