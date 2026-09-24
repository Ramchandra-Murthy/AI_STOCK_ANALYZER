"""FastAPI backend for EROS intraday market scanning.

This API is introduced alongside the existing Streamlit UI. The Streamlit
application remains the presentation layer until the new frontend is ready.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query

from scanner.market_scanner import market_scan
from scanner.price_jump import scan_price_jumps

from api.scan_manager import ErosScanManager
from scanner.unusual_activity import scan_unusual_activity

app = FastAPI(
    title="EROS Market API",
    version="1.0.0",
    description="Backend API for the EROS intraday NSE/BSE scanner.",
)

_SCAN_MANAGER = ErosScanManager(max_workers=2)


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a DataFrame to JSON-safe records."""
    if frame is None or frame.empty:
        return []
    clean = frame.copy()
    clean = clean.astype(object).where(pd.notna(clean), None)
    return clean.to_dict(orient="records")


def _stats(frame: pd.DataFrame) -> dict[str, Any]:
    """Return scanner diagnostics attached to a DataFrame."""
    return dict(getattr(frame, "attrs", {}).get("scan_stats", {}))


@app.get("/health")
def health() -> dict[str, str]:
    """Lightweight health check that never runs a market scan."""
    return {"status": "ok", "service": "eros-api"}


@app.get("/api/v1/intraday/price-jumps")
def price_jumps(
    limit: int = Query(20, ge=1, le=100),
    cap_category: str = Query("All caps"),
    exchange_category: str = Query("Both"),
    lookback_minutes: int = Query(5, ge=1, le=60),
    jump_percent: float = Query(1.0, ge=0.0, le=100.0),
) -> dict[str, Any]:
    """Return current EROS price-pulse candidates and scan diagnostics."""
    try:
        frame = scan_price_jumps(
            limit=limit,
            cap_category=cap_category,
            exchange_category=exchange_category,
            lookback_minutes=lookback_minutes,
            jump_percent=jump_percent,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Price-pulse scan failed: {exc}") from exc

    return {
        "count": len(frame),
        "results": _records(frame),
        "scan_stats": _stats(frame),
    }


@app.post("/api/v1/intraday/price-jumps/start")
def start_price_jumps(
    limit: int = Query(20, ge=1, le=100),
    cap_category: str = Query("All caps"),
    exchange_category: str = Query("Both"),
    lookback_minutes: int = Query(5, ge=1, le=60),
    jump_percent: float = Query(1.0, ge=0.0, le=100.0),
) -> dict[str, str]:
    """Start a non-blocking EROS price-jump scan."""
    job_id = _SCAN_MANAGER.start_price_jump_scan(
        limit=limit,
        cap_category=cap_category,
        exchange_category=exchange_category,
        lookback_minutes=lookback_minutes,
        jump_percent=jump_percent,
    )
    return {"job_id": job_id, "status": "queued"}


@app.get("/api/v1/intraday/price-jumps/jobs/{job_id}")
def price_jump_job(job_id: str) -> dict[str, Any]:
    """Return the state or completed result of a background scan."""
    job = _SCAN_MANAGER.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Scan job not found.")
    return job


@app.get("/api/v1/intraday/unusual-activity")
def unusual_activity(
    limit: int = Query(20, ge=1, le=100),
    cap_category: str = Query("All caps"),
    exchange_category: str = Query("Both"),
) -> dict[str, Any]:
    """Return current unusual price/volume activity."""
    try:
        frame = scan_unusual_activity(
            limit=limit,
            cap_category=cap_category,
            exchange_category=exchange_category,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Unusual-activity scan failed: {exc}") from exc

    return {
        "count": len(frame),
        "results": _records(frame),
        "scan_stats": _stats(frame),
    }


@app.get("/api/v1/scanner/market")
def market(
    limit: int = Query(10, ge=1, le=30),
) -> dict[str, Any]:
    """Return the existing broad-market scanner output."""
    try:
        frame = market_scan()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Market scan failed: {exc}") from exc

    return {
        "count": min(len(frame), limit),
        "results": _records(frame.head(limit)),
    }
