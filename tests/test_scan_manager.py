"""Tests for the EROS FastAPI scan manager."""

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
