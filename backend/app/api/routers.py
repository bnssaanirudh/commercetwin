from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db

api_router = APIRouter(prefix="/api/v1")


class PaginatedResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int
    page: int
    size: int


# --- Merchant Twin ---
@api_router.get("/merchants/{merchant_id}", tags=["merchant twin"])
def get_merchant(merchant_id: str, db: Session = Depends(get_db)):
    return {"merchant_id": merchant_id, "name": "ByteHub", "policy": {"shipping": True}}


# --- Catalog/Products ---
@api_router.get("/products", tags=["catalog"])
def list_products(page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    from app.models import Product
    skip = (page - 1) * size
    items = db.query(Product).offset(skip).limit(size).all()
    total = db.query(Product).count()
    return {"items": [item.__dict__ for item in items], "total": total, "page": page, "size": size}


@api_router.get("/products/{sku}", tags=["catalog"])
def get_product(sku: str, db: Session = Depends(get_db)):
    from app.models import Product
    item = db.query(Product).filter(Product.sku == sku).first()
    if not item:
        raise HTTPException(status_code=404, detail="Product not found")
    return item.__dict__


# --- Buyers ---
@api_router.get("/buyers", tags=["buyers"])
def list_buyers(page: int = 1, size: int = 50, db: Session = Depends(get_db)):
    return {"items": [], "total": 0, "page": page, "size": size}


# --- Experiments ---
@api_router.get("/experiments", tags=["experiments"])
def list_experiments(page: int = 1, size: int = 50, db: Session = Depends(get_db)):
    from app.models import Experiment
    skip = (page - 1) * size
    items = db.query(Experiment).offset(skip).limit(size).all()
    total = db.query(Experiment).count()
    return {
        "items": [{"id": item.experiment_id, "experiment_id": item.experiment_id} for item in items],
        "total": total,
        "page": page,
        "size": size,
    }


class CreateExperimentRequest(BaseModel):
    merchant_version: str = "v1"
    buyer_cohort_version: str = "v1"
    chaos_profile: str = "none"
    seed: int = 42


@api_router.post("/experiments", tags=["experiments"])
def create_experiment(req: CreateExperimentRequest, db: Session = Depends(get_db)):
    from app.services.commerce_service import CommerceService
    svc = CommerceService(db)
    exp_id = svc.create_experiment(req.model_dump())
    return {"experiment_id": exp_id}


class RunExperimentRequest(BaseModel):
    buyer_cohort_size: int = 10
    seed: int = 42


@api_router.post("/experiments/{experiment_id}/run", tags=["experiments"])
def run_experiment(experiment_id: str, req: RunExperimentRequest, db: Session = Depends(get_db)):
    """
    Synchronously run an experiment using CommerceService.
    Uses the SemanticBuyer with a minimal synthetic catalog per buyer.
    Returns run results with final state summary.
    """
    from app.buyers.configurations import SemanticBuyer
    from app.buyers.schemas import BuyerIntentSchema, HardConstraints, SoftPreferences
    from app.models import Experiment, Product
    from app.services.commerce_service import CommerceService

    exp = db.query(Experiment).filter(Experiment.experiment_id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    svc = CommerceService(db)
    results = []

    for i in range(req.buyer_cohort_size):
        intent_id = f"synthetic-{experiment_id}-{i}"
        intent = BuyerIntentSchema(
            intent_id=intent_id,
            raw_intent=f"I need a product for test buyer {i}",
            hard_constraints=HardConstraints(required_categories=["electronics"]),
            soft_preferences=SoftPreferences(),
            target_budget_paise=50000,
            max_budget_paise=50000,
            autonomy_level="autonomous",
            seed=req.seed + i,
        )
        p = Product(sku=f"SYNTH-{i}", title=f"Synthetic {i}", category="electronics", description="test")
        p.price_paise = 10000
        agent = SemanticBuyer(intent, [p], {})
        try:
            runner = svc.run_trace(
                agent=agent,
                inventory_db={f"SYNTH-{i}": 10},
                pricing_db={f"SYNTH-{i}": 10000},
                merchant_policy_db={"shipping_available": True, "flat_shipping_paise": 0},
                experiment_id=experiment_id,
            )
            results.append({
                "buyer_id": intent_id,
                "final_state": runner.state_machine.current_state.name,
            })
        except Exception as e:
            results.append({"buyer_id": intent_id, "final_state": "ERROR", "error": str(e)})

    successful = sum(1 for r in results if r["final_state"] == "READY_FOR_PAYMENT")
    return {
        "experiment_id": experiment_id,
        "status": "completed",
        "total_buyers": req.buyer_cohort_size,
        "successful": successful,
        "results": results,
    }


@api_router.get("/experiments/{experiment_id}", tags=["experiments"])
def get_experiment(experiment_id: str, db: Session = Depends(get_db)):
    from app.models import Experiment
    item = db.query(Experiment).filter(Experiment.experiment_id == experiment_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"experiment_id": item.experiment_id, "status": "completed"}


# --- Traces ---
@api_router.get("/traces", tags=["traces"])
def list_traces(page: int = 1, size: int = 50, db: Session = Depends(get_db)):
    from app.models import TransactionTrace
    skip = (page - 1) * size
    items = db.query(TransactionTrace).offset(skip).limit(size).all()
    total = db.query(TransactionTrace).count()
    return {
        "items": [{"trace_id": item.trace_id, "status": item.final_classification} for item in items],
        "total": total,
        "page": page,
        "size": size,
    }


@api_router.get("/traces/{trace_id}", tags=["traces"])
def get_trace(trace_id: str, db: Session = Depends(get_db)):
    from app.models import TraceEvent, TransactionTrace
    trace = db.query(TransactionTrace).filter(TransactionTrace.trace_id == trace_id).first()
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    events = (
        db.query(TraceEvent)
        .filter(TraceEvent.trace_id == trace_id)
        .order_by(TraceEvent.seq.asc())
        .all()
    )
    return {
        "trace_id": trace_id,
        "final_classification": trace.final_classification,
        "events": [
            {"source": e.source, "seq": e.seq, "event_type": e.event_type, "payload": e.payload}
            for e in events
        ],
    }


# --- Failures ---
@api_router.get("/failures", tags=["failures"])
def list_failures(page: int = 1, size: int = 50, db: Session = Depends(get_db)):
    from app.models import FailureCluster
    skip = (page - 1) * size
    items = db.query(FailureCluster).offset(skip).limit(size).all()
    total = db.query(FailureCluster).count()
    return {
        "items": [{"failure_id": item.failure_id, "reason": item.reason_code, "trace_id": item.trace_id} for item in items],
        "total": total,
        "page": page,
        "size": size,
    }


@api_router.get("/failures/{failure_id}", tags=["failures"])
def get_failure(failure_id: str, db: Session = Depends(get_db)):
    from app.models import FailureCluster
    item = db.query(FailureCluster).filter(FailureCluster.failure_id == failure_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Failure not found")
    return {"failure_id": item.failure_id, "reason": item.reason_code, "trace_id": item.trace_id, "status": "open"}


@api_router.post("/failures/{trace_id}/repairs", tags=["failures"])
def create_failure_repair(trace_id: str, db: Session = Depends(get_db)):
    from app.services.commerce_service import CommerceService
    svc = CommerceService(db)
    localized = svc.localize_failure(trace_id)
    res = svc.generate_repair(trace_id, localized_cause=localized)
    if res.get("status") == "MANUAL_REVIEW_REQUIRED":
        return {"repair_id": None, "status": "MANUAL_REVIEW_REQUIRED", "reason": res.get("reason")}
    return res


# --- Repairs ---
@api_router.get("/repairs", tags=["repairs"])
def list_repairs(page: int = 1, size: int = 50, db: Session = Depends(get_db)):
    from app.models import RepairProposal
    skip = (page - 1) * size
    items = db.query(RepairProposal).offset(skip).limit(size).all()
    total = db.query(RepairProposal).count()
    res_items = []
    for item in items:
        patch_blob = item.proposed_patch or {}
        inner_patch = patch_blob.get("patch", patch_blob)
        res_items.append({
            "repair_id": item.repair_id,
            "failure_id": item.failure_id,
            "snapshot_id": item.snapshot_id,
            "repair_type": item.repair_type,
            "status": item.status,
            "confidence": item.confidence,
            "target_sku": inner_patch.get("target_sku"),
            "operations": inner_patch.get("operations", []),
            "estimated_impact_paise": (patch_blob.get("estimated_impact_paise") or 0),
            "created_at": item.created_at.isoformat() if item.created_at else None,
        })
    return {"items": res_items, "total": total, "page": page, "size": size}


@api_router.get("/repairs/{repair_id}", tags=["repairs"])
def get_repair(repair_id: str, db: Session = Depends(get_db)):
    from app.models import RepairProposal
    item = db.query(RepairProposal).filter(RepairProposal.repair_id == repair_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Repair not found")
    return {"repair_id": item.repair_id, "status": item.status, "snapshot_id": item.snapshot_id}


@api_router.post("/repairs/{repair_id}/verify", tags=["repairs"])
def verify_repair(repair_id: str, db: Session = Depends(get_db)):
    from app.services.commerce_service import CommerceService
    svc = CommerceService(db)
    success = svc.verify_repair(repair_id)
    return {"repair_id": repair_id, "status": "VERIFIED" if success else "FAILED"}


# --- Payments ---
@api_router.get("/payments", tags=["payments"])
def list_payments(page: int = 1, size: int = 50, db: Session = Depends(get_db)):
    from app.models import PaymentOperation
    skip = (page - 1) * size
    items = db.query(PaymentOperation).offset(skip).limit(size).all()
    total = db.query(PaymentOperation).count()
    res_items = []
    for item in items:
        res_items.append({
            "operation_id": item.operation_id,
            "trace_id": item.trace_id,
            "amount_paise": item.amount_paise,
            "currency": item.currency,
            "state": item.state,
            "razorpay_order_id": item.razorpay_order_id,
            "razorpay_payment_id": item.razorpay_payment_id,
            "reconciled": item.state in ("captured", "authorized"),
            "created_at": item.created_at.isoformat() if item.created_at else None,
        })
    return {"items": res_items, "total": total, "page": page, "size": size}


# --- Replay ---
class CreateReplayRequest(BaseModel):
    repair_id: str


@api_router.post("/replays", tags=["replay"])
def create_replay(req: CreateReplayRequest, db: Session = Depends(get_db)):
    from app.models import ReplayResult
    from app.services.commerce_service import CommerceService
    svc = CommerceService(db)
    success = svc.verify_repair(req.repair_id)
    # Fetch the persisted ReplayResult
    result = (
        db.query(ReplayResult)
        .filter(ReplayResult.repair_id == req.repair_id)
        .order_by(ReplayResult.created_at.desc())
        .first()
    )
    replay_id = result.replay_id if result else f"REP-{req.repair_id[:8]}"
    return {
        "replay_id": replay_id,
        "repair_id": req.repair_id,
        "status": "completed" if success else "failed",
        "success": success,
    }


@api_router.get("/replays/{replay_id}", tags=["replay"])
def get_replay(replay_id: str, db: Session = Depends(get_db)):
    from app.models import ReplayResult
    item = db.query(ReplayResult).filter(ReplayResult.replay_id == replay_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Replay not found")
    return {
        "replay_id": item.replay_id,
        "repair_id": item.repair_id,
        "trace_id": item.trace_id,
        "snapshot_id": item.snapshot_id,
        "success": item.success,
        "before_state": item.before_state,
        "after_state": item.after_state,
        "status": "completed" if item.success else "failed",
    }


# --- Metrics ---
@api_router.get("/metrics", tags=["metrics"])
def get_metrics(db: Session = Depends(get_db)):
    from app.services.commerce_service import CommerceService
    svc = CommerceService(db)
    return svc.get_aggregate_metrics()
