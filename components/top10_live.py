"""Fast live Top-10 market-mover scanner with one-minute refresh."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Lock
from time import perf_counter
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
import yfinance as yf

from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES

TOP10_REFRESH_SECONDS = 60
TOP10_CACHE_SECONDS = 50
TOP10_TIMEZONE = "Asia/Kolkata"
TOP10_CHUNK_SIZE = 10
TOP10_MAX_CANDIDATES_PER_EXCHANGE = 20
TOP10_MAX_CONSECUTIVE_FAILURES = 2
TOP10_SCAN_WARNING_SECONDS = 20
TOP10_STALE_DATA_SECONDS = 180
TOP10_MARKET_OPEN_HOUR = 9
TOP10_MARKET_OPEN_MINUTE = 15
TOP10_MARKET_CLOSE_HOUR = 15
TOP10_MARKET_CLOSE_MINUTE = 30
TOP10_SESSION_STATUS_KEY = "top10_market_status"
TOP10_PARTIAL_FAILURES_KEY = "top10_partial_failures"
TOP10_COVERAGE_KEY = "top10_quote_coverage"
TOP10_EXPECTED_QUOTES = 40
TOP10_GOOD_COVERAGE_QUOTES = 36
TOP10_REDUCED_COVERAGE_QUOTES = 20
_IST = ZoneInfo(TOP10_TIMEZONE)

_SCAN_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="top10-scan")
_SCAN_LOCK = Lock()
_SCAN_FUTURE: Future[tuple[pd.DataFrame, float, int, int]] | None = None
_SCAN_RESULT: tuple[pd.DataFrame, float, int, int] | None = None
_SCAN_FAILURES = 0


def _market_is_open(now: datetime) -> bool:
    """Return whether the NSE/BSE regular session is open in India."""
    if now.weekday() >= 5:
        return False
    market_open = now.replace(
        hour=TOP10_MARKET_OPEN_HOUR,
        minute=TOP10_MARKET_OPEN_MINUTE,
        second=0,
        microsecond=0,
    )
    market_close = now.replace(
        hour=TOP10_MARKET_CLOSE_HOUR,
        minute=TOP10_MARKET_CLOSE_MINUTE,
        second=0,
        microsecond=0,
    )
    return market_open <= now <= market_close


def _ticker(symbol: str, exchange: str) -> str:
    suffix = ".NS" if exchange == "NSE" else ".BO"
    cleaned = str(symbol).strip().upper()
    return cleaned if cleaned.endswith((".NS", ".BO")) else f"{cleaned}{suffix}"


def _extract_close(history: pd.DataFrame, ticker: str) -> pd.Series:
    """Extract one ticker's Close series from either yfinance layout."""
    if history is None or history.empty:
        return pd.Series(dtype="float64")

    if not isinstance(history.columns, pd.MultiIndex):
        if "Close" not in history.columns:
            return pd.Series(dtype="float64")
        return pd.to_numeric(history["Close"], errors="coerce").dropna()

    for level in range(history.columns.nlevels):
        values = history.columns.get_level_values(level)
        if ticker in values:
            frame = history.xs(ticker, axis=1, level=level)
            if "Close" in frame.columns:
                return pd.to_numeric(frame["Close"], errors="coerce").dropna()

    return pd.Series(dtype="float64")


def _format_candle_time(timestamp: object) -> str:
    """Format a provider candle timestamp in India time for the live table."""
    try:
        value = pd.Timestamp(timestamp)
        if value.tzinfo is None:
            value = value.tz_localize("UTC")
        return value.tz_convert(_IST).strftime("%Y-%m-%d %H:%M:%S IST")
    except (TypeError, ValueError):
        return str(timestamp)


def _coverage_status(valid_quotes: int) -> str:
    """Classify quote coverage without changing ranking or scan selection."""
    if valid_quotes >= TOP10_GOOD_COVERAGE_QUOTES:
        return "GOOD"
    if valid_quotes >= TOP10_REDUCED_COVERAGE_QUOTES:
        return "REDUCED"
    return "CRITICAL"


def _annotate_watchlist_changes(
    current: pd.DataFrame,
    previous: pd.DataFrame | None,
) -> tuple[pd.DataFrame, list[str]]:
    """Add one-minute watchlist membership/rank changes to the current Top-10."""
    if current.empty:
        return current.copy(), []

    annotated = current.copy()
    previous = previous if previous is not None else pd.DataFrame()
    previous_keys = (
        set(zip(previous["Exchange"], previous["Symbol"], strict=True))
        if {"Exchange", "Symbol"}.issubset(previous.columns)
        else set()
    )
    previous_ranks = (
        {(row["Exchange"], row["Symbol"]): int(row["Rank"]) for row in previous.to_dict("records")}
        if {"Exchange", "Symbol", "Rank"}.issubset(previous.columns)
        else {}
    )

    statuses: list[str] = []
    rank_changes: list[int | None] = []
    current_keys = set()

    for row in annotated.to_dict("records"):
        key = (row["Exchange"], row["Symbol"])
        current_keys.add(key)
        if key not in previous_keys:
            statuses.append("NEW")
            rank_changes.append(None)
            continue
        rank_change = previous_ranks[key] - int(row["Rank"])
        rank_changes.append(rank_change)
        statuses.append("UP" if rank_change > 0 else "DOWN" if rank_change < 0 else "UNCHANGED")

    annotated.insert(0, "Status", statuses)
    annotated.insert(
        1,
        "Rank change",
        pd.Series(rank_changes, index=annotated.index, dtype=object),
    )
    dropped = [f"{exchange}:{symbol}" for exchange, symbol in sorted(previous_keys - current_keys)]
    return annotated, dropped


