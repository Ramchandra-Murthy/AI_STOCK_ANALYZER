"""Tests for durable momentum ranking history and rank/score deltas."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from services.momentum_history import (
    MomentumHistoryError,
    compare_momentum_snapshots,
    load_momentum_history,
    record_momentum_snapshot,
)

IST = ZoneInfo("Asia/Kolkata")


def ranking(rows):
    return pd.DataFrame(
        rows,
        columns=[
            "Rank",
            "Symbol",
            "Exchange",
            "Momentum strength",
            "Direction",
            "Confirmation",
            "Volume ratio",
        ],
    )


def test_records_and_loads_snapshots_chronologically(tmp_path):
    database = tmp_path / "momentum.sqlite3"
    first = datetime(2026, 11, 9, 10, 0, tzinfo=IST)
    second = first + timedelta(minutes=1)

    first_id = record_momentum_snapshot(
        ranking([(1, "RELIANCE", "NSE", 72.5, "UP", "FULL", 1.8)]),
        first,
        database_path=database,
    )
    second_id = record_momentum_snapshot(
        ranking([(1, "TCS", "NSE", 80.0, "UP", "FULL", 2.1)]),
        second,
        database_path=database,
    )

    assert first_id is not None and second_id is not None and first_id != second_id
    history = load_momentum_history(database_path=database)
    assert history["Symbol"].tolist() == ["RELIANCE", "TCS"]
    assert history["Scan time"].tolist() == [first.isoformat(), second.isoformat()]


def test_same_timestamp_is_idempotent_and_updates_existing_symbol_rows(tmp_path):
    database = tmp_path / "momentum.sqlite3"
    captured = datetime(2026, 11, 9, 10, 0, tzinfo=IST)
    first_id = record_momentum_snapshot(
        ranking([(1, "RELIANCE", "NSE", 70.0, "UP", "FULL", 1.5)]),
        captured,
        database_path=database,
    )
    retry_id = record_momentum_snapshot(
        ranking([(1, "RELIANCE", "NSE", 75.0, "UP", "FULL", 1.7)]),
        captured,
        database_path=database,
    )

    history = load_momentum_history(database_path=database)
    assert retry_id == first_id
    assert len(history) == 1
    assert history.iloc[0]["Momentum strength"] == 75.0


def test_history_retention_is_bounded(tmp_path):
    database = tmp_path / "momentum.sqlite3"
    start = datetime(2026, 11, 9, 10, 0, tzinfo=IST)
    for offset in range(4):
        record_momentum_snapshot(
            ranking([(1, f"STOCK{offset}", "NSE", 50 + offset, "UP", "PARTIAL", None)]),
            start + timedelta(minutes=offset),
            database_path=database,
            max_snapshots=2,
        )

    history = load_momentum_history(database_path=database, limit=10)
    assert history["Symbol"].tolist() == ["STOCK2", "STOCK3"]


def test_empty_ranking_is_not_recorded(tmp_path):
    assert (
        record_momentum_snapshot(
            ranking([]),
            datetime(2026, 11, 9, 10, 0, tzinfo=IST),
            database_path=tmp_path / "momentum.sqlite3",
        )
        is None
    )


@pytest.mark.parametrize(
    "bad_rows",
    [
        [(0, "ABC", "NSE", 50.0, "UP", "FULL", 1.0)],
        [(1, "ABC", "NSE", float("nan"), "UP", "FULL", 1.0)],
        [(1, "ABC", "OTHER", 50.0, "UP", "FULL", 1.0)],
        [
            (1, "ABC", "NSE", 50.0, "UP", "FULL", 1.0),
            (2, "ABC", "NSE", 60.0, "UP", "FULL", 1.2),
        ],
    ],
)
def test_invalid_snapshot_is_rejected_without_partial_write(tmp_path, bad_rows):
    database = tmp_path / "momentum.sqlite3"
    with pytest.raises(MomentumHistoryError):
        record_momentum_snapshot(
            ranking(bad_rows),
            datetime(2026, 11, 9, 10, 0, tzinfo=IST),
            database_path=database,
        )
    assert load_momentum_history(database_path=database).empty


def test_comparison_identifies_rank_score_changes_and_dropped_symbols():
    previous = ranking(
        [
            (1, "RELIANCE", "NSE", 70.0, "UP", "FULL", 1.5),
            (2, "TCS", "NSE", 65.0, "UP", "PARTIAL", 1.2),
            (3, "INFY", "NSE", 60.0, "MIXED", "NONE", 1.0),
        ]
    )
    current = ranking(
        [
            (1, "TCS", "NSE", 75.0, "UP", "FULL", 1.8),
            (2, "RELIANCE", "NSE", 68.0, "UP", "FULL", 1.4),
            (3, "WIPRO", "BSE", 55.0, "DOWN", "PARTIAL", 1.1),
        ]
    )

    result = compare_momentum_snapshots(current, previous).set_index("Symbol")
    assert result.loc["TCS", "Status"] == "RANK UP"
    assert result.loc["TCS", "Rank change"] == 1
    assert result.loc["TCS", "Score change"] == 10.0
    assert result.loc["RELIANCE", "Status"] == "RANK DOWN"
    assert result.loc["WIPRO", "Status"] == "NEW"
    assert result.loc["INFY", "Status"] == "DROPPED"


def test_score_change_without_rank_change_reports_strengthening_or_weakening():
    previous = ranking([(1, "ABC", "NSE", 60.0, "UP", "FULL", 1.2)])
    current = ranking([(1, "ABC", "NSE", 65.0, "UP", "FULL", 1.4)])
    result = compare_momentum_snapshots(current, previous)
    assert result.iloc[0]["Status"] == "STRENGTHENING"
    assert result.iloc[0]["Score change"] == 5.0
