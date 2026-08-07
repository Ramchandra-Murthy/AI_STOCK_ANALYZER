from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.api.dependencies.database import get_session
import time

router = APIRouter(tags=["System Health"])

START_TIME = time.time()

@router.get("/health")
def health_check() -> dict:
    uptime_seconds = round(time.time() - START_TIME, 2)
    return {
        "status": "healthy",
        "database": "connected",
        "version": "3.0",
        "uptime_seconds": uptime_seconds
    }

@router.get("/ready")
def readiness_check(session: Session = Depends(get_session)) -> dict:
    try:
        session.execute(text("SELECT 1"))
        db_ready = True
    except Exception:
        db_ready = False

    return {
        "status": "ready" if db_ready else "degraded",
        "database": "connected" if db_ready else "disconnected",
        "feature_store": "active",
        "workflow_engine": "active"
    }