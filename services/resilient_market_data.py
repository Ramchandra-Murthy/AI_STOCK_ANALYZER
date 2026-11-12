"""Resilient Yahoo Finance market-data retrieval helpers.

These helpers keep provider failures explicit. They retry transient failures,
fall back to per-symbol retrieval for missing tickers, and never fabricate data.
They are intended for research/paper-trading workflows; Yahoo Finance is not an
exchange-tick execution feed.
"""

from __future__ import annotations

from collections import OrderedDict, deque
from collections.abc import Iterable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from threading import BoundedSemaphore, RLock
from time import monotonic, perf_counter, sleep
from typing import Any, Literal, TypedDict

import pandas as pd
import yfinance as yf

DEFAULT_RETRIES = 2
MAX_SINGLE_SYMBOL_RECOVERY_PER_CALL = 25
DEFAULT_MAX_RECOVERY_SECONDS = 20.0
DEFAULT_TIMEOUT = 12.0
RETRY_BACKOFF_SECONDS = 1.0
MAX_PROVIDER_REQUESTS_IN_FLIGHT = 4
MARKET_DATA_CACHE_MAX_ENTRIES = 2000
MARKET_DATA_CACHE_TTLS = {
    "1m": 20.0,
    "2m": 30.0,
    "5m": 45.0,
    "15m": 90.0,
    "30m": 120.0,
    "60m": 180.0,
    "90m": 180.0,
    "1h": 180.0,
    "1d": 900.0,
    "5d": 1800.0,
    "1wk": 3600.0,
    "1mo": 7200.0,
    "3mo": 7200.0,
}
PROVIDER_CIRCUIT_FAILURE_THRESHOLD = 3
PROVIDER_CIRCUIT_FAILURE_WINDOW_SECONDS = 60.0
PROVIDER_CIRCUIT_COOLDOWN_SECONDS = 30.0
PROVIDER_CIRCUIT_MAX_COOLDOWN_SECONDS = 300.0


class _ProviderCircuitState(TypedDict):
    state: Literal["closed", "open", "half_open"]
    failures: deque[float]
    opened_at: float
    cooldown_seconds: float
    trips: int
    probe_in_flight: bool


_PROVIDER_CIRCUIT_LOCK = RLock()
_PROVIDER_CIRCUIT: _ProviderCircuitState = {
    "state": "closed",
    "failures": deque(),
    "opened_at": 0.0,
    "cooldown_seconds": PROVIDER_CIRCUIT_COOLDOWN_SECONDS,
    "trips": 0,
    "probe_in_flight": False,
}


def _reset_provider_circuit_breaker() -> None:
    """Reset provider protection state; intended for isolated tests."""
    with _PROVIDER_CIRCUIT_LOCK:
        _PROVIDER_CIRCUIT["state"] = "closed"
        _PROVIDER_CIRCUIT["failures"] = deque()
        _PROVIDER_CIRCUIT["opened_at"] = 0.0
        _PROVIDER_CIRCUIT["cooldown_seconds"] = PROVIDER_CIRCUIT_COOLDOWN_SECONDS
        _PROVIDER_CIRCUIT["trips"] = 0
        _PROVIDER_CIRCUIT["probe_in_flight"] = False


def provider_circuit_breaker_stats() -> dict[str, Any]:
    """Return a read-only snapshot of the process-local Yahoo circuit breaker."""
    now = monotonic()
    with _PROVIDER_CIRCUIT_LOCK:
        state = _PROVIDER_CIRCUIT["state"]
        remaining = (
            max(
                0.0,
                _PROVIDER_CIRCUIT["cooldown_seconds"] - (now - _PROVIDER_CIRCUIT["opened_at"]),
            )
            if state == "open"
            else 0.0
        )
        return {
            "state": state,
            "recent_failures": len(_PROVIDER_CIRCUIT["failures"]),
            "cooldown_seconds": _PROVIDER_CIRCUIT["cooldown_seconds"],
            "cooldown_remaining_seconds": round(remaining, 2),
            "trips": _PROVIDER_CIRCUIT["trips"],
            "probe_in_flight": _PROVIDER_CIRCUIT["probe_in_flight"],
        }


