import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

from engine.breakout_engine import detect_breakout
from engine.signal_engine import generate_signal
from indicators.atr import calculate_atr
from indicators.bollinger import calculate_bollinger
from indicators.macd import calculate_macd
from indicators.macd_histogram import calculate_histogram
from indicators.moving_average import calculate_ema, calculate_sma
from indicators.rsi import calculate_rsi
from indicators.support_resistance import calculate_support_resistance
from indicators.trend import detect_trend
from scanner.dynamic_universe import (
    merge_bse_universe,
    merge_nse_universe,
    yahoo_symbol_for_bse_code,
)
from services.resilient_market_data import download_symbol_frames
from services.scanner_trend_sort import sort_bullish_to_bearish
from services.sector_mapping import sector_for_symbol

logger = logging.getLogger(__name__)

TOP_CANDIDATES_TO_ANALYZE = 20
DISPLAY_COUNT = 20
DOWNLOAD_CHUNK_SIZE = 100
MAX_SCREEN_WORKERS = 2
ANALYSIS_PERIOD = "1y"
MAX_DAILY_DATA_AGE_DAYS = 4
FAILED_TICKER_TTL_SECONDS = 5 * 60
_failed_tickers_until: dict[str, float] = {}


def _ticker(symbol: str, exchange: str) -> str:
    suffix = "NS" if exchange == "NSE" else "BO"
    return f"{symbol}.{suffix}"


def _yahoo_ticker(symbol: str, exchange: str) -> str | None:
    """Return a Yahoo Finance ticker for a supported exchange symbol."""
    if exchange == "NSE":
        replacements = {
            "ZOMATO": "ETERNAL",
            "TATAMOTORS": "TMPV",
        }
        yahoo_symbol = replacements.get(symbol, symbol)
        return f"{yahoo_symbol}.NS"

    if exchange == "BSE":
        mapped_symbol = yahoo_symbol_for_bse_code(symbol)
        return f"{mapped_symbol}.BO" if mapped_symbol else None

    return None


def _extract_series(history: pd.DataFrame, ticker: str, field: str) -> pd.Series:
    """Extract a field from either yfinance MultiIndex column orientation."""
    if not isinstance(history.columns, pd.MultiIndex):
        return pd.to_numeric(history[field], errors="coerce").dropna()

    levels = history.columns
    for level in range(levels.nlevels):
        if ticker in levels.get_level_values(level):
            frame = history.xs(ticker, axis=1, level=level)
            if field in frame.columns:
                return pd.to_numeric(frame[field], errors="coerce").dropna()

    return pd.Series(dtype="float64")