def _scan_live_top10() -> tuple[pd.DataFrame, float, int, int]:
    """Scan a small curated candidate set with one-minute candles only."""
    started = perf_counter()
    failures = 0
    rows: list[dict[str, object]] = []

    candidates = [
        *(("NSE", symbol) for symbol in NSE_CANDIDATES[:TOP10_MAX_CANDIDATES_PER_EXCHANGE]),
        *(("BSE", symbol) for symbol in BSE_CANDIDATES[:TOP10_MAX_CANDIDATES_PER_EXCHANGE]),
    ]

    for exchange in ("NSE", "BSE"):
        symbols = [symbol for venue, symbol in candidates if venue == exchange]
        tickers = [_ticker(symbol, exchange) for symbol in symbols]

        for start in range(0, len(tickers), TOP10_CHUNK_SIZE):
            chunk = tickers[start : start + TOP10_CHUNK_SIZE]
            try:
                history = yf.download(
                    tickers=chunk,
                    period="5d",
                    interval="1m",
                    auto_adjust=False,
                    progress=False,
                    group_by="ticker",
                    threads=False,
                    timeout=15,
                )
            except Exception:
                failures += 1
                continue

            for ticker in chunk:
                close = _extract_close(history, ticker)
                if len(close) < 2:
                    continue

                latest = float(close.iloc[-1])
                previous = float(close.iloc[-2])
                if latest <= 0 or previous <= 0:
                    continue

                change_1m = (latest / previous - 1.0) * 100
                change_5m = (
                    (latest / float(close.iloc[-6]) - 1.0) * 100 if len(close) >= 6 else None
                )
                symbol = ticker.rsplit(".", 1)[0]

                rows.append(
                    {
                        "Rank": 0,
                        "Symbol": symbol,
                        "Exchange": exchange,
                        "Price": round(latest, 2),
                        "1-min %": round(change_1m, 2),
                        "5-min %": round(change_5m, 2) if change_5m is not None else None,
                        "Last candle": _format_candle_time(close.index[-1]),
                    }
                )

    frame = pd.DataFrame(rows)
    if frame.empty and failures:
        raise RuntimeError("Live quote provider failed for all scan chunks")
    if frame.empty:
        return frame, round(perf_counter() - started, 2), failures, 0

    valid_quotes = len(frame)
    frame = (
        frame.assign(_abs_change=frame["1-min %"].abs())
        .sort_values("_abs_change", ascending=False)
        .head(10)
        .drop(columns="_abs_change")
        .reset_index(drop=True)
    )
    frame["Rank"] = range(1, len(frame) + 1)
    return frame, round(perf_counter() - started, 2), failures, valid_quotes


@st.cache_data(ttl=TOP10_CACHE_SECONDS, show_spinner=False)
def _load_live_top10() -> tuple[pd.DataFrame, float, int, int]:
    """Cached fallback for the live Top-10 scan."""
    return _scan_live_top10()


def _start_background_scan() -> None:
    """Start one shared scan without blocking the Streamlit fragment."""
    global _SCAN_FUTURE
    with _SCAN_LOCK:
        if _SCAN_FUTURE is None or _SCAN_FUTURE.done():
            _SCAN_FUTURE = _SCAN_EXECUTOR.submit(_scan_live_top10)


def _consume_background_scan() -> tuple[pd.DataFrame, float, int, int] | None:
    """Return a completed background scan and keep the UI non-blocking."""
    global _SCAN_FUTURE, _SCAN_RESULT, _SCAN_FAILURES
    with _SCAN_LOCK:
        if _SCAN_FUTURE is not None and _SCAN_FUTURE.done():
            try:
                _SCAN_RESULT = _SCAN_FUTURE.result()
            except Exception:
                _SCAN_RESULT = None
                _SCAN_FAILURES += 1
            else:
                _SCAN_FAILURES = 0
            _SCAN_FUTURE = None
        return _SCAN_RESULT


