"""In-memory background scan manager for the EROS API."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Lock
from typing import Any
from uuid import uuid4

import pandas as pd

from api.scan_history import save_completed_scan
from scanner.price_jump import scan_price_jumps


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a DataFrame into JSON-safe records."""
    if frame is None or frame.empty:
        return []
    clean = frame.copy()
    clean = clean.astype(object).where(pd.notna(clean), None)
    return clean.to_dict(orient="records")


def _stats(frame: pd.DataFrame) -> dict[str, Any]:
    """Extract scanner diagnostics."""
    return dict(getattr(frame, "attrs", {}).get("scan_stats", {}))


class ErosScanManager:
    """Run EROS scans outside the HTTP request thread."""

    def __init__(self, max_workers: int = 2, max_jobs: int = 100) -> None:
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="eros-scan",
        )
        self._jobs: dict[str, dict[str, Any]] = {}
        self._max_jobs = max(1, max_jobs)
        self._lock = Lock()

    def start_price_jump_scan(self, **kwargs: Any) -> str:
        """Start a price-jump scan and return its job identifier."""
        job_id = uuid4().hex
        with self._lock:
            if len(self._jobs) >= self._max_jobs:
                oldest_job_id = next(iter(self._jobs))
                del self._jobs[oldest_job_id]
            self._jobs[job_id] = {
                "job_id": job_id,
                "status": "queued",
                "started_at": None,
                "finished_at": None,
                "count": 0,
                "results": [],
                "scan_stats": {},
                "error": None,
            }
        self._executor.submit(self._run_price_jump_scan, job_id, kwargs)
        return job_id

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Return a copy of a scan job, if it exists."""
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job is not None else None

    def _run_price_jump_scan(self, job_id: str, kwargs: dict[str, Any]) -> None:
        started = datetime.now(UTC).isoformat()
        with self._lock:
            self._jobs[job_id]["status"] = "running"
            self._jobs[job_id]["started_at"] = started
        try:
            frame = scan_price_jumps(**kwargs)
            with self._lock:
                self._jobs[job_id].update(
                    status="completed",
                    finished_at=datetime.now(UTC).isoformat(),
                    count=len(frame),
                    results=_records(frame),
                    scan_stats=_stats(frame),
                )
            save_completed_scan(
                job_id,
                self._jobs[job_id]["finished_at"],
                self._jobs[job_id]["results"],
                self._jobs[job_id]["scan_stats"],
            )
        except Exception as exc:
            with self._lock:
                self._jobs[job_id].update(
                    status="failed",
                    finished_at=datetime.now(UTC).isoformat(),
                    error=str(exc),
                )
