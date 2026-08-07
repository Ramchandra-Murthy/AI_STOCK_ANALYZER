from __future__ import annotations

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config.settings import settings
from backend.api.routers.system.health_router import router as system_router
from backend.api.routers.realtime_router import router as realtime_router
from backend.api.api_router import api_router
from backend.security.auth_router import auth_router
from backend.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

app = FastAPI(
    title="EROS 3.0 Institutional Autonomous Investment Intelligence Platform",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register All Enterprise Routers
app.include_router(system_router)
app.include_router(realtime_router)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root() -> dict:
    return {
        "platform": "EROS 3.0",
        "status": "OPERATIONAL",
        "architecture": "Cloud-Native Enterprise Platform (CNEP)"
    }