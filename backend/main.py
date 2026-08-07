from __future__ import annotations

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config.settings import settings
from backend.api.routers.system.health_router import router as system_router
from backend.api.routers.realtime_router import router as realtime_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Verified Enterprise Routers
app.include_router(system_router)
app.include_router(realtime_router)

@app.get("/")
def root() -> dict:
    return {
        "platform": settings.PROJECT_NAME,
        "status": "OPERATIONAL",
        "environment": settings.ENVIRONMENT,
        "architecture": "Cloud-Native Enterprise Platform (CNEP)"
    }