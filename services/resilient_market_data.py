"""Resilient Yahoo Finance market-data retrieval helpers.

These helpers keep provider failures explicit. They retry transient failures,
fall back to per-symbol retrieval for missing tickers, and never fabricate data.
They are intended for research/paper-trading workflows; Yahoo Finance is not an
exchange-tick execution feed.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import BoundedSemaphore, RLock
from time import monotonic, perf_counter, sleep
from typing import Any

import pandas as pd
import yfinance as yf

DEFAULT_RETRIES = 2
DEFAULT_TIMEOUT = 12.0
RETRY_BACKOFF_SECONDS = 1.0
MAX_PROVIDER_REQUESTS_IN_FLIGHT = 4
MARKET_DATA_CACHE_MAX_ENTRIES = 2000
MARKET_DATA_CACHE_TTLS = {
    "1m": 20.0, "2m": 30.0, "5m": 45.0, "15m": 90.0,
    "30m": 120.0, "60m": 180.0, "90m": 180.0, "1h": 180.0,
    "1d": 900.0, "5d": 1800.0, "1wk": 3600.0, "1mo": 7200.0, "3mo": 7200.0,
}
_PROVIDER_REQUEST_LIMIT = BoundedSemaphore(MAX_PROVIDER_REQUESTS_IN_FLIGHT)
_CACHE_LOCK = RLock()
_MARKET_DATA_CACHE: OrderedDict[
    tuple[str, str, str, bool], tuple[float, pd.DataFrame]
] = OrderedDict()


def _cache_ttl(interval: str, override: float | None = None) -> float:
    """Return a conservative interval-aware cache lifetime."""
    if override is not None:
        return max(0.0, float(override))
    return MARKET_DATA_CACHE_TTLS.get(str(interval).lower(), 300.0)


def clear_market_data_cache() -> None:
    """Clear cached market frames; primarily useful for tests and explicit refreshes."""
    with _CACHE_LOCK:
        _MARKET_DATA_CACHE.clear()


def market_data_cache_stats() -> dict[str, int]:
    """Return a small, thread-safe cache diagnostic snapshot."""
    with _CACHE_LOCK:
        return {"entries": len(_MARKET_DATA_CACHE), "max_entries": MARKET_DATA_CACHE_MAX_ENTRIES}


def _cache_key(ticker: str, period: str, interval: str, auto_adjust: bool):
    return ticker, str(period), str(interval), bool(auto_adjust)


def _get_cached_frame(key, ttl: float) -> pd.DataFrame | None:
    if ttl <= 0:
        return None
    now = monotonic()
    with _CACHE_LOCK:
        entry = _MARKET_DATA_CACHE.get(key)
        if entry is None:
            return None
        stored_at, frame = entry
        if now - stored_at >= ttl:
            del _MARKET_DATA_CACHE[key]
            return None
        _MARKET_DATA_CACHE.move_to_end(key)
        return frame.copy(deep=True)


def _store_cached_frame(key, frame: pd.DataFrame) -> None:
    if frame is None or frame.empty:
        return
    with _CACHE_LOCK:
        _MARKET_DATA_CACHE[key] = (monotonic(), frame.copy(deep=True))
        _MARKET_DATA_CACHE.move_to_end(key)
        while len(_MARKET_DATA_CACHE) > MARKET_DATA_CACHE_MAX_ENTRIES:
            _MARKET_DATA_CACHE.popitem(last=False)


def _configure_yfinance() -> None:
    """Enable yfinance's built-in transient-network retry support when available."""
    try:
        yf.config.network.retries = max(
            int(getattr(yf.config.network, "retries", 0)),
            DEFAULT_RETRIES,
        )
    except (AttributeError, TypeError, ValueError):
        # Older yfinance versions may not expose the global config object.
        return


def _ticker_frame(history: pd.DataFrame | None, ticker: str) -> pd.DataFrame:
    """Extract one ticker from either supported yfinance column layout."""
    if history is None or history.empty:
        return pd.DataFrame()

    if not isinstance(history.columns, pd.MultiIndex):
        frame = history.copy()
    else:
        frame = pd.DataFrame()
        for level in range(history.columns.nlevels):
            if ticker in history.columns.get_level_values(level):
                frame = history.xs(ticker, axis=1, level=level).copy()
                break

    if frame.empty:
        return pd.DataFrame()

    frame = frame.loc[:, ~frame.columns.duplicated()].copy()
    if "Close" not in frame.columns:
        return pd.DataFrame()
    return frame.dropna(how="all").sort_index()


