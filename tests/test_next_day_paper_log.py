"""Tests for the append-only paper-trading log (research only; no broker, no live results)."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from algorithmic_trading.trading_costs import IndiaEquityCostModel
from scanner.next_day_movers import ScannerConfig, scan_next_day_movers
from scanner.next_day_movers_eval import default_intraday_cost_model, round_trip_cost_fraction
from scanner.next_day_paper_log import (
    MIN_SESSIONS_FOR_ANY_CONCLUSION,
    PAPER_CAVEAT,
    PAPER_LABEL,
    read_log,
    record_shortlist,
    session_is_complete,
    session_key,
    settle_outcomes,
    summarise_paper_log,
)
from scanner.universe import NSE_CANDIDATES

IST = ZoneInfo("Asia/Kolkata")
CUTOFF = date(2026, 11, 3)
TARGET = date(2026, 11, 4)  # Wednesday, regular session
SYMBOLS = NSE_CANDIDATES[:16]
SCAN_NOW = datetime(2026, 11, 3, 17, 30, tzinfo=IST)
BEFORE_OPEN = datetime(2026, 11, 3, 20, 0, tzinfo=IST)
AFTER_SETTLE = datetime(2026, 11, 4, 16, 0, tzinfo=IST)


def frame(seed: int, end: date, n: int = 220, price0: float = 500.0, vol0: float = 1e6):
    rng = np.random.default_rng(seed)
    index = pd.bdate_range(end=end, periods=n)
    close = price0 * np.exp(np.cumsum(rng.normal(0.0, 0.012, n)))
    open_ = np.r_[price0, close[:-1]] * (1 + rng.normal(0, 0.003, n))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.004, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.004, n)))
    volume = vol0 * np.exp(rng.normal(0, 0.3, n))
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=index
    )


def frames_through(end: date) -> dict[str, pd.DataFrame]:
    out = {f"{s}.NS": frame(i, end, price0=200.0 + 40 * i) for i, s in enumerate(SYMBOLS)}
    out["^NSEI"] = frame(900, end, price0=24000.0, vol0=0.0)
    return out


def extend(frames: dict[str, pd.DataFrame], *days: date) -> dict[str, pd.DataFrame]:
    """Append one plausible bar per later session to every frame (history is unchanged)."""
    out = {t: f.copy() for t, f in frames.items()}
    for day in days:
        for ticker, bars in out.items():
            last = bars.iloc[-1]
            new = pd.DataFrame(
                {
                    "Open": [last["Close"]],
                    "High": [last["Close"] * 1.01],
                    "Low": [last["Close"] * 0.99],
                    "Close": [last["Close"] * 1.002],
                    "Volume": [last["Volume"]],
                },
                index=pd.DatetimeIndex([pd.Timestamp(day)]),
            )
            out[ticker] = pd.concat([bars, new])
    return out


def set_bar(frames, ticker: str, day: date, open_: float, close: float, volume: float = 1e6):
    stamp = pd.Timestamp(day)
    lo, hi = min(open_, close) * 0.99, max(open_, close) * 1.01
    frames[ticker].loc[stamp, ["Open", "High", "Low", "Close", "Volume"]] = [
        open_,
        hi,
        lo,
        close,
        volume,
    ]


def fetcher_for(frames):
    calls = []

    def fetch(tickers):
        calls.append(list(tickers))
        usable = {t: frames[t] for t in tickers if t in frames}
        return usable, {"requested": len(tickers), "usable": len(usable)}

    fetch.calls = calls  # type: ignore[attr-defined]
    return fetch


def make_result(frames=None, now=SCAN_NOW, top_n=5):
    frames = frames or frames_through(CUTOFF)
    return scan_next_day_movers(
        ScannerConfig(exchanges=("NSE",), top_n=top_n, check_surveillance=False),
        now=now,
        universe=[(s, "NSE") for s in SYMBOLS],
        fetcher=fetcher_for(frames),
    )


@pytest.fixture
def log(tmp_path: Path) -> Path:
    return tmp_path / "paper" / "log.jsonl"


def lines(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


# ---------------------------------------------------------------- session completion


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (datetime(2026, 11, 4, 9, 14, tzinfo=IST), False),
        (datetime(2026, 11, 4, 15, 30, tzinfo=IST), False),
        (datetime(2026, 11, 4, 15, 44, 59, tzinfo=IST), False),
        (datetime(2026, 11, 4, 15, 45, tzinfo=IST), True),
        (datetime(2026, 11, 5, 9, 0, tzinfo=IST), True),
    ],
)
def test_a_session_is_complete_only_after_close_plus_buffer(now, expected) -> None:
    assert session_is_complete(TARGET, now) is expected


@pytest.mark.parametrize("target", [date(2026, 11, 7), date(2026, 11, 10), date(2027, 1, 5)])
def test_weekend_holiday_and_unconfigured_year_are_never_complete(target) -> None:
    assert session_is_complete(target, datetime(2030, 1, 1, tzinfo=IST)) is False


# ---------------------------------------------------------------- recording a shortlist


def test_shortlist_is_recorded_with_cutoff_target_scores_flags_and_provenance(log) -> None:
    result = make_result()
    outcome = record_shortlist(result, exchanges=("NSE",), top_n=5, path=log, now=BEFORE_OPEN)
    assert outcome.recorded and outcome.key == session_key(TARGET, ("NSE",))

    (record,) = lines(log)
    assert record["record_type"] == "shortlist" and record["label"] == PAPER_LABEL
    assert record["prediction_cutoff"] == "2026-11-03T15:30:00+05:30"
    assert record["target_business_date"] == "2026-11-04"
    assert record["status"] == result.status
    assert record["score_type"] == "ranking_score_0_100_not_a_probability"
    assert record["recorded_at"] < "2026-11-04T09:15"
    assert record["provenance"]["data_source"].startswith("Yahoo Finance")
    assert record["provenance"]["not_scored"]
    assert set(record["eligible_tickers"]) == {f"{s}.NS" for s in SYMBOLS}
    assert len(record["momentum5_tickers"]) == 5
    assert record["benchmarks"] == {"NSE": "^NSEI"}
    assert len(record["candidates"]) == 5
    first = record["candidates"][0]
    assert {"rank", "score", "risk_flags", "last_close", "data_timestamp", "data_source"} <= set(
        first
    )
    assert first["data_timestamp"] == "2026-11-03"
    assert "order" not in json.dumps(record).lower().replace("ordering", "")  # no broker concepts


def test_a_shortlist_cannot_be_recorded_once_the_target_session_has_started(log) -> None:
    result = make_result()
    late = datetime(2026, 11, 4, 9, 15, tzinfo=IST)
    rejected = record_shortlist(result, exchanges=("NSE",), top_n=5, path=log, now=late)
    assert not rejected.recorded and rejected.reason == "target_session_already_started"
    assert not log.exists()
    just_in_time = datetime(2026, 11, 4, 9, 14, 59, tzinfo=IST)
    assert record_shortlist(
        result, exchanges=("NSE",), top_n=5, path=log, now=just_in_time
    ).recorded


def test_a_shortlist_is_never_overwritten_or_duplicated(log) -> None:
    result = make_result()
    assert record_shortlist(result, exchanges=("NSE",), top_n=5, path=log, now=BEFORE_OPEN).recorded
    again = record_shortlist(result, exchanges=("NSE",), top_n=5, path=log, now=BEFORE_OPEN)
    assert not again.recorded and again.reason == "already_recorded"
    assert len(lines(log)) == 1
    # A different exchange selection is a separate prediction.
    other = record_shortlist(result, exchanges=("BSE",), top_n=5, path=log, now=BEFORE_OPEN)
    assert other.recorded and len(lines(log)) == 2


def test_no_ranking_means_nothing_is_recorded(log) -> None:
    unavailable = scan_next_day_movers(
        ScannerConfig(exchanges=("NSE",), check_surveillance=False),
        now=SCAN_NOW,
        universe=[(s, "NSE") for s in SYMBOLS],
        fetcher=lambda tickers: (_ for _ in ()).throw(TimeoutError("down")),
    )
    assert unavailable.status == "UNAVAILABLE"
    outcome = record_shortlist(unavailable, exchanges=("NSE",), top_n=5, path=log, now=BEFORE_OPEN)
    assert not outcome.recorded and outcome.reason == "no_ranking_to_record"
    assert not log.exists()


# ---------------------------------------------------------------- settling outcomes


def _logged(log, top_n=5):
    result = make_result(top_n=top_n)
    record_shortlist(result, exchanges=("NSE",), top_n=top_n, path=log, now=BEFORE_OPEN)
    return result


def test_outcomes_are_not_recorded_before_the_target_session_completes(log) -> None:
    _logged(log)
    fetch = fetcher_for(extend(frames_through(CUTOFF), TARGET))
    for now in (
        BEFORE_OPEN,
        datetime(2026, 11, 4, 12, 0, tzinfo=IST),
        datetime(2026, 11, 4, 15, 44, tzinfo=IST),
    ):
        report = settle_outcomes(log, now=now, fetcher=fetch)
        assert report.settled == ()
        assert report.pending == {session_key(TARGET, ("NSE",)): "target_session_not_complete"}
    assert fetch.calls == []  # not even fetched
    assert len(lines(log)) == 1


def test_missing_target_bars_keep_the_session_pending_and_write_nothing(log) -> None:
    _logged(log)
    report = settle_outcomes(log, now=AFTER_SETTLE, fetcher=fetcher_for(frames_through(CUTOFF)))
    assert report.settled == ()
    assert list(report.pending.values()) == ["target_session_bars_unavailable"]
    assert len(lines(log)) == 1


def test_provider_failure_keeps_the_session_pending_and_is_reported(log) -> None:
    _logged(log)

    def broken(_tickers):
        raise ConnectionError("provider down")

    report = settle_outcomes(log, now=AFTER_SETTLE, fetcher=broken)
    assert report.settled == () and "ConnectionError" in report.errors[0]
    assert list(report.pending.values())[0].startswith("provider_failed")
    assert len(lines(log)) == 1


def test_net_outcome_equals_gross_minus_costs_and_includes_baselines(log) -> None:
    result = _logged(log)
    frames = extend(frames_through(CUTOFF), TARGET)
    # Known target-session bars: every pick opens 100 and closes 101 (+1.00% gross).
    for cand in result.candidates:
        set_bar(frames, cand.ticker, TARGET, 100.0, 101.0)
    # Index +0.5%; every other universe name flat (so the universe mean is known).
    set_bar(frames, "^NSEI", TARGET, 24000.0, 24120.0, volume=0.0)
    for ticker in result.eligible_tickers:
        if ticker not in {c.ticker for c in result.candidates}:
            set_bar(frames, ticker, TARGET, 100.0, 100.0)

    report = settle_outcomes(log, now=AFTER_SETTLE, fetcher=fetcher_for(frames))
    assert report.settled == (session_key(TARGET, ("NSE",)),) and report.pending == {}
    outcome = lines(log)[-1]
    cost = round_trip_cost_fraction(default_intraday_cost_model())

    assert outcome["record_type"] == "outcome" and outcome["label"] == PAPER_LABEL
    assert outcome["bars_dated"] == "2026-11-04"
    score = outcome["score_top_n"]
    assert score["n_valid"] == 5 and score["n_missing"] == 0
    assert score["mean_o2c_gross"] == pytest.approx(0.01)
    assert score["mean_o2c_net"] == pytest.approx(0.01 - cost, abs=1e-6)
    assert outcome["assumptions"]["round_trip_cost_and_slippage_bps"] == pytest.approx(
        cost * 1e4, abs=1e-4
    )
    assert outcome["assumptions"]["cost_model"]["slippage_bps"] == 5.0
    assert "not live-trading performance" in outcome["assumptions"]["caveat"]
    assert outcome["index_o2c_gross"]["NSE"] == pytest.approx(0.005)
    universe = outcome["equal_weight_universe"]
    expected_universe = 5 * 0.01 / len(result.eligible_tickers)
    assert universe["mean_o2c_gross"] == pytest.approx(expected_universe, abs=1e-5)
    assert outcome["momentum5_top_n"]["n_requested"] == 5
    assert all(p["status"] == "ok" for p in outcome["picks"])
    assert all(
        p["o2c_net"] == pytest.approx(p["o2c_gross"] - cost, abs=1e-6) for p in outcome["picks"]
    )


def test_custom_cost_model_changes_the_net_outcome(log) -> None:
    result = _logged(log)
    frames = extend(frames_through(CUTOFF), TARGET)
    for cand in result.candidates:
        set_bar(frames, cand.ticker, TARGET, 100.0, 101.0)
    free = IndiaEquityCostModel()
    settle_outcomes(log, now=AFTER_SETTLE, fetcher=fetcher_for(frames), cost_model=free)
    score = lines(log)[-1]["score_top_n"]
    assert score["mean_o2c_net"] == pytest.approx(score["mean_o2c_gross"])


def test_a_missing_or_zero_volume_pick_is_reported_missing_not_zero(log) -> None:
    result = _logged(log)
    frames = extend(frames_through(CUTOFF), TARGET)
    picks = [c.ticker for c in result.candidates]
    for ticker in picks:
        set_bar(frames, ticker, TARGET, 100.0, 102.0)
    del frames[picks[0]]  # provider returns nothing for the first pick
    set_bar(frames, picks[1], TARGET, 100.0, 102.0, volume=0.0)  # suspended / no trade
    frames[picks[2]] = frames[picks[2]].drop(index=pd.Timestamp(TARGET))  # no bar that day

    settle_outcomes(log, now=AFTER_SETTLE, fetcher=fetcher_for(frames))
    outcome = lines(log)[-1]
    statuses = {p["ticker"]: p["status"] for p in outcome["picks"]}
    assert [statuses[t] for t in picks] == ["missing", "missing", "missing", "ok", "ok"]
    assert outcome["score_top_n"]["n_valid"] == 2 and outcome["score_top_n"]["n_missing"] == 3
    assert outcome["score_top_n"]["mean_o2c_gross"] == pytest.approx(0.02)
    assert all("o2c_gross" not in p for p in outcome["picks"] if p["status"] == "missing")


def test_only_bars_dated_on_the_target_session_are_used(log) -> None:
    result = _logged(log)
    frames = extend(frames_through(CUTOFF), TARGET, date(2026, 11, 5), date(2026, 11, 6))
    for cand in result.candidates:
        set_bar(frames, cand.ticker, TARGET, 100.0, 101.0)
        set_bar(frames, cand.ticker, date(2026, 11, 5), 100.0, 150.0)
    settle_outcomes(log, now=datetime(2026, 11, 6, 20, 0, tzinfo=IST), fetcher=fetcher_for(frames))
    assert lines(log)[-1]["score_top_n"]["mean_o2c_gross"] == pytest.approx(0.01)


def test_settlement_is_idempotent_and_never_edits_the_shortlist(log) -> None:
    _logged(log)
    before = lines(log)[0]
    frames = extend(frames_through(CUTOFF), TARGET)
    first = settle_outcomes(log, now=AFTER_SETTLE, fetcher=fetcher_for(frames))
    second = settle_outcomes(log, now=AFTER_SETTLE, fetcher=fetcher_for(frames))
    assert len(first.settled) == 1 and second.settled == () and second.pending == {}
    records = lines(log)
    assert [r["record_type"] for r in records] == ["shortlist", "outcome"]
    assert records[0] == before


def test_the_prediction_is_unaffected_by_later_bars_in_the_provider_data(log) -> None:
    # The provider already returns the target session when the scan runs; the cutoff drops it.
    frames = extend(frames_through(CUTOFF), TARGET)
    with_future = make_result(frames)
    clean = make_result(frames_through(CUTOFF))
    assert [(c.ticker, c.score) for c in with_future.candidates] == [
        (c.ticker, c.score) for c in clean.candidates
    ]


# ---------------------------------------------------------------- reading and summary


def test_unreadable_lines_are_counted_not_hidden(log) -> None:
    _logged(log)
    with log.open("a") as handle:
        handle.write("{not json\n")
        handle.write(json.dumps({"record_type": "mystery", "key": "x"}) + "\n")
    contents = read_log(log)
    assert contents.corrupt_lines == 2 and len(contents.shortlists) == 1
    assert summarise_paper_log(log).totals["unreadable_lines"] == 2


def test_summary_shows_costs_baselines_and_makes_no_edge_claim(log) -> None:
    result = _logged(log)
    frames = extend(frames_through(CUTOFF), TARGET)
    for cand in result.candidates:
        set_bar(frames, cand.ticker, TARGET, 100.0, 101.0)
    settle_outcomes(log, now=AFTER_SETTLE, fetcher=fetcher_for(frames))
    summary = summarise_paper_log(log)
    assert list(summary.sessions["target_session"]) == ["2026-11-04"]
    row = summary.sessions.iloc[0]
    assert row["picks_valid"] == "5/5"
    for column in (
        "score_net_bps",
        "score_gross_bps",
        "momentum5_net_bps",
        "universe_gross_bps",
        "index_gross_bps",
        "net_excess_vs_universe_bps",
    ):
        assert column in summary.sessions.columns
    assert row["score_net_bps"] < row["score_gross_bps"]
    totals = summary.totals
    assert totals["sessions_settled"] == 1 and totals["sessions_pending"] == 0
    assert totals["enough_sessions_for_conclusion"] is False
    assert totals["min_sessions_for_any_conclusion"] == MIN_SESSIONS_FOR_ANY_CONCLUSION
    assert summary.caveat == PAPER_CAVEAT and "not live-trading performance" in summary.caveat


def test_empty_or_missing_log_summarises_cleanly(tmp_path) -> None:
    summary = summarise_paper_log(tmp_path / "nothing.jsonl")
    assert summary.sessions.empty
    assert summary.totals["shortlists_logged"] == 0
    assert summary.totals["mean_score_net_bps"] is None
    assert settle_outcomes(tmp_path / "nothing.jsonl", now=AFTER_SETTLE).settled == ()