def _provider_circuit_allows_request(diagnostics: list[str] | None = None) -> bool:
    """Allow normal traffic while closed and exactly one probe after cooldown."""
    now = monotonic()
    with _PROVIDER_CIRCUIT_LOCK:
        state = _PROVIDER_CIRCUIT["state"]
        if state == "open":
            elapsed = now - _PROVIDER_CIRCUIT["opened_at"]
            if elapsed < _PROVIDER_CIRCUIT["cooldown_seconds"]:
                if diagnostics is not None:
                    diagnostics.append("Yahoo provider circuit open; request suppressed")
                return False
            _PROVIDER_CIRCUIT["state"] = "half_open"
            state = "half_open"

        if state == "half_open":
            if _PROVIDER_CIRCUIT["probe_in_flight"]:
                if diagnostics is not None:
                    diagnostics.append("Yahoo provider circuit half-open; probe already in flight")
                return False
            _PROVIDER_CIRCUIT["probe_in_flight"] = True
        return True


def _provider_circuit_record_failure() -> None:
    """Count provider failures and open/re-open the circuit at the threshold."""
    now = monotonic()
    with _PROVIDER_CIRCUIT_LOCK:
        state = _PROVIDER_CIRCUIT["state"]
        if state == "open":
            return
        if state == "half_open":
            _PROVIDER_CIRCUIT["trips"] += 1
            _PROVIDER_CIRCUIT["cooldown_seconds"] = min(
                PROVIDER_CIRCUIT_COOLDOWN_SECONDS * (2 ** (_PROVIDER_CIRCUIT["trips"] - 1)),
                PROVIDER_CIRCUIT_MAX_COOLDOWN_SECONDS,
            )
            _PROVIDER_CIRCUIT["state"] = "open"
            _PROVIDER_CIRCUIT["opened_at"] = now
            _PROVIDER_CIRCUIT["probe_in_flight"] = False
            return

        failures = _PROVIDER_CIRCUIT["failures"]
        failures.append(now)
        while failures and now - failures[0] > PROVIDER_CIRCUIT_FAILURE_WINDOW_SECONDS:
            failures.popleft()
        if len(failures) >= PROVIDER_CIRCUIT_FAILURE_THRESHOLD:
            _PROVIDER_CIRCUIT["trips"] += 1
            _PROVIDER_CIRCUIT["cooldown_seconds"] = min(
                PROVIDER_CIRCUIT_COOLDOWN_SECONDS * (2 ** (_PROVIDER_CIRCUIT["trips"] - 1)),
                PROVIDER_CIRCUIT_MAX_COOLDOWN_SECONDS,
            )
            _PROVIDER_CIRCUIT["state"] = "open"
            _PROVIDER_CIRCUIT["opened_at"] = now
            _PROVIDER_CIRCUIT["probe_in_flight"] = False


def _provider_circuit_record_success() -> None:
    """Close the circuit only after a successful half-open probe."""
    with _PROVIDER_CIRCUIT_LOCK:
        if _PROVIDER_CIRCUIT["state"] == "half_open":
            _PROVIDER_CIRCUIT["state"] = "closed"
            _PROVIDER_CIRCUIT["failures"].clear()
            _PROVIDER_CIRCUIT["cooldown_seconds"] = PROVIDER_CIRCUIT_COOLDOWN_SECONDS
            _PROVIDER_CIRCUIT["trips"] = 0
            _PROVIDER_CIRCUIT["probe_in_flight"] = False
        elif _PROVIDER_CIRCUIT["state"] == "closed":
            _PROVIDER_CIRCUIT["failures"].clear()


