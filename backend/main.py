from __future__ import annotations

from backend.security.dependencies import require_role
from backend.api.dependencies.auth import get_current_user
from backend.api.dependencies.database import get_session
from sqlalchemy.orm import Session

import logging
from fastapi import FastAPI, status, Depends
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config.settings import settings
from backend.api.routers.system.health_router import router as system_router
from backend.api.routers.realtime_router import router as realtime_router
from backend.api.routers.task_router import router as task_router
from backend.api.routers.auth_router import router as auth_router
from backend.api.routers.valuation_router import router as valuation_router
from backend.api.exceptions.handlers import register_exception_handlers
from backend.tasks.celery_app import celery_app
from backend.tasks.task_control import task_control

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="3.0.0",
)
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)

@app.get("/health", status_code=status.HTTP_200_OK)
def root_health():
    return {
        "status": "healthy",
        "version": "3.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/ready", status_code=status.HTTP_200_OK)
def root_ready():
    return {
        "status": "ready",
        "database": "connected",
        "redis": "connected"
    }

app.include_router(realtime_router)
app.include_router(task_router)
app.include_router(auth_router)
app.include_router(valuation_router)

@app.get("/api/v1/admin/queues", status_code=status.HTTP_200_OK, dependencies=[Depends(require_role("ADMIN"))])
def api_admin_queues():
    return task_control.get_queue_status()

@app.get("/api/v1/admin/tasks", status_code=status.HTTP_200_OK, dependencies=[Depends(require_role("ADMIN"))])
def api_admin_tasks():
    registered = task_control.get_registered_tasks()
    return {
        "tasks": registered,
        "total": len(registered),
        "status": "HEALTHY"
    }

from backend.api.routers.eros_production_router import (
    router as eros_production_router,
)
app.include_router(eros_production_router)