def _download_batch(
    tickers: list[str],
    *,
    period: str,
    interval: str,
    auto_adjust: bool,
    timeout: float,
    retries: int = DEFAULT_RETRIES,
    diagnostics: list[str] | None = None,
) -> pd.DataFrame:
    """Download one batch with bounded retries and no hidden synthetic data."""
    _configure_yfinance()
    last_error: Exception | None = None

    retry_count = max(0, int(retries))
    for attempt in range(retry_count + 1):
        try:
            with _PROVIDER_REQUEST_LIMIT:
                result = yf.download(
                    tickers=tickers,
                    period=period,
                    interval=interval,
                    auto_adjust=auto_adjust,
                    progress=False,
                    group_by="ticker",
                    threads=False,
                    timeout=timeout,
                    repair=True,
                )
            if result is not None and not result.empty:
                return result
        except Exception as exc:
            last_error = exc
            if diagnostics is not None:
                diagnostics.append(f"batch request raised {type(exc).__name__}")
        else:
            if diagnostics is not None and (result is None or result.empty):
                diagnostics.append("batch request returned no rows")

        if attempt < retry_count:
            sleep(RETRY_BACKOFF_SECONDS * (2**attempt))

    if last_error is not None:
        return pd.DataFrame()
    return pd.DataFrame()


def _download_single(
    ticker: str,
    *,
    period: str,
    interval: str,
    auto_adjust: bool,
    timeout: float,
    retries: int = DEFAULT_RETRIES,
    diagnostics: list[str] | None = None,
) -> pd.DataFrame:
    """Recover one missing ticker through the direct Ticker.history endpoint."""
    _configure_yfinance()
    retry_count = max(0, int(retries))
    for attempt in range(retry_count + 1):
        try:
            with _PROVIDER_REQUEST_LIMIT:
                result = yf.Ticker(ticker).history(
                    period=period,
                    interval=interval,
                    auto_adjust=auto_adjust,
                    timeout=timeout,
                    repair=True,
                    raise_errors=False,
                )
            frame = _ticker_frame(result, ticker)
            if not frame.empty:
                return frame
        except Exception as exc:
            if diagnostics is not None:
                diagnostics.append(f"single-symbol request raised {type(exc).__name__}")
        if attempt < retry_count:
            sleep(RETRY_BACKOFF_SECONDS * (2**attempt))
    return pd.DataFrame()


def download_symbols_individually(
    tickers: Iterable[str],
    *,
    period: str,
    interval: str,
    auto_adjust: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    max_symbols: int | None = None,
    diagnostics: list[str] | None = None,
) -> tuple[dict[str, pd.DataFrame], list[str]]:
    """Recover tickers one request at a time, with a hard cap on requests.

    Unlike ``download_symbol_frames(recover_missing=True)`` this does not issue a
    batch request first, so callers that already tried a batch do not repeat it.
    At most ``max_symbols`` tickers are attempted and each is tried
    ``retries + 1`` times; the remainder is reported as unresolved, never
    fabricated.
    """
    symbols = list(dict.fromkeys(str(t).strip().upper() for t in tickers if str(t).strip()))
    attempted = symbols if max_symbols is None else symbols[: max(0, int(max_symbols))]

    frames: dict[str, pd.DataFrame] = {}
    for ticker in attempted:
        frame = _download_single(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=auto_adjust,
            timeout=timeout,
            retries=retries,
            diagnostics=diagnostics,
        )
        if not frame.empty:
            frames[ticker] = frame

    return frames, [ticker for ticker in symbols if ticker not in frames]


