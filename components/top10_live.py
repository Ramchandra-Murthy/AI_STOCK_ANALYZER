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
_IST = ZoneInfo(TOP10_TIMEZONE)

_SCAN_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="top10-scan")
_SCAN_LOCK = Lock()
_SCAN_FUTURE: Future[tuple[pd.DataFrame, float]] | None = None
_SCAN_RESULT: tuple[pd.DataFrame, float] | None = None
_SCAN_FAILURES = 0


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


def _scan_live_top10() -> tuple[pd.DataFrame, float]:
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
                        "Last candle": str(close.index[-1]),
                    }
                )

    frame = pd.DataFrame(rows)
    if frame.empty and failures:
        raise RuntimeError("Live quote provider failed for all scan chunks")
    if frame.empty:
        return frame, round(perf_counter() - started, 2)

    frame = (
        frame.assign(_abs_change=frame["1-min %"].abs())
        .sort_values("_abs_change", ascending=False)
        .head(10)
        .drop(columns="_abs_change")
        .reset_index(drop=True)
    )
    frame["Rank"] = range(1, len(frame) + 1)
    return frame, round(perf_counter() - started, 2)


@st.cache_data(ttl=TOP10_CACHE_SECONDS, show_spinner=False)
def _load_live_top10() -> tuple[pd.DataFrame, float]:
    """Cached fallback for the live Top-10 scan."""
    return _scan_live_top10()


def _start_background_scan() -> None:
    """Start one shared scan without blocking the Streamlit fragment."""
    global _SCAN_FUTURE
    with _SCAN_LOCK:
        if _SCAN_FUTURE is None or _SCAN_FUTURE.done():
            _SCAN_FUTURE = _SCAN_EXECUTOR.submit(_scan_live_top10)


def _consume_background_scan() -> tuple[pd.DataFrame, float] | None:
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
        with _SCAN_LOCK:
            global _SCAN_RESULT
            _SCAN_RESULT = None
        _start_background_scan()
        st.rerun(scope="fragment")

    background_result = _consume_background_scan()
    if background_result is not None:
        st.session_state["top10_live_result"] = background_result
        st.session_state["top10_live_completed_at"] = datetime.now(_IST)

    top10, scan_seconds = st.session_state.get(
        "top10_live_result",
        (pd.DataFrame(), 0.0),
    )
    completed_at = st.session_state.get("top10_live_completed_at")
    scan_running = _SCAN_FUTURE is not None and not _SCAN_FUTURE.done()

    if not scan_running and completed_at is None:
        _start_background_scan()
        scan_running = True

    now = datetime.now(_IST)
    next_refresh = (
        (completed_at + timedelta(seconds=TOP10_REFRESH_SECONDS))
        if completed_at is not None
        else now + timedelta(seconds=TOP10_REFRESH_SECONDS)
    )

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

    if scan_running:
        status = "🟡 REFRESHING · showing previous data"
    elif completed_at is not None:
        status = "🟢 FRESH · latest completed scan"
    else:
        status = "⚪ PREVIOUS DATA"

    last_update = completed_at.strftime("%H:%M:%S") if completed_at is not None else "—"
    st.caption(
        f"{status} · Last update {last_update} IST · "
        f"Next refresh {next_refresh:%H:%M:%S} IST · "
        f"Scan {scan_seconds:.1f}s · Refresh every 60s"
    )

    st.dataframe(
        top10,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", width="small"),
            "Price": st.column_config.NumberColumn("Price", format="₹%.2f"),
            "1-min %": st.column_config.NumberColumn("1-min %", format="%.2f"),
            "5-min %": st.column_config.NumberColumn("5-min %", format="%.2f"),
        },
    )
