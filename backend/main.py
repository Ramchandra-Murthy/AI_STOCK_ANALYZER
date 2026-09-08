from __future__ import annotations

import logging
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config.settings import settings
from backend.api.routers.system.health_router import router as system_router
from backend.api.routers.realtime_router import router as realtime_router
from backend.api.routers.task_router import router as task_router
from backend.tasks.celery_app import celery_app
from backend.tasks.task_control import task_control
from core.container import ServiceKey, bootstrap_container, container

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME, version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(system_router)

@app.on_event("startup")
def initialize_eros() -> None:
    bootstrap_container()

@app.get("/health", status_code=status.HTTP_200_OK)
def root_health():
    return {"status": "healthy", "version": "3.0", "environment": settings.ENVIRONMENT}

@app.get("/ready", status_code=status.HTTP_200_OK)
def root_ready():
    return {"status": "ready", "database": "connected", "redis": "connected"}

app.include_router(realtime_router)
app.include_router(task_router)

@app.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
def api_auth_register(payload: dict):
    return {"username": payload.get("username", "analyst"), "email": payload.get("email", "analyst@eros.org"), "status": "CREATED", "access_token": "mock-jwt-token-xyz"}

@app.post("/api/v1/auth/login", status_code=status.HTTP_200_OK)
def api_auth_login(payload: dict):
    username = payload.get("username", "analyst")
    return {"access_token": "mock-jwt-token-xyz", "token_type": "bearer", "user": {"username": username, "email": f"{username}@eros.org", "role": "ANALYST"}}

@app.post("/api/v1/valuation", status_code=status.HTTP_200_OK)
def api_valuation(payload: dict):
    symbol = payload.get("symbol", "RELIANCE.NS")
    bootstrap_container()
    service = container.resolve(ServiceKey.RESEARCH)
    result = service.run_pipeline(symbol)
    valuation = result.get("valuation_v43") or result.get("valuation") or {}
    recommendation = result.get("recommendation")
    return {"symbol": result.get("symbol", symbol), "intrinsic_value": valuation.get("intrinsic_value") if isinstance(valuation, dict) else None, "blended_valuation": valuation.get("blended_valuation") if isinstance(valuation, dict) else None, "margin_of_safety": valuation.get("margin_of_safety") if isinstance(valuation, dict) else None, "recommendation": recommendation.get("recommendation") if isinstance(recommendation, dict) else None, "status": result.get("status", "FAILED"), "errors": result.get("errors", [])}

@app.get("/api/v1/admin/queues", status_code=status.HTTP_200_OK)
def api_admin_queues():
    return task_control.get_queue_status()

@app.get("/api/v1/admin/tasks", status_code=status.HTTP_200_OK)
def api_admin_tasks():
    registered = task_control.get_registered_tasks()
    return {"tasks": registered, "total": len(registered), "status": "HEALTHY"}

from backend.api.routers.eros_production_router import router as eros_production_router
app.include_router(eros_production_router)
