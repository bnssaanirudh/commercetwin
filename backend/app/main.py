import uuid
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from app.payments.router import router as payments_router
from app.analytics.router import router as analytics_router
from app.api.routers import api_router

app = FastAPI(
    title="CommerceTwin API",
    description="Digital Twin and Chaos Lab for Agentic Commerce",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    req_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Store request_id in state
    request.state.request_id = req_id
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log exception safely here (don't leak stack trace to client)
    req_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "request_id": req_id}
    )

app.include_router(payments_router)
app.include_router(analytics_router)
app.include_router(api_router)

from sqlalchemy.orm import Session
from fastapi import Depends
from app.db import get_db

@app.get("/api/v1/health")
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint to ensure the skeleton boots and DB is responsive."""
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    return {
        "status": "ok",
        "env": settings.app_env,
        "debug": settings.app_debug,
        "database": db_status
    }

@app.get("/api/v1/ready")
@app.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness endpoint for load balancers."""
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database unavailable")