def _extract_history_frame(history: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Extract one ticker's OHLCV frame from a yfinance batch response."""
    if history.empty:
        return pd.DataFrame()

    if not isinstance(history.columns, pd.MultiIndex):
        frame = history.copy()
    else:
        frame = pd.DataFrame()
        levels = history.columns
        for level in range(levels.nlevels):
            if ticker in levels.get_level_values(level):
                frame = history.xs(ticker, axis=1, level=level).copy()
                break

    required = ["Open", "High", "Low", "Close", "Volume"]
    if frame.empty or any(column not in frame.columns for column in required):
        return pd.DataFrame()

    frame = frame.loc[:, required].apply(pd.to_numeric, errors="coerce")
    # Non-finite and physically invalid OHLCV rows must not enter indicators or rankings.
    frame = frame.replace([float("inf"), float("-inf")], float("nan")).dropna(subset=required)
    valid_prices = (frame[["Open", "High", "Low", "Close"]] > 0).all(axis=1)
    valid_volume = frame["Volume"] >= 0
    valid_ohlc = (frame["High"] >= frame[["Open", "Close", "Low"]].max(axis=1)) & (
        frame["Low"] <= frame[["Open", "Close", "High"]].min(axis=1)
    )
    return frame.loc[valid_prices & valid_volume & valid_ohlc]


def _format_last_data_date(index: pd.Index) -> str:
    """Format the last daily candle date without inventing a date for unknown indexes."""
    if not isinstance(index, pd.DatetimeIndex) or index.empty:
        return "UNKNOWN"
    return index[-1].date().isoformat()


def _daily_data_status(index: pd.Index, today: date | None = None) -> str:
    """Classify daily candle freshness without treating an unknown timestamp as fresh."""
    if not isinstance(index, pd.DatetimeIndex) or index.empty:
        return "UNKNOWN"
    latest = index.max()
    if pd.isna(latest):
        return "UNKNOWN"
    latest_date = latest.date()
    current_date = today or datetime.now(ZoneInfo("Asia/Kolkata")).date()
    if latest_date > current_date:
        return "FUTURE DATE"
    if (current_date - latest_date).days > MAX_DAILY_DATA_AGE_DAYS:
        return "STALE"
    return "FRESH"


def _download_shared_history(chunk: list[str], *, period: str, timeout: float) -> pd.DataFrame:
    """Download a chunk through the shared cache and bounded provider controls."""
    if not chunk:
        return pd.DataFrame()

    diagnostics: list[str] = []
    try:
        frames, missing = download_symbol_frames(
            chunk,
            period=period,
            interval="1d",
            auto_adjust=True,
            batch_size=len(chunk),
            timeout=timeout,
            recover_missing=True,
            diagnostics=diagnostics,
            max_workers=MAX_SCREEN_WORKERS,
        )
    except Exception as exc:
        logger.warning(
            "Shared market-data provider unavailable (%d symbols, first: %s): %s",
            len(chunk),
            chunk[0],
            exc,
        )
        return pd.DataFrame()

    if diagnostics:
        logger.debug("Market history retrieval: %s", diagnostics[-1])
    if missing:
        logger.info(
            "Historical coverage incomplete: requested=%d returned=%d missing=%d",
            len(chunk),
            len(frames),
            len(missing),
        )
    if not frames:
        return pd.DataFrame()
    if len(frames) == 1:
        ticker, frame = next(iter(frames.items()))
        return pd.concat({ticker: frame}, axis=1)
    return pd.concat(frames, axis=1)


def _download_chunk(chunk: list[str]) -> pd.DataFrame:
    """Download broad-market screening history through shared market-data controls."""
    return _download_shared_history(chunk, period="5d", timeout=15.0)


def _download_analysis_chunk(chunk: list[str]) -> pd.DataFrame:
    """Download full shortlisted history through the shared market-data service."""
    return _download_shared_history(chunk, period=ANALYSIS_PERIOD, timeout=20.0)


def _batch_change_screen(
    candidates: dict[str, list[str]],
    coverage: dict[str, dict[str, int]] | None = None,
    progress_callback: Any | None = None,
) -> list[tuple[str, str, float, float]]:
    """Find price movers across NSE and BSE universes without a liquidity exclusion."""
    ranked: list[tuple[str, str, float, float]] = []

    for exchange, symbols in candidates.items():
        ticker_map = {
            ticker: symbol
            for symbol in symbols
            if (ticker := _yahoo_ticker(symbol, exchange)) is not None
        }
        now = time.monotonic()
        for failed_ticker, expiry in list(_failed_tickers_until.items()):
            if expiry <= now:
                _failed_tickers_until.pop(failed_ticker, None)
        skipped_failed = [
            ticker for ticker in ticker_map if _failed_tickers_until.get(ticker, 0) > now
        ]
        tickers = [ticker for ticker in ticker_map if ticker not in skipped_failed]

        if coverage is not None:
            coverage[exchange]["tickers_requested"] = len(ticker_map)
            coverage[exchange]["mapped_tickers"] = len(ticker_map)
            coverage[exchange]["unmapped_symbols"] = len(symbols) - len(ticker_map)
            coverage[exchange]["cached_failures_skipped"] = coverage[exchange].get(
                "cached_failures_skipped", 0
            ) + len(skipped_failed)
            coverage[exchange]["screen_tickers_missing_data"] += (
                len(symbols) - len(ticker_map) + len(skipped_failed)
            )

        pending_chunks = [
            tickers[start : start + DOWNLOAD_CHUNK_SIZE]
            for start in range(0, len(tickers), DOWNLOAD_CHUNK_SIZE)
        ]
        initial_chunk_count = len(pending_chunks)
        completed_chunks = 0

        # Run a small, bounded number of independent Yahoo requests concurrently.
        # yfinance's own per-download threading is disabled to avoid nested
        # thread pools and excessive connection fan-out.
        while pending_chunks:
            current_chunks = pending_chunks
            pending_chunks = []
            with ThreadPoolExecutor(max_workers=MAX_SCREEN_WORKERS) as executor:
                futures = {
                    executor.submit(_download_chunk, chunk): chunk for chunk in current_chunks
                }
                for future in as_completed(futures):
                    chunk = futures[future]
                    completed_chunks += 1
                    if progress_callback is not None:
                        progress_callback(exchange, completed_chunks, initial_chunk_count)
                    if coverage is not None:
                        coverage[exchange]["screen_chunks_requested"] += 1

                    try:
                        history = future.result()
                    except Exception as exc:  # defensive boundary around provider workers
                        logger.warning(
                            "Price screen worker failed (%d symbols, first: %s): %s",
                            len(chunk),
                            chunk[0] if chunk else "-",
                            exc,
                        )
                        history = pd.DataFrame()

                    if history.empty:
                        if coverage is not None:
                            coverage[exchange]["screen_chunks_empty"] += 1

                        # Preserve bounded recovery: failed NSE chunks may split
                        # down to small batches; BSE chunks split only once.
                        should_split = len(chunk) > 5 and (
                            exchange != "BSE" or len(chunk) > DOWNLOAD_CHUNK_SIZE // 2
                        )
                        if should_split:
                            midpoint = len(chunk) // 2
                            pending_chunks.extend([chunk[:midpoint], chunk[midpoint:]])
                        elif coverage is not None:
                            coverage[exchange]["screen_tickers_missing_data"] += len(chunk)
                        continue

                    for ticker in chunk:
                        try:
                            close = _extract_series(history, ticker, "Close")
                            volume = _extract_series(history, ticker, "Volume")

                            usable_history = len(close) >= 2 and len(volume) >= 2
                            if usable_history:
                                _failed_tickers_until.pop(ticker, None)
                                if coverage is not None:
                                    coverage[exchange]["histories_returned"] += 1
                                    coverage[exchange]["screen_tickers_with_data"] += 1
                            else:
                                _failed_tickers_until[ticker] = (
                                    time.monotonic() + FAILED_TICKER_TTL_SECONDS
                                )
                                if coverage is not None:
                                    coverage[exchange]["screen_tickers_missing_data"] += 1

                            if not usable_history:
                                continue

                            latest = float(close.iloc[-1])
                            previous = float(close.iloc[-2])
                            average_volume = float(volume.tail(5).mean())

                            if previous == 0:
                                continue

                            change_pct = ((latest - previous) / previous) * 100
                            average_turnover = latest * average_volume
                            ranked.append((ticker, exchange, change_pct, average_turnover))

                        except (KeyError, TypeError, ValueError, IndexError):
                            continue

    ranked.sort(key=lambda row: abs(row[2]), reverse=True)
    return ranked


def _analyze_history(
    ticker: str,
    history: pd.DataFrame,
    average_turnover: float | None = None,
) -> dict[str, Any] | None:
    """Extract one ticker from a batch response and analyze its daily history."""
    return _analyze_history_frame(
        ticker,
        _extract_history_frame(history, ticker),
        average_turnover,
    )


def _analyze_history_frame(
    ticker: str,
    df: pd.DataFrame,
    average_turnover: float | None = None,
    outcome: dict[str, int] | None = None,
) -> dict[str, Any] | None:
    """Analyze one ticker and optionally record why it did not produce a result."""
    if outcome is not None:
        outcome["analysis_attempted"] = outcome.get("analysis_attempted", 0) + 1
    if len(df) < 50:
        if outcome is not None:
            outcome["analysis_insufficient_history"] = (
                outcome.get("analysis_insufficient_history", 0) + 1
            )
        return None

    last_data_date = _format_last_data_date(df.index)
    try:
        df = df.reset_index(drop=True)
        df = calculate_sma(df, 20)
        df = calculate_sma(df, 50)
        df = calculate_ema(df, 20)
        df = calculate_rsi(df, 14)
        df = calculate_macd(df)
        df = calculate_histogram(df)
        df = calculate_bollinger(df)
        df = calculate_atr(df)
        df = calculate_support_resistance(df, 10)

        trend = detect_trend(df)
        signal = generate_signal(df)
        detect_breakout(df)

        if signal.get("Status") != "OK":
            if outcome is not None:
                outcome["analysis_signal_rejected"] = outcome.get("analysis_signal_rejected", 0) + 1
            return None

        last = df.iloc[-1]
        exchange = "BSE" if ticker.endswith(".BO") else "NSE"
        symbol = ticker.removesuffix(".NS").removesuffix(".BO")
        return {
            "Symbol": symbol,
            "Exchange": exchange,
            "Sector": sector_for_symbol(symbol),
            "Price": round(float(last["Close"]), 2),
            "Data Provider": "Yahoo Finance",
            "Data Retrieved At": datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(
                timespec="seconds"
            ),
            "Data Frequency": "DAILY",
            "Last Data Date": last_data_date,
            "Data Freshness": _daily_data_status(
                pd.DatetimeIndex([last_data_date])
                if last_data_date != "UNKNOWN"
                else pd.DatetimeIndex([])
            ),
            "Data Status": "DAILY DATA · NOT INTRADAY",
            "Avg Turnover (₹)": (
                round(average_turnover, 0) if average_turnover is not None else None
            ),
            "Trend": trend["Trend"],
            "RSI": round(float(last["RSI_14"]), 2),
            "MACD": round(float(last["MACD"]), 2),
            "ATR": round(float(last["ATR"]), 2),
            "AI Score": signal["Score"],
            "Score Breakdown": "; ".join(
                f"{name} {value:+d}" for name, value in signal.get("Score Components", {}).items()
            ),
            "Confidence": signal.get("Confidence"),
            "Confidence Status": signal.get("Confidence Status", "Not calibrated"),
            "Risk": signal.get("Risk", "Medium"),
            "Recommendation": signal["Recommendation"],
            "Signal Reasons": "; ".join(signal.get("Reasons", [])) or "No reasons supplied",
        }
    except (KeyError, TypeError, ValueError, IndexError):
        if outcome is not None:
            outcome["analysis_errors"] = outcome.get("analysis_errors", 0) + 1
        return None


def _select_analysis_tickers(
    movers: list[tuple[str, str, float, float]],
    exchanges: list[str],
    limit: int,
) -> list[str]:
    """Select a bounded, exchange-balanced analysis shortlist.

    Allocate the limit evenly across selected exchanges first, then use any
    unused capacity for the strongest remaining movers.
    """
    if limit < 1 or not exchanges:
        return []

    base, remainder = divmod(limit, len(exchanges))
    quotas = {
        exchange: base + (1 if index < remainder else 0) for index, exchange in enumerate(exchanges)
    }
    selected: list[str] = []
    seen: set[str] = set()
    counts = {exchange: 0 for exchange in exchanges}

    for ticker, exchange, _change, _turnover in movers:
        if exchange not in quotas or ticker in seen or counts[exchange] >= quotas[exchange]:
            continue
        selected.append(ticker)
        seen.add(ticker)
        counts[exchange] += 1
        if len(selected) >= limit:
            return selected

    # If one exchange has too few candidates, fill the unused slots from the
    # remaining globally ranked movers instead of returning an undersized list.
    for ticker, exchange, _change, _turnover in movers:
        if exchange not in quotas or ticker in seen:
            continue
        selected.append(ticker)
        seen.add(ticker)
        if len(selected) >= limit:
            break
    return selected


def market_scan(
    exchange_filter: str = "NSE + BSE",
    progress_callback: Any | None = None,
    analysis_limit: int = TOP_CANDIDATES_TO_ANALYZE,
) -> pd.DataFrame:
    """Scan the selected exchange universe using batched market data and local analysis."""
    if not isinstance(analysis_limit, int) or isinstance(analysis_limit, bool):
        raise ValueError("analysis_limit must be a positive integer")
    if analysis_limit < 1 or analysis_limit > 500:
        raise ValueError("analysis_limit must be between 1 and 500")

    scan_started = time.perf_counter()
    cpu_started = time.process_time()
    timings: dict[str, float] = {
        "screen_workers": MAX_SCREEN_WORKERS,
        "download_chunk_size": DOWNLOAD_CHUNK_SIZE,
    }
    selected = exchange_filter.strip().upper()
    universe_started = time.perf_counter()
    candidates = {}
    if selected in ("NSE", "NSE + BSE", "BOTH"):
        candidates["NSE"] = merge_nse_universe()
    if selected in ("BSE", "NSE + BSE", "BOTH"):
        candidates["BSE"] = merge_bse_universe()
    if not candidates:
        raise ValueError(f"Unsupported exchange filter: {exchange_filter}")
    timings["universe_build_seconds"] = time.perf_counter() - universe_started
    coverage = {
        exchange: {
            "candidates": len(symbols),
            "tickers_requested": 0,
            "mapped_tickers": 0,
            "unmapped_symbols": 0,
            "screen_chunks_requested": 0,
            "screen_chunks_empty": 0,
            "screen_tickers_with_data": 0,
            "screen_tickers_missing_data": 0,
            "histories_returned": 0,
            "histories_rejected": 0,
            "analysis_download_failed": 0,
            "stale_data_rejected": 0,
            "unknown_timestamp_rejected": 0,
            "future_timestamp_rejected": 0,
            "analysis_attempted": 0,
            "analysis_insufficient_history": 0,
            "analysis_signal_rejected": 0,
            "analysis_errors": 0,
            "analyses_completed": 0,
            "final_rows": 0,
            "cached_failures_skipped": 0,
        }
        for exchange, symbols in candidates.items()
    }
    coverage_by_ticker = {
        ticker: exchange
        for exchange, symbols in candidates.items()
        for symbol in symbols
        if (ticker := _yahoo_ticker(symbol, exchange)) is not None
    }
    screen_started = time.perf_counter()
    if progress_callback is None:
        movers = _batch_change_screen(candidates, coverage=coverage)
    else:
        movers = _batch_change_screen(
            candidates, coverage=coverage, progress_callback=progress_callback
        )
    timings["screen_seconds"] = time.perf_counter() - screen_started
    for exchange in coverage:
        coverage[exchange]["histories_rejected"] = max(
            0, coverage[exchange]["tickers_requested"] - coverage[exchange]["histories_returned"]
        )
        coverage[exchange]["history_coverage_pct"] = round(
            100
            * coverage[exchange]["histories_returned"]
            / max(1, coverage[exchange]["tickers_requested"]),
            1,
        )
    if not movers:
        empty = pd.DataFrame()
        empty.attrs["scanner_coverage"] = coverage
        timings["cpu_seconds"] = time.process_time() - cpu_started
        timings["total_seconds"] = time.perf_counter() - scan_started
        empty.attrs["scanner_timings"] = timings
        return empty

    exchange_order = list(candidates)
    available_by_exchange = {
        exchange: sum(1 for _ticker, venue, _change, _turnover in movers if venue == exchange)
        for exchange in exchange_order
    }
    selected_by_exchange = {exchange: 0 for exchange in exchange_order}
    analysis_tickers = _select_analysis_tickers(movers, exchange_order, analysis_limit)
    selected_set = set(analysis_tickers)
    for ticker, exchange, _change, _turnover in movers:
        if ticker in selected_set:
            selected_by_exchange[exchange] += 1
    for exchange in coverage:
        coverage[exchange]["analysis_candidates_available"] = available_by_exchange[exchange]
        coverage[exchange]["analysis_candidates_deferred"] = max(
            0, available_by_exchange[exchange] - selected_by_exchange[exchange]
        )
        coverage[exchange]["analysis_shortlist_limit"] = analysis_limit

    for ticker in analysis_tickers:
        exchange = coverage_by_ticker.get(ticker)
        if exchange in coverage:
            coverage[exchange]["analysis_requested"] = (
                coverage[exchange].get("analysis_requested", 0) + 1
            )
    if not analysis_tickers:
        empty = pd.DataFrame()
        empty.attrs["scanner_coverage"] = coverage
        timings["cpu_seconds"] = time.process_time() - cpu_started
        timings["total_seconds"] = time.perf_counter() - scan_started
        empty.attrs["scanner_timings"] = timings
        return empty

    analysis_download_started = time.perf_counter()
    history = _download_analysis_chunk(analysis_tickers)
    timings["analysis_download_seconds"] = time.perf_counter() - analysis_download_started
    if history.empty:
        for exchange in coverage:
            if any(coverage_by_ticker.get(ticker) == exchange for ticker in analysis_tickers):
                coverage[exchange]["analysis_download_failed"] = 1
        empty = pd.DataFrame()
        empty.attrs["scanner_coverage"] = coverage
        timings["cpu_seconds"] = time.process_time() - cpu_started
        timings["total_seconds"] = time.perf_counter() - scan_started
        empty.attrs["scanner_timings"] = timings
        return empty

    turnover_by_ticker = {ticker: turnover for ticker, _exchange, _change, turnover in movers}

    analysis_started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    for ticker in analysis_tickers:
        exchange = coverage_by_ticker.get(ticker)
        ticker_history = _extract_history_frame(history, ticker)
        freshness = _daily_data_status(ticker_history.index)
        if freshness != "FRESH":
            if exchange in coverage:
                if freshness == "STALE":
                    coverage[exchange]["stale_data_rejected"] += 1
                elif freshness == "FUTURE DATE":
                    coverage[exchange]["future_timestamp_rejected"] += 1
                else:
                    coverage[exchange]["unknown_timestamp_rejected"] += 1
            continue
        outcome = coverage.get(exchange, {})
        row = _analyze_history_frame(
            ticker, ticker_history, turnover_by_ticker.get(ticker), outcome=outcome
        )
        if row is not None:
            rows.append(row)
            if exchange in coverage:
                coverage[exchange]["analyses_completed"] += 1

    timings["analysis_seconds"] = time.perf_counter() - analysis_started
    df = pd.DataFrame(rows)
    if df.empty:
        df.attrs["scanner_coverage"] = coverage
        timings["cpu_seconds"] = time.process_time() - cpu_started
        timings["total_seconds"] = time.perf_counter() - scan_started
        df.attrs["scanner_timings"] = timings
        return df

    # Confidence is intentionally unavailable until calibrated on out-of-sample data.
    result = sort_bullish_to_bearish(df).head(analysis_limit).reset_index(drop=True)
    for exchange in coverage:
        coverage[exchange]["final_rows"] = int((result["Exchange"] == exchange).sum())
    result.attrs["scanner_coverage"] = coverage
    timings["cpu_seconds"] = time.process_time() - cpu_started
    timings["total_seconds"] = time.perf_counter() - scan_started
    result.attrs["scanner_timings"] = timings
    return result
