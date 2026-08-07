from __future__ import annotations

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.health import router as health_router
from backend.api.routers.valuation_router import router as valuation_router

from backend.api.routers.auth_router import router as auth_router

from backend.api.routers.task_router import router as task_router
from backend.api.exceptions.handlers import register_exception_handlers

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="EROS Enterprise Equity Research & Valuation Platform",
    version="3.0",
    description="Institutional-grade automated equity research, valuation, and portfolio optimization API."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health_router)
app.include_router(valuation_router)
app.include_router(auth_router)
app.include_router(task_router)