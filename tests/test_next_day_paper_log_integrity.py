"""Integrity regression tests for the next-day scanner paper log."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

from scanner.next_day_paper_log import (
    IST,
    RECORD_OUTCOME,
    RECORD_SHORTLIST,
    read_log,
    session_is_complete,
)


def test_paper_log_keeps_first_shortlist_and_outcome(tmp_path: Path) -> None:
    """Re-appending a key must not replace the original prediction or settled outcome."""
    path = tmp_path / "paper.jsonl"
    records = [
        {"record_type": RECORD_SHORTLIST, "key": "2026-11-04|NSE", "rank": 1},
        {"record_type": RECORD_SHORTLIST, "key": "2026-11-04|NSE", "rank": 99},
        {"record_type": RECORD_OUTCOME, "key": "2026-11-04|NSE", "return": 0.02},
        {"record_type": RECORD_OUTCOME, "key": "2026-11-04|NSE", "return": -0.50},
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")

    contents = read_log(path)

    assert contents.shortlists["2026-11-04|NSE"]["rank"] == 1
    assert contents.outcomes["2026-11-04|NSE"]["return"] == 0.02
    assert contents.corrupt_lines == 0


def test_paper_log_reports_corrupt_lines_without_hiding_valid_records(
    tmp_path: Path,
) -> None:
    path = tmp_path / "paper.jsonl"
    valid = {"record_type": RECORD_SHORTLIST, "key": "2026-11-04|NSE", "rank": 1}
    path.write_text(
        json.dumps(valid) + "\n" + "{not-json}\n" + json.dumps({"unexpected": True}) + "\n",
        encoding="utf-8",
    )

    contents = read_log(path)

    assert "2026-11-04|NSE" in contents.shortlists
    assert contents.corrupt_lines == 2


def test_session_is_not_complete_before_close_plus_settlement_buffer() -> None:
    target = date(2026, 11, 4)
    before_buffer = datetime(2026, 11, 4, 15, 29, tzinfo=IST)
    after_buffer = datetime(2026, 11, 4, 15, 31, tzinfo=IST)

    assert not session_is_complete(target, before_buffer)
    assert session_is_complete(target, after_buffer)


def test_session_completion_fails_closed_for_weekend() -> None:
    target = date(2026, 11, 7)  # Saturday
    after_close = datetime.combine(target, datetime.min.time(), IST) + timedelta(days=1)

    assert not session_is_complete(target, after_close)
