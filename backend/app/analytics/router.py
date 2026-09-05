from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics.leak_graph import RevenueLeakCalculator
from app.db import get_db

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.get("/failures")
def get_failure_localization(db: Session = Depends(get_db)):
    calculator = RevenueLeakCalculator(db)
    return calculator.calculate_leak_graph()


@router.get("/revenue-leak")
def get_revenue_leak(db: Session = Depends(get_db)):
    """Alias for /failures — returns revenue leak cluster analysis."""
    from app.models import FailureCluster
    items = db.query(FailureCluster).all()
    return {
        "items": [
            {
                "failure_id": item.failure_id,
                "reason": item.reason_code,
                "stage": item.stage,
                "estimated_lost_value_paise": item.estimated_lost_value_paise,
                "trace_id": item.trace_id,
            }
            for item in items
        ],
        "total": len(items),
    }


@router.get("/metrics")
def get_analytics_metrics(db: Session = Depends(get_db)):
    """Alias for /api/v1/metrics — aggregate experiment metrics."""
    from app.services.commerce_service import CommerceService
    svc = CommerceService(db)
    return svc.get_aggregate_metrics()