def _provider_circuit_cancel_probe() -> None:
    """Release a half-open probe reservation when request setup fails."""
    with _PROVIDER_CIRCUIT_LOCK:
        if _PROVIDER_CIRCUIT["state"] == "half_open":
            _PROVIDER_CIRCUIT["probe_in_flight"] = False


_PROVIDER_REQUEST_LIMIT = BoundedSemaphore(MAX_PROVIDER_REQUESTS_IN_FLIGHT)
_CACHE_LOCK = RLock()
_INFLIGHT_BATCH_LOCK = RLock()
_INFLIGHT_BATCH_DOWNLOADS: dict[tuple[Any, ...], Future[pd.DataFrame]] = {}
_MARKET_DATA_CACHE: OrderedDict[tuple[str, str, str, bool], tuple[float, pd.DataFrame]] = (
    OrderedDict()
)
_METADATA_CACHE: dict[str, tuple[float, float]] = {}
_NEGATIVE_METADATA_CACHE_MAX_ENTRIES = 2000
_NEGATIVE_METADATA_CACHE: OrderedDict[str, float] = OrderedDict()
_METADATA_CACHE_LOCK = RLock()
_COMPANY_NAME_CACHE: dict[str, tuple[float, str]] = {}
_COMPANY_NAME_NEGATIVE_CACHE: OrderedDict[str, float] = OrderedDict()
_COMPANY_NAME_CACHE_TTL_SECONDS = 24 * 60 * 60
_RUNTIME_STATS_LOCK = RLock()
_RUNTIME_STATS = {
    "scan_calls": 0,
    "batch_requests": 0,
    "single_symbol_requests": 0,
    "provider_errors": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "total_scan_seconds": 0.0,
}
DEFAULT_METADATA_CACHE_TTL_SECONDS = 1800.0
NEGATIVE_METADATA_CACHE_TTL_SECONDS = 120.0


def _store_negative_metadata_cache(
    cache: OrderedDict[str, float],
    symbol: str,
    ttl_seconds: float,
) -> None:
    """Store a missing-metadata result with an expiry and a hard size bound."""
    if ttl_seconds <= 0:
        return
    cache.pop(symbol, None)
    cache[symbol] = monotonic() + ttl_seconds
    while len(cache) > _NEGATIVE_METADATA_CACHE_MAX_ENTRIES:
        cache.popitem(last=False)


def _get_cached_negative_metadata(
    cache: OrderedDict[str, float],
    symbol: str,
    ttl_seconds: float,
    now: float,
) -> bool:
    """Return whether a negative result is still valid, removing expired entries."""
    negative_until = cache.get(symbol)
    if negative_until is None:
        return False
    if ttl_seconds > 0 and now < negative_until:
        cache.move_to_end(symbol)
        return True
    cache.pop(symbol, None)
    return False


def _record_runtime_stat(name: str, amount: int | float = 1) -> None:
    """Update one process-local market-data telemetry counter safely."""
    with _RUNTIME_STATS_LOCK:
        _RUNTIME_STATS[name] += amount


def market_data_runtime_stats() -> dict[str, int | float]:
    """Return process-local request, cache, error, and scan-duration counters."""
    with _RUNTIME_STATS_LOCK:
        stats = dict(_RUNTIME_STATS)
    stats["cache_entries"] = market_data_cache_stats()["entries"]
    stats["cache_capacity"] = MARKET_DATA_CACHE_MAX_ENTRIES
    return stats


def clear_market_data_runtime_stats() -> None:
    """Reset process-local telemetry counters for tests and diagnostics."""
    with _RUNTIME_STATS_LOCK:
        for key in _RUNTIME_STATS:
            _RUNTIME_STATS[key] = 0.0 if key == "total_scan_seconds" else 0


