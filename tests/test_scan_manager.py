"""Tests for the EROS FastAPI scan manager."""

from threading import Event
from unittest.mock import patch

import pandas as pd

from api.scan_manager import ErosScanManager


def test_background_price_jump_scan_completes() -> None:
    frame = pd.DataFrame({"Symbol": ["TEST"], "Change over 5m": [1.5]})
    frame.attrs["scan_stats"] = {"candidate_count": 1}

    manager = ErosScanManager(max_workers=1)
    with patch("api.scan_manager.scan_price_jumps", return_value=frame):
        job_id = manager.start_price_jump_scan(limit=1)

        for _ in range(50):
            job = manager.get_job(job_id)
            if job and job["status"] == "completed":
                break

        assert job is not None
        assert job["status"] == "completed"
        assert job["count"] == 1
        assert job["scan_stats"]["candidate_count"] == 1
        assert job["results"][0]["Symbol"] == "TEST"


def test_active_price_jump_scan_reuses_identical_parameters() -> None:
    frame = pd.DataFrame({"Symbol": ["TEST"]})
    started = Event()
    release = Event()

    def scan(**_kwargs: object) -> pd.DataFrame:
        started.set()
        release.wait(timeout=5)
        return frame

    manager = ErosScanManager(max_workers=1)
    with patch("api.scan_manager.scan_price_jumps", side_effect=scan):
        first_job_id = manager.start_price_jump_scan(
            exchange_category="NSE",
            lookback_minutes=5,
            jump_percent=1,
        )
        assert started.wait(timeout=2)

        second_job_id = manager.start_price_jump_scan(
            exchange_category="NSE",
            lookback_minutes=5,
            jump_percent=1,
        )

        assert second_job_id == first_job_id
        release.set()


def test_active_price_jump_scan_starts_for_different_parameters() -> None:
    frame = pd.DataFrame({"Symbol": ["TEST"]})
    started = Event()
    release = Event()

    def scan(**_kwargs: object) -> pd.DataFrame:
        started.set()
        release.wait(timeout=5)
        return frame

    manager = ErosScanManager(max_workers=1)
    with patch("api.scan_manager.scan_price_jumps", side_effect=scan):
        first_job_id = manager.start_price_jump_scan(
            exchange_category="NSE",
            lookback_minutes=5,
            jump_percent=1,
        )
        assert started.wait(timeout=2)

        second_job_id = manager.start_price_jump_scan(
            exchange_category="NSE",
            lookback_minutes=10,
            jump_percent=1,
        )

        assert second_job_id != first_job_id
        release.set()
