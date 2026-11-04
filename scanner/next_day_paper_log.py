"""Append-only paper-trading log for the next-business-day upside scanner.

Research and paper-trading evidence only. Nothing here talks to a broker, places or
simulates broker orders, or measures live-trading performance. The log answers one narrow
question honestly: *what did the scanner shortlist before a session, and what did a
simulated open-to-close holding of that shortlist do in the session that followed, net of
assumed costs, next to simple baselines?*

Design rules (each enforced and unit-tested):

* A shortlist is recorded only **before** its target session opens, and never overwritten,
  so a prediction cannot be edited or added with hindsight.
* An outcome is recorded only **after** the target session has completed (calendar close
  plus the settling buffer) and only from bars dated exactly on the target session.
  Missing, invalid or zero-volume bars become explicit ``missing`` outcomes, never zeros.
* If the provider fails or the target-session bars are not available yet, nothing is
  written and the session stays pending; stale data is never substituted.
* Outcomes use the same cost model as the walk-forward evaluation and always show gross
  and net-of-cost figures next to the equal-weight universe, 5-day-momentum and index
  baselines.
* Every record is labelled ``paper_simulation_not_live_trading``.
"""

from __future__ import annotations

import json
import math
import os
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from algorithmic_trading.trading_costs import IndiaEquityCostModel
from scanner.next_day_movers import (
    DATA_SOURCE,
    DISCLAIMER,
    FrameFetcher,
    ScanResult,
    clean_ohlcv_history,
    default_frame_fetcher,
)
from scanner.next_day_movers_eval import default_intraday_cost_model, round_trip_cost_fraction
from services.market_calendar import (
    IST,
    REGULAR_SESSION_CLOSE,
    REGULAR_SESSION_OPEN,
    CalendarUnavailableError,
    is_equity_trading_day,
)

SCHEMA_VERSION = 1
PAPER_LABEL = "paper_simulation_not_live_trading"
DEFAULT_LOG_PATH = Path("generated_reports/paper_trading/next_day_scanner_log.jsonl")
SETTLE_BUFFER_MINUTES = 15
MIN_SESSIONS_FOR_ANY_CONCLUSION = 120

PAPER_CAVEAT = (
    "Paper simulation only: hypothetical open-to-close holdings at the official open and close, "
    "with approximate costs. It is not live-trading performance, ignores fills, impact and "
    "circuit limits, and a short log is not evidence of a predictive edge "
    f"(the pre-registered rule needs at least {MIN_SESSIONS_FOR_ANY_CONCLUSION} evaluated days)."
)

RECORD_SHORTLIST = "shortlist"
RECORD_OUTCOME = "outcome"


@dataclass(frozen=True)
class RecordResult:
    """Result of an attempt to log a shortlist; ``recorded`` is False with a ``reason``."""

    recorded: bool
    reason: str
    key: str | None = None


@dataclass(frozen=True)
class SettleReport:
    """What a settlement pass did. Pending sessions are listed with the reason."""

    settled: tuple[str, ...] = ()
    pending: dict[str, str] = field(default_factory=dict)
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class LogContents:
    """Parsed log. ``corrupt_lines`` counts unreadable lines, which are never hidden."""

    shortlists: dict[str, dict[str, Any]]
    outcomes: dict[str, dict[str, Any]]
    corrupt_lines: int


