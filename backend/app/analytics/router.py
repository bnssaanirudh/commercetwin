from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.analytics.leak_graph import RevenueLeakCalculator

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.get("/failures")
def get_failure_localization(db: Session = Depends(get_db)):
    calculator = RevenueLeakCalculator(db)
    return calculator.calculate_leak_graph()