def download_symbol_frames(
    tickers: Iterable[str],
    *,
    period: str,
    interval: str,
    auto_adjust: bool = False,
    batch_size: int = 10,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    recover_missing: bool = True,
    diagnostics: list[str] | None = None,
    max_workers: int = 3,
    cache_ttl_seconds: float | None = None,
) -> tuple[dict[str, pd.DataFrame], list[str]]:
    """Return usable frames, downloading batches with bounded concurrency.

    Concurrency is deliberately capped so scanner speed improves without
    creating an unbounded burst of requests against the quote provider.
    Results are reassembled in input order; unresolved symbols remain explicit.
    """
    symbols = list(dict.fromkeys(str(t).strip().upper() for t in tickers if str(t).strip()))
    if not symbols:
        return {}, []

    scan_started = perf_counter()
    recovery_seconds = 0.0
    recovery_count = 0
    batch_size = max(1, int(batch_size))
    worker_count = max(1, min(int(max_workers), MAX_PROVIDER_REQUESTS_IN_FLIGHT))
    ttl = _cache_ttl(interval, cache_ttl_seconds)
    frames: dict[str, pd.DataFrame] = {}
    cache_hits = 0
    for ticker in symbols:
        cached = _get_cached_frame(_cache_key(ticker, period, interval, auto_adjust), ttl)
        if cached is not None:
            frames[ticker] = cached
            cache_hits += 1

    uncached_symbols = [ticker for ticker in symbols if ticker not in frames]
    chunks = [
        uncached_symbols[start : start + batch_size]
        for start in range(0, len(uncached_symbols), batch_size)
    ]
    batch_seconds = 0.0

    def download_one(chunk: list[str]) -> tuple[list[str], pd.DataFrame, float]:
        started = perf_counter()
        history = _download_batch(
            chunk,
            period=period,
            interval=interval,
            auto_adjust=auto_adjust,
            timeout=timeout,
            retries=retries,
            diagnostics=diagnostics,
        )
        return chunk, history, perf_counter() - started

    # Keep only a small fixed number of provider requests in flight.
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(download_one, chunk) for chunk in chunks]
        completed: dict[int, tuple[list[str], pd.DataFrame]] = {}
        for future in as_completed(futures):
            chunk, history, elapsed = future.result()
            batch_seconds += elapsed
            completed[chunks.index(chunk)] = (chunk, history)

    for chunk_index in range(len(chunks)):
        chunk, history = completed[chunk_index]
        for ticker in chunk:
            frame = _ticker_frame(history, ticker)
            if not frame.empty:
                frames[ticker] = frame

    missing = [ticker for ticker in symbols if ticker not in frames]
    if recover_missing:
        for ticker in missing:
            recovery_started = perf_counter()
            frame = _download_single(
                ticker,
                period=period,
                interval=interval,
                auto_adjust=auto_adjust,
                timeout=timeout,
                retries=retries,
                diagnostics=diagnostics,
            )
            recovery_seconds += perf_counter() - recovery_started
            recovery_count += 1
            if not frame.empty:
                frames[ticker] = frame

    for ticker, frame in frames.items():
        _store_cached_frame(_cache_key(ticker, period, interval, auto_adjust), frame)

    if diagnostics is not None:
        diagnostics.append(
            "download summary: "
            f"requested={len(symbols)} usable={len(frames)} "
            f"missing={len(symbols) - len(frames)} batches={len(chunks)} "
            f"cache_hits={cache_hits} cache_ttl={ttl:.0f}s "
            f"batch_workers={worker_count} provider_request_limit={MAX_PROVIDER_REQUESTS_IN_FLIGHT} "
            f"single_recovery_attempts={recovery_count} "
            f"batch_seconds={batch_seconds:.2f} "
            f"recovery_seconds={recovery_seconds:.2f} "
            f"total_seconds={perf_counter() - scan_started:.2f}"
        )

    return frames, [ticker for ticker in symbols if ticker not in frames]


def download_market_frames(
    tickers: Iterable[str],
    *,
    period: str,
    interval: str,
    auto_adjust: bool = False,
    batch_size: int = 10,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    recover_missing: bool = True,
    cache_ttl_seconds: float | None = None,
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    """Download frames with diagnostics suitable for scanner health reporting."""

    symbols = list(dict.fromkeys(str(t).strip().upper() for t in tickers if str(t).strip()))
    diagnostics: list[str] = []
    frames, missing = download_symbol_frames(
        symbols,
        period=period,
        interval=interval,
        auto_adjust=auto_adjust,
        batch_size=batch_size,
        timeout=timeout,
        retries=retries,
        recover_missing=recover_missing,
        diagnostics=diagnostics,
        cache_ttl_seconds=cache_ttl_seconds,
    )
    return frames, {
        "requested": len(symbols),
        "usable": len(frames),
        "missing": missing,
        "coverage_pct": round(len(frames) / len(symbols) * 100, 1) if symbols else 100.0,
        "complete": not missing,
        "failure_diagnostics": list(
            dict.fromkeys(item for item in diagnostics if not item.startswith("download summary:"))
        ),
    }