@dataclass(frozen=True)
class PaperSummary:
    """Per-session table plus honest totals for display."""

    sessions: pd.DataFrame
    totals: dict[str, Any]
    caveat: str = PAPER_CAVEAT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _num(value: Any) -> float | None:
    """JSON-safe float: NaN/inf/None become ``None`` so a missing value is never a zero."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, 6) if math.isfinite(number) else None


def session_key(target: date, exchanges: Iterable[str]) -> str:
    """Stable identity of one logged shortlist: target session plus the exchange selection."""
    return f"{target.isoformat()}|{'+'.join(sorted(exchanges))}"


def target_session_open(target: date) -> datetime:
    """Regular-session open of the target date in IST."""
    return datetime.combine(target, REGULAR_SESSION_OPEN, IST)


def session_is_complete(target: date, now: datetime) -> bool:
    """True once the target session's close plus the settling buffer has passed.

    Fails closed: a date the calendar cannot vouch for (unsupported year, weekend or
    holiday) is never treated as a completed session.
    """
    current = now.replace(tzinfo=IST) if now.tzinfo is None else now.astimezone(IST)
    try:
        if not is_equity_trading_day(target):
            return False
    except CalendarUnavailableError:
        return False
    ready = datetime.combine(target, REGULAR_SESSION_CLOSE, IST) + timedelta(
        minutes=SETTLE_BUFFER_MINUTES
    )
    return current >= ready


def _append(path: Path, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True, allow_nan=False)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_log(path: Path | str = DEFAULT_LOG_PATH) -> LogContents:
    """Read the log; unreadable lines are counted, never silently skipped."""
    shortlists: dict[str, dict[str, Any]] = {}
    outcomes: dict[str, dict[str, Any]] = {}
    corrupt = 0
    file = Path(path)
    if not file.exists():
        return LogContents(shortlists, outcomes, corrupt)
    for raw in file.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
            kind = record["record_type"]
            key = record["key"]
        except (ValueError, KeyError, TypeError):
            corrupt += 1
            continue
        if kind == RECORD_SHORTLIST:
            shortlists.setdefault(key, record)  # first write wins; later duplicates ignored
        elif kind == RECORD_OUTCOME:
            outcomes.setdefault(key, record)
        else:
            corrupt += 1
    return LogContents(shortlists, outcomes, corrupt)


# ---------------------------------------------------------------------------
# Recording a shortlist (before the target session)
# ---------------------------------------------------------------------------


def record_shortlist(
    result: ScanResult,
    *,
    exchanges: Iterable[str],
    top_n: int,
    path: Path | str = DEFAULT_LOG_PATH,
    now: datetime | None = None,
) -> RecordResult:
    """Append the shortlist for ``result.target_business_date`` if it is still a prediction.

    Rejected (nothing written) when there is no ranking, when the target session has
    already opened, or when that session and exchange selection was already logged.
    """
    current = now or datetime.now(IST)
    current = current.replace(tzinfo=IST) if current.tzinfo is None else current.astimezone(IST)
    target = result.target_business_date
    cutoff = result.prediction_cutoff
    if result.status not in {"OK", "DEGRADED"} or not result.candidates:
        return RecordResult(False, "no_ranking_to_record")
    if target is None or cutoff is None:
        return RecordResult(False, "missing_cutoff_or_target")
    if cutoff.date() >= target:
        return RecordResult(False, "cutoff_not_before_target")
    if current >= target_session_open(target):
        return RecordResult(False, "target_session_already_started")

    exchange_tuple = tuple(sorted(exchanges))
    key = session_key(target, exchange_tuple)
    if key in read_log(path).shortlists:
        return RecordResult(False, "already_recorded", key)

    quality = result.data_quality
    record = {
        "schema_version": SCHEMA_VERSION,
        "record_type": RECORD_SHORTLIST,
        "label": PAPER_LABEL,
        "key": key,
        "recorded_at": current.isoformat(),
        "generated_at": result.generated_at.isoformat(),
        "prediction_cutoff": cutoff.isoformat(),
        "target_business_date": target.isoformat(),
        "exchanges": list(exchange_tuple),
        "top_n": top_n,
        "status": result.status,
        "score_type": result.score_type,
        "disclaimer": DISCLAIMER,
        "warnings": list(result.warnings),
        "provenance": {
            "data_source": DATA_SOURCE,
            "universe_requested": quality.get("universe_requested"),
            "eligible": quality.get("eligible"),
            "coverage_pct": quality.get("coverage_pct"),
            "excluded_count": quality.get("excluded_count"),
            "not_scored": list(result.unavailable_data),
        },
        "benchmarks": dict(result.benchmark_tickers),
        "eligible_tickers": list(result.eligible_tickers),
        "momentum5_tickers": list(result.momentum5_tickers),
        "candidates": [
            {
                "rank": c.rank,
                "symbol": c.symbol,
                "exchange": c.exchange,
                "ticker": c.ticker,
                "score": _num(c.score),
                "positive_score": _num(c.positive_score),
                "penalty": _num(c.penalty),
                "factor_coverage": _num(c.factor_coverage),
                "risk_flags": list(c.risk_flags),
                "supporting_factors": list(c.supporting_factors),
                "last_close": _num(c.last_close),
                "data_timestamp": c.data_timestamp.isoformat(),
                "data_source": c.data_source,
            }
            for c in result.candidates
        ],
    }
    _append(Path(path), record)
    return RecordResult(True, "recorded", key)


# ---------------------------------------------------------------------------
# Settling outcomes (after the target session)
# ---------------------------------------------------------------------------


def _session_bars(
    frames: Mapping[str, pd.DataFrame],
    tickers: Iterable[str],
    target: date,
    *,
    require_volume: bool = True,
) -> dict[str, dict[str, float]]:
    """Validated target-session ``{ticker: {"open", "close", "prev_close"}}``.

    Only a bar dated exactly on ``target`` with positive prices counts, and stocks also need
    positive volume (an index series legitimately reports none). ``prev_close`` is the latest
    earlier close (informational, for close-to-close).
    """
    bars: dict[str, dict[str, float]] = {}
    stamp = pd.Timestamp(target)
    for ticker in dict.fromkeys(tickers):
        clean, _, _ = clean_ohlcv_history(frames.get(ticker))
        if clean is None or stamp not in clean.index:
            continue
        row = clean.loc[stamp]
        if not (row["Open"] > 0 and row["Close"] > 0):
            continue
        if require_volume and not row["Volume"] > 0:
            continue
        earlier = clean.loc[clean.index < stamp, "Close"]
        bars[ticker] = {
            "open": float(row["Open"]),
            "close": float(row["Close"]),
            "prev_close": float(earlier.iloc[-1]) if len(earlier) else math.nan,
        }
    return bars


def _group_stats(
    tickers: Iterable[str], bars: Mapping[str, Mapping[str, float]], cost: float
) -> dict[str, Any]:
    names = list(dict.fromkeys(tickers))
    o2c = [bars[t]["close"] / bars[t]["open"] - 1.0 for t in names if t in bars]
    mean = sum(o2c) / len(o2c) if o2c else math.nan
    return {
        "n_requested": len(names),
        "n_valid": len(o2c),
        "n_missing": len(names) - len(o2c),
        "mean_o2c_gross": _num(mean),
        "mean_o2c_net": _num(mean - cost) if o2c else None,
        "share_positive_gross": _num(sum(1 for r in o2c if r > 0) / len(o2c)) if o2c else None,
    }


def build_outcome(
    shortlist: Mapping[str, Any],
    frames: Mapping[str, pd.DataFrame],
    cost_model: IndiaEquityCostModel,
    settled_at: datetime,
) -> dict[str, Any] | None:
    """Compute the outcome record, or ``None`` when no target-session bar exists yet."""
    target = date.fromisoformat(shortlist["target_business_date"])
    candidates = shortlist["candidates"]
    universe = shortlist.get("eligible_tickers", [])
    momentum = shortlist.get("momentum5_tickers", [])
    benchmarks: Mapping[str, str] = shortlist.get("benchmarks", {})
    wanted = [c["ticker"] for c in candidates] + list(universe) + list(momentum)
    bars = _session_bars(frames, wanted, target)
    index_bars = _session_bars(frames, benchmarks.values(), target, require_volume=False)
    stock_bars = [t for t in [*universe, *(c["ticker"] for c in candidates)] if t in bars]
    if not stock_bars:
        return None  # nothing for the target session yet: stay pending, do not fabricate

    cost = round_trip_cost_fraction(cost_model)
    picks = []
    for cand in candidates:
        bar = bars.get(cand["ticker"])
        if bar is None:
            picks.append({"ticker": cand["ticker"], "rank": cand["rank"], "status": "missing"})
            continue
        o2c = bar["close"] / bar["open"] - 1.0
        prev = bar["prev_close"]
        picks.append(
            {
                "ticker": cand["ticker"],
                "rank": cand["rank"],
                "status": "ok",
                "open": _num(bar["open"]),
                "close": _num(bar["close"]),
                "o2c_gross": _num(o2c),
                "o2c_net": _num(o2c - cost),
                "c2c_gross_not_tradable": _num(bar["close"] / prev - 1.0),
            }
        )
    index_o2c = {
        exchange: _num(index_bars[ticker]["close"] / index_bars[ticker]["open"] - 1.0)
        for exchange, ticker in benchmarks.items()
        if ticker in index_bars
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": RECORD_OUTCOME,
        "label": PAPER_LABEL,
        "key": shortlist["key"],
        "target_business_date": shortlist["target_business_date"],
        "settled_at": settled_at.isoformat(),
        "bars_source": DATA_SOURCE,
        "bars_dated": target.isoformat(),
        "assumptions": {
            "entry": "official target-session open",
            "exit": "official target-session close",
            "equal_weight": True,
            "round_trip_cost_and_slippage_bps": _num(cost * 1e4),
            "cost_model": asdict(cost_model),
            "caveat": PAPER_CAVEAT,
        },
        "score_top_n": _group_stats((c["ticker"] for c in candidates), bars, cost),
        "momentum5_top_n": _group_stats(momentum, bars, cost),
        "equal_weight_universe": _group_stats(universe, bars, cost),
        "index_o2c_gross": index_o2c,
        "picks": picks,
    }


def settle_outcomes(
    path: Path | str = DEFAULT_LOG_PATH,
    *,
    now: datetime | None = None,
    fetcher: FrameFetcher | None = None,
    cost_model: IndiaEquityCostModel | None = None,
) -> SettleReport:
    """Record outcomes for logged shortlists whose target session has completed.

    Sessions that are not complete, whose bars are unavailable, or whose fetch failed are
    left pending with a reason; nothing is written for them.
    """
    current = now or datetime.now(IST)
    current = current.replace(tzinfo=IST) if current.tzinfo is None else current.astimezone(IST)
    contents = read_log(path)
    pending: dict[str, str] = {}
    due: list[dict[str, Any]] = []
    for key, shortlist in contents.shortlists.items():
        if key in contents.outcomes:
            continue
        target = date.fromisoformat(shortlist["target_business_date"])
        if session_is_complete(target, current):
            due.append(shortlist)
        else:
            pending[key] = "target_session_not_complete"
    if not due:
        return SettleReport((), pending, ())

    wanted: list[str] = []
    for shortlist in due:
        wanted += [c["ticker"] for c in shortlist["candidates"]]
        wanted += list(shortlist.get("eligible_tickers", []))
        wanted += list(shortlist.get("momentum5_tickers", []))
        wanted += list(shortlist.get("benchmarks", {}).values())
    fetch = fetcher or default_frame_fetcher("1mo")
    try:
        frames, _ = fetch(list(dict.fromkeys(wanted)))
    except Exception as exc:  # provider boundary: report, leave pending, never fabricate
        message = f"{type(exc).__name__}: {exc}"
        for shortlist in due:
            pending[shortlist["key"]] = f"provider_failed: {message}"
        return SettleReport((), pending, (message,))

    cost = cost_model or default_intraday_cost_model()
    settled: list[str] = []
    for shortlist in due:
        outcome = build_outcome(shortlist, frames, cost, current)
        if outcome is None:
            pending[shortlist["key"]] = "target_session_bars_unavailable"
            continue
        _append(Path(path), outcome)
        settled.append(shortlist["key"])
    return SettleReport(tuple(settled), pending, ())


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def summarise_paper_log(path: Path | str = DEFAULT_LOG_PATH) -> PaperSummary:
    """Per-session paper results and honest totals (no performance or edge claims)."""
    contents = read_log(path)
    rows = []
    for key, outcome in sorted(contents.outcomes.items()):
        if key not in contents.shortlists:
            continue
        score, universe = outcome["score_top_n"], outcome["equal_weight_universe"]
        momentum = outcome["momentum5_top_n"]
        index_values = [v for v in outcome["index_o2c_gross"].values() if v is not None]
        index_o2c = index_values[0] if index_values else None
        net = score["mean_o2c_net"]
        rows.append(
            {
                "target_session": outcome["target_business_date"],
                "exchanges": "+".join(contents.shortlists[key]["exchanges"]),
                "picks_valid": f"{score['n_valid']}/{score['n_requested']}",
                "score_net_bps": None if net is None else net * 1e4,
                "score_gross_bps": _bps(score["mean_o2c_gross"]),
                "momentum5_net_bps": _bps(momentum["mean_o2c_net"]),
                "universe_gross_bps": _bps(universe["mean_o2c_gross"]),
                "index_gross_bps": _bps(index_o2c),
                "net_excess_vs_universe_bps": (
                    None
                    if net is None or universe["mean_o2c_gross"] is None
                    else (net - universe["mean_o2c_gross"]) * 1e4
                ),
            }
        )
    sessions = pd.DataFrame(rows)
    nets = sessions["score_net_bps"].dropna() if not sessions.empty else pd.Series(dtype=float)
    totals = {
        "shortlists_logged": len(contents.shortlists),
        "sessions_settled": len(contents.outcomes),
        "sessions_pending": len([k for k in contents.shortlists if k not in contents.outcomes]),
        "unreadable_lines": contents.corrupt_lines,
        "mean_score_net_bps": float(nets.mean()) if len(nets) else None,
        "min_sessions_for_any_conclusion": MIN_SESSIONS_FOR_ANY_CONCLUSION,
        "enough_sessions_for_conclusion": len(nets) >= MIN_SESSIONS_FOR_ANY_CONCLUSION,
    }
    return PaperSummary(sessions=sessions, totals=totals)


def _bps(value: float | None) -> float | None:
    return None if value is None else value * 1e4


__all__ = [
    "DEFAULT_LOG_PATH",
    "PAPER_CAVEAT",
    "PAPER_LABEL",
    "PaperSummary",
    "RecordResult",
    "SettleReport",
    "read_log",
    "record_shortlist",
    "session_is_complete",
    "session_key",
    "settle_outcomes",
    "summarise_paper_log",
    "target_session_open",
]
