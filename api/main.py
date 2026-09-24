"""FastAPI backend for EROS intraday market scanning.

This API is introduced alongside the existing Streamlit UI. The Streamlit
application remains the presentation layer until the new frontend is ready.
"""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Query

from scanner.market_scanner import market_scan
from scanner.price_jump import scan_price_jumps
from scanner.unusual_activity import scan_unusual_activity

app = FastAPI(
    title="EROS Market API",
    version="1.0.0",
    description="Backend API for the EROS intraday NSE/BSE scanner.",
)

_SCAN_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="eros-scan")
_SCAN_JOBS: dict[str, dict[str, Any]] = {}
_SCAN_LOCK = Lock()


def _run_price_pulse_job(
    job_id: str,
    *,
    limit: int,
    cap_category: str,
    exchange_category: str,
    lookback_minutes: int,
    jump_percent: float,
) -> None:
    """Run a price-pulse scan outside the HTTP request thread."""
    try:
        frame = scan_price_jumps(
            limit=limit,
            cap_category=cap_category,
            exchange_category=exchange_category,
            lookback_minutes=lookback_minutes,
            jump_percent=jump_percent,
        )
        with _SCAN_LOCK:
            _SCAN_JOBS[job_id].update(
                status="completed",
                finished_at=datetime.now(timezone.utc).isoformat(),
                count=len(frame),
                results=_records(frame),
                scan_stats=_stats(frame),
            )
    except Exception as exc:
        with _SCAN_LOCK:
            _SCAN_JOBS[job_id].update(
                status="failed",
                finished_at=datetime.now(timezone.utc).isoformat(),
                error=str(exc),
            )


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


@app.post("/api/v1/intraday/price-jumps/start")
def start_price_pulse_scan(
    limit: int = Query(20, ge=1, le=100),
    cap_category: str = Query("All caps"),
    exchange_category: str = Query("Both"),
    lookback_minutes: int = Query(5, ge=1, le=60),
    jump_percent: float = Query(1.0, ge=0.0, le=100.0),
) -> dict[str, Any]:
    """Start a non-blocking EROS price-pulse scan."""
    import uuid

    job_id = uuid.uuid4().hex
    with _SCAN_LOCK:
        _SCAN_JOBS[job_id] = {
            "job_id": job_id,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "count": 0,
            "results": [],
        }
    _SCAN_EXECUTOR.submit(
        _run_price_pulse_job,
        job_id,
        limit=limit,
        cap_category=cap_category,
        exchange_category=exchange_category,
        lookback_minutes=lookback_minutes,
        jump_percent=jump_percent,
    )
    return {"job_id": job_id, "status": "running"}


@app.get("/api/v1/intraday/price-jumps/jobs/{job_id}")
def price_pulse_job(job_id: str) -> dict[str, Any]:
    """Return the current state/result of an asynchronous price-pulse scan."""
    with _SCAN_LOCK:
        job = _SCAN_JOBS.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Scan job not found.")
        return dict(job)


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
        future = _SCAN_EXECUTOR.submit(market_scan)
        frame = future.result()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Market scan failed: {exc}") from exc

    return {
        "count": min(len(frame), limit),
        "results": _records(frame.head(limit)),
    }
