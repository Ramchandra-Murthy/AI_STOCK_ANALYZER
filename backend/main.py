from __future__ import annotations

import logging
from fastapi import FastAPI

from backend.api.routers.system.health_router import router as system_router
from backend.api.routers.realtime_router import router as realtime_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="EROS 3.0 Institutional Autonomous Investment Intelligence Platform",
    version="3.0.0",
)

# Register Enterprise Routers
app.include_router(system_router)
app.include_router(realtime_router)

@app.get("/")
def root() -> dict:
    return {
        "platform": "EROS 3.0",
        "status": "OPERATIONAL",
        "architecture": "Cloud-Native Enterprise Platform (CNEP)"
    }