@st.fragment(run_every=f"{TOP10_REFRESH_SECONDS}s")
def show_live_top10_scanner(*, period: str = "6mo", interval: str = "1d") -> None:
    """Render a live Top-10 scanner while refresh work runs in the background."""
    del period, interval

    st.subheader("🔴 Live Top-10 Market Scanner")
    st.caption(
        "Ranks the largest absolute 1-minute price moves from the configured "
        "NSE/BSE candidate universe. Data is provider-sourced and may be delayed."
    )

    if st.button("↻ Refresh Top-10 now", key="top10_manual_refresh"):
        _load_live_top10.clear()
        _start_background_scan()
        st.rerun(scope="fragment")

    background_result = _consume_background_scan()
    if background_result is not None:
        st.session_state["top10_live_result"] = background_result
        st.session_state["top10_live_completed_at"] = datetime.now(_IST)
        st.session_state[TOP10_PARTIAL_FAILURES_KEY] = background_result[2]
        st.session_state[TOP10_COVERAGE_KEY] = background_result[3]

    top10, scan_seconds, partial_failures, valid_quotes = st.session_state.get(
        "top10_live_result",
        (pd.DataFrame(), 0.0, 0, 0),
    )
    completed_at = st.session_state.get("top10_live_completed_at")
    scan_running = _SCAN_FUTURE is not None and not _SCAN_FUTURE.done()

    now = datetime.now(_IST)
    market_open = _market_is_open(now)

    refresh_due = market_open and (
        completed_at is None or now >= completed_at + timedelta(seconds=TOP10_REFRESH_SECONDS)
    )
    if not scan_running and refresh_due:
        _start_background_scan()
        scan_running = True
    next_refresh = (
        (completed_at + timedelta(seconds=TOP10_REFRESH_SECONDS))
        if completed_at is not None
        else now + timedelta(seconds=TOP10_REFRESH_SECONDS)
    )

    if not market_open:
        session_status = "MARKET_CLOSED"
        st.info("⚪ MARKET CLOSED · Live scanning resumes during the next regular NSE/BSE session.")
    elif scan_running:
        session_status = "REFRESHING"
        st.info("🟡 LIVE REFRESH · Updating the Top-10 in the background.")
    else:
        session_status = "READY"

    st.session_state[TOP10_SESSION_STATUS_KEY] = session_status

    if top10.empty:
        if _SCAN_FAILURES >= TOP10_MAX_CONSECUTIVE_FAILURES:
            st.error(
                "🔴 LIVE DATA UNAVAILABLE · The quote provider failed repeatedly. Retrying automatically."
            )
        else:
            st.info("🟡 REFRESHING · Fetching the first live Top-10 scan in the background…")
        return

    if _SCAN_FAILURES >= TOP10_MAX_CONSECUTIVE_FAILURES:
        st.warning(
            "🟠 PROVIDER ISSUE · Showing the last successful Top-10. Automatic retry is active."
        )
    elif partial_failures:
        st.warning(
            f"🟠 PARTIAL PROVIDER ISSUE · {partial_failures} quote chunk(s) failed. "
            "Displayed results may be incomplete; automatic retry is active."
        )

    data_age_seconds = (
        max(0.0, (now - completed_at).total_seconds()) if completed_at is not None else None
    )
    if scan_running:
        status = "🟡 REFRESHING · showing previous data"
    elif data_age_seconds is not None and data_age_seconds >= TOP10_STALE_DATA_SECONDS:
        status = "🔴 STALE DATA · latest completed data"
    elif completed_at is not None and scan_seconds >= TOP10_SCAN_WARNING_SECONDS:
        status = "🟠 SLOW SCAN · latest completed data"
    elif completed_at is not None:
        status = "🟢 FRESH · latest completed scan"
    else:
        status = "⚪ PREVIOUS DATA"

    last_update = completed_at.strftime("%H:%M:%S") if completed_at is not None else "—"
    coverage_status = _coverage_status(valid_quotes)
    previous_top10 = st.session_state.get("top10_live_previous_result")
    annotated_top10, dropped_symbols = _annotate_watchlist_changes(top10, previous_top10)
    st.session_state["top10_live_previous_result"] = top10.copy()
    st.caption(
        f"{status} · Last update {last_update} IST · "
        f"Next refresh {next_refresh:%H:%M:%S} IST · "
        f"Data age {data_age_seconds:.0f}s · Scan {scan_seconds:.1f}s · "
        f"Provider failures {partial_failures} · Quotes {valid_quotes}/{TOP10_EXPECTED_QUOTES} · "
        f"Coverage {coverage_status} · Refresh every 60s"
    )
    if dropped_symbols:
        st.caption(f"🔵 DROPPED SINCE LAST SCAN · {', '.join(dropped_symbols)}")

    if coverage_status == "CRITICAL":
        st.error(
            f"🔴 CRITICAL QUOTE COVERAGE · Only {valid_quotes}/{TOP10_EXPECTED_QUOTES} quotes are valid. "
            "Displayed Top-10 data may be materially incomplete; automatic retry is active."
        )
    elif coverage_status == "REDUCED":
        st.warning(
            f"🟠 REDUCED QUOTE COVERAGE · {valid_quotes}/{TOP10_EXPECTED_QUOTES} quotes are valid. "
            "Displayed results may be incomplete; automatic retry is active."
        )

    st.dataframe(
        annotated_top10,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Rank": st.column_config.NumberColumn("Rank", width="small"),
            "Rank change": st.column_config.NumberColumn("Rank change", width="small"),
            "Price": st.column_config.NumberColumn("Price", format="₹%.2f"),
            "1-min %": st.column_config.NumberColumn("1-min %", format="%.2f"),
            "5-min %": st.column_config.NumberColumn("5-min %", format="%.2f"),
        },
    )