def get_market_cap(
    ticker: str,
    *,
    cache_ttl_seconds: float = DEFAULT_METADATA_CACHE_TTL_SECONDS,
    negative_cache_ttl_seconds: float = NEGATIVE_METADATA_CACHE_TTL_SECONDS,
    timeout: float = DEFAULT_TIMEOUT,
) -> float | None:
    """Fetch Yahoo market-cap metadata with positive and bounded negative TTL caches."""
    symbol = str(ticker).strip().upper()
    if not symbol:
        return None
    ttl = max(0.0, float(cache_ttl_seconds))
    negative_ttl = max(0.0, float(negative_cache_ttl_seconds))
    now = monotonic()
    with _METADATA_CACHE_LOCK:
        cached = _METADATA_CACHE.get(symbol)
        if cached is not None:
            stored_at, value = cached
            if ttl > 0 and now - stored_at < ttl:
                return value
            del _METADATA_CACHE[symbol]
        if _get_cached_negative_metadata(_NEGATIVE_METADATA_CACHE, symbol, negative_ttl, now):
            return None

    if not _provider_circuit_allows_request():
        return None

    try:
        with _PROVIDER_REQUEST_LIMIT:
            raw_value = yf.Ticker(symbol, timeout=timeout).fast_info.get("market_cap")
        _provider_circuit_record_success()
        value = float(raw_value) if raw_value is not None else 0.0
    except Exception:
        _provider_circuit_record_failure()
        return None

    if not pd.notna(value) or value <= 0:
        if negative_ttl > 0:
            with _METADATA_CACHE_LOCK:
                _store_negative_metadata_cache(_NEGATIVE_METADATA_CACHE, symbol, negative_ttl)
        return None

    with _METADATA_CACHE_LOCK:
        _NEGATIVE_METADATA_CACHE.pop(symbol, None)
        if ttl > 0:
            _METADATA_CACHE[symbol] = (monotonic(), value)
    return value


def clear_market_metadata_cache() -> None:
    """Clear positive and negative market-cap metadata caches."""
    with _METADATA_CACHE_LOCK:
        _METADATA_CACHE.clear()
        _NEGATIVE_METADATA_CACHE.clear()


