import logging
import time
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

import app.models
from app.analytics.router import router as analytics_router
from app.api.routers import api_router
from app.db import Base, engine, get_db
from app.payments.router import router as payments_router

from .config import settings

Base.metadata.create_all(bind=engine)

logger = logging.getLogger(__name__)

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
    logger.exception("Unhandled exception request_id=%s", req_id)
    origin = request.headers.get("origin", "")
    headers = {}
    if origin and (origin in settings.parsed_cors_origins or "*" in settings.parsed_cors_origins):
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "request_id": req_id},
        headers=headers,
    )


app.include_router(payments_router)
app.include_router(analytics_router)
app.include_router(api_router)


@app.get("/api/v1/health")
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check: process alive + DB connection verified."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except OSError as e:
        db_status = f"error: {e!s}"

    return {
        "status": "ok",
        "env": settings.app_env,
        "debug": settings.app_debug,
        "database": db_status,
    }


@app.get("/api/v1/ready")
@app.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness endpoint for load balancers — fails when DB is unreachable."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except OSError:
        raise HTTPException(status_code=503, detail="Database unavailable")