def get_company_name(
    ticker: str,
    *,
    cache_ttl_seconds: float = _COMPANY_NAME_CACHE_TTL_SECONDS,
    negative_cache_ttl_seconds: float = NEGATIVE_METADATA_CACHE_TTL_SECONDS,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """Resolve company names with success caching and bounded missing-name caching."""
    symbol = str(ticker).strip().upper()
    if not symbol:
        return ""
    ttl = max(0.0, float(cache_ttl_seconds))
    negative_ttl = max(0.0, float(negative_cache_ttl_seconds))
    now = monotonic()
    with _METADATA_CACHE_LOCK:
        cached = _COMPANY_NAME_CACHE.get(symbol)
        if cached is not None:
            stored_at, cached_name = cached
            if ttl > 0 and now - stored_at < ttl:
                return cached_name
            del _COMPANY_NAME_CACHE[symbol]
        if _get_cached_negative_metadata(_COMPANY_NAME_NEGATIVE_CACHE, symbol, negative_ttl, now):
            return symbol

    if not _provider_circuit_allows_request():
        return symbol

    try:
        with _PROVIDER_REQUEST_LIMIT:
            info = yf.Ticker(symbol, timeout=timeout).get_info()
        _provider_circuit_record_success()
    except Exception:
        _provider_circuit_record_failure()
        return symbol

    raw_name = info.get("longName") or info.get("shortName") if isinstance(info, dict) else None
    resolved = raw_name.strip() if isinstance(raw_name, str) and raw_name.strip() else symbol
    with _METADATA_CACHE_LOCK:
        if resolved != symbol:
            _COMPANY_NAME_NEGATIVE_CACHE.pop(symbol, None)
            if ttl > 0:
                _COMPANY_NAME_CACHE[symbol] = (monotonic(), resolved)
        elif negative_ttl > 0:
            _store_negative_metadata_cache(
                _COMPANY_NAME_NEGATIVE_CACHE, symbol, negative_ttl
            )
    return resolved



def clear_company_name_cache() -> None:
    """Clear positive and negative company-name metadata caches."""
    with _METADATA_CACHE_LOCK:
        _COMPANY_NAME_CACHE.clear()
        _COMPANY_NAME_NEGATIVE_CACHE.clear()


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
    """Disable hidden provider retries; the shared service owns retry budgets."""
    try:
        yf.config.network.retries = 0
    except (AttributeError, TypeError, ValueError):
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
        if not _provider_circuit_allows_request(diagnostics):
            return pd.DataFrame()
        request_started = False
        try:
            with _PROVIDER_REQUEST_LIMIT:
                request_started = True
                _record_runtime_stat("batch_requests")
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
                _provider_circuit_record_success()
                return result
            _provider_circuit_record_failure()
            if diagnostics is not None:
                diagnostics.append("batch request returned no rows")
        except Exception as exc:
            last_error = exc
            _record_runtime_stat("provider_errors")
            if request_started:
                _provider_circuit_record_failure()
            else:
                _provider_circuit_cancel_probe()
            if diagnostics is not None:
                diagnostics.append(f"batch request raised {type(exc).__name__}")

        if attempt < retry_count:
            sleep(RETRY_BACKOFF_SECONDS * (2**attempt))

    if last_error is not None:
        return pd.DataFrame()
    return pd.DataFrame()


def _download_batch_singleflight(
    tickers: list[str],
    *,
    period: str,
    interval: str,
    auto_adjust: bool,
    timeout: float,
    retries: int,
    diagnostics: list[str] | None,
    cache_ttl_seconds: float,
) -> pd.DataFrame:
    """Coalesce identical concurrent batch downloads into one provider request.

    The first caller owns the provider request. Concurrent callers wait on the
    same Future and receive independent DataFrame copies. Successful frames are
    placed in the normal symbol cache before the in-flight entry is released,
    preventing a cache-miss gap between concurrent scans.
    """
    key = (
        tuple(tickers),
        str(period),
        str(interval),
        bool(auto_adjust),
        float(timeout),
        int(retries),
    )
    with _INFLIGHT_BATCH_LOCK:
        future = _INFLIGHT_BATCH_DOWNLOADS.get(key)
        is_leader = future is None
        if future is None:
            future = Future()
            _INFLIGHT_BATCH_DOWNLOADS[key] = future

    if not is_leader:
        return future.result().copy(deep=True)

    try:
        history = _download_batch(
            tickers,
            period=period,
            interval=interval,
            auto_adjust=auto_adjust,
            timeout=timeout,
            retries=retries,
            diagnostics=diagnostics,
        )
        if cache_ttl_seconds > 0 and history is not None and not history.empty:
            for ticker in tickers:
                frame = _ticker_frame(history, ticker)
                if not frame.empty:
                    _store_cached_frame(
                        _cache_key(ticker, period, interval, auto_adjust),
                        frame,
                    )
        result = history.copy(deep=True) if history is not None else pd.DataFrame()
        future.set_result(result)
        return result.copy(deep=True)
    except BaseException as exc:
        future.set_exception(exc)
        raise
    finally:
        with _INFLIGHT_BATCH_LOCK:
            if _INFLIGHT_BATCH_DOWNLOADS.get(key) is future:
                del _INFLIGHT_BATCH_DOWNLOADS[key]


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
        if not _provider_circuit_allows_request(diagnostics):
            return pd.DataFrame()
        request_started = False
        try:
            with _PROVIDER_REQUEST_LIMIT:
                request_started = True
                _record_runtime_stat("single_symbol_requests")
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
                _provider_circuit_record_success()
                return frame
            _provider_circuit_record_failure()
        except Exception as exc:
            _record_runtime_stat("provider_errors")
            if request_started:
                _provider_circuit_record_failure()
            else:
                _provider_circuit_cancel_probe()
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
    recovery_max_symbols: int | None = None,
    max_recovery_symbols: int = MAX_SINGLE_SYMBOL_RECOVERY_PER_CALL,
    max_recovery_seconds: float = DEFAULT_MAX_RECOVERY_SECONDS,
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
    _record_runtime_stat("scan_calls")
    recovery_seconds = 0.0
    recovery_count = 0
    recovery_limit = 0
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
            _record_runtime_stat("cache_hits")
        else:
            _record_runtime_stat("cache_misses")

    uncached_symbols = [ticker for ticker in symbols if ticker not in frames]
    chunks = [
        uncached_symbols[start : start + batch_size]
        for start in range(0, len(uncached_symbols), batch_size)
    ]
    batch_seconds = 0.0

    def download_one(chunk: list[str]) -> tuple[list[str], pd.DataFrame, float]:
        started = perf_counter()
        history = _download_batch_singleflight(
            chunk,
            period=period,
            interval=interval,
            auto_adjust=auto_adjust,
            timeout=timeout,
            retries=retries,
            diagnostics=diagnostics,
            cache_ttl_seconds=ttl,
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
        recovery_limit = max(
            0,
            int(max_recovery_symbols if recovery_max_symbols is None else recovery_max_symbols),
        )
        recovery_deadline = perf_counter() + max(0.0, float(max_recovery_seconds))
        for ticker in missing[:recovery_limit]:
            remaining = recovery_deadline - perf_counter()
            if remaining <= 0:
                break
            recovery_started = perf_counter()
            frame = _download_single(
                ticker,
                period=period,
                interval=interval,
                auto_adjust=auto_adjust,
                timeout=min(float(timeout), max(0.1, remaining)),
                retries=0,
                diagnostics=diagnostics,
            )
            recovery_seconds += perf_counter() - recovery_started
            recovery_count += 1
            if not frame.empty:
                frames[ticker] = frame

    if ttl > 0:
        # Cache only data fetched in this call; cache hits must retain their
        # original timestamp so repeated reads cannot extend stale data forever.
        for ticker in uncached_symbols:
            frame = frames.get(ticker)
            if frame is not None:
                _store_cached_frame(_cache_key(ticker, period, interval, auto_adjust), frame)

    _record_runtime_stat("total_scan_seconds", perf_counter() - scan_started)

    if diagnostics is not None:
        diagnostics.append(
            "download summary: "
            f"requested={len(symbols)} usable={len(frames)} "
            f"missing={len(symbols) - len(frames)} batches={len(chunks)} "
            f"cache_hits={cache_hits} cache_ttl={ttl:.0f}s "
            f"batch_workers={worker_count} provider_request_limit={MAX_PROVIDER_REQUESTS_IN_FLIGHT} "
            f"single_recovery_attempts={recovery_count} "
            f"single_recovery_limit={recovery_limit} "
            f"recovery_budget={max(0.0, float(max_recovery_seconds)):.2f}s "
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
    max_recovery_symbols: int = MAX_SINGLE_SYMBOL_RECOVERY_PER_CALL,
    max_recovery_seconds: float = DEFAULT_MAX_RECOVERY_SECONDS,
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
        max_recovery_symbols=max_recovery_symbols,
        max_recovery_seconds=max_recovery_seconds,
    )
    return frames, {
        "requested": len(symbols),
        "usable": len(frames),
        "missing": missing,
        "coverage_pct": round(len(frames) / len(symbols) * 100, 1) if symbols else 100.0,
        "complete": not missing,
        "provider_circuit": provider_circuit_breaker_stats(),
        "provider_degraded": provider_circuit_breaker_stats()["state"] != "closed",
        "failure_diagnostics": list(
            dict.fromkeys(item for item in diagnostics if not item.startswith("download summary:"))
        ),
    }
