import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import pandas as pd
import yfinance as yf

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
    dynamic_bse_symbols,
    dynamic_nse_symbols,
    universe_source_status,
    yahoo_symbol_for_bse_code,
)
from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES
from services.sector_mapping import sector_for_symbol

TOP_CANDIDATES_TO_ANALYZE = 40
DISPLAY_COUNT = 20
DOWNLOAD_CHUNK_SIZE = 40
MAX_CANDIDATES_PER_EXCHANGE = 20
SCREEN_DOWNLOAD_WORKERS = 3
ANALYSIS_PERIOD = "1y"


def _ticker(symbol: str, exchange: str) -> str | None:
    """Return a Yahoo ticker, resolving BSE scrip codes to their company symbols."""
    normalized = str(symbol).strip().upper()
    if exchange == "NSE":
        yahoo_symbol = {"ZOMATO": "ETERNAL", "TATAMOTORS": "TMPV"}.get(normalized, normalized)
        return f"{yahoo_symbol}.NS"
    if exchange != "BSE":
        raise ValueError(f"Unsupported exchange: {exchange}")
    yahoo_symbol = yahoo_symbol_for_bse_code(normalized)
    return f"{yahoo_symbol}.BO" if yahoo_symbol else None


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
    finite_rows = frame.apply(lambda column: column.map(math.isfinite)).all(axis=1)
    return frame.loc[finite_rows].copy()


def _download_chunk(chunk: list[str]) -> pd.DataFrame:
    """Download a mover-screen chunk, retrying once without threading."""
    try:
        history = yf.download(
            tickers=chunk,
            period="5d",
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="ticker",
            threads=False,
            timeout=15,
        )
        if history is not None and not history.empty:
            return history
    except Exception:
        pass

    try:
        history = yf.download(
            tickers=chunk,
            period="5d",
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="ticker",
            threads=False,
            timeout=15,
        )
    except Exception:
        return pd.DataFrame()
    return history if history is not None else pd.DataFrame()


def _download_analysis_chunk(chunk: list[str]) -> pd.DataFrame:
    """Download the full history for shortlisted tickers in one batch."""
    try:
        history = yf.download(
            tickers=chunk,
            period=ANALYSIS_PERIOD,
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="ticker",
            threads=True,
            timeout=15,
        )
        if history is not None and not history.empty:
            return history
    except Exception:
        pass

    try:
        history = yf.download(
            tickers=chunk,
            period=ANALYSIS_PERIOD,
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="ticker",
            threads=False,
            timeout=20,
        )
    except Exception:
        return pd.DataFrame()
    return history if history is not None else pd.DataFrame()


def _batch_change_screen(
    candidates: dict[str, list[str]],
    coverage: dict[str, dict[str, Any]] | None = None,
) -> list[tuple[str, str, float, float]]:
    """Screen all supplied symbols in bounded concurrent Yahoo Finance batches."""
    ranked: list[tuple[str, str, float, float]] = []
    jobs: list[tuple[str, list[str]]] = []

    for exchange, symbols in candidates.items():
        stats = coverage.setdefault(exchange, {}) if coverage is not None else {}
        mapped = [(symbol, _ticker(symbol, exchange)) for symbol in symbols]
        tickers = [ticker for _symbol, ticker in mapped if ticker is not None]
        if coverage is not None:
            stats["tickers_requested"] = len(tickers)
            stats["unmapped_symbols"] = sum(ticker is None for _symbol, ticker in mapped)

        for offset in range(0, len(tickers), DOWNLOAD_CHUNK_SIZE):
            jobs.append((exchange, tickers[offset : offset + DOWNLOAD_CHUNK_SIZE]))

        if coverage is not None:
            stats["screen_chunks_requested"] = sum(
                1 for job_exchange, _chunk in jobs if job_exchange == exchange
            )

    def screen_result(exchange: str, chunk: list[str], history: pd.DataFrame) -> None:
        stats = coverage.setdefault(exchange, {}) if coverage is not None else {}
        if history.empty:
            if coverage is not None:
                stats["screen_chunks_empty"] = stats.get("screen_chunks_empty", 0) + 1
            return

        for ticker in chunk:
            try:
                close = _extract_series(history, ticker, "Close")
                volume = _extract_series(history, ticker, "Volume")
                if len(close) < 2 or volume.empty:
                    continue

                latest = float(close.iloc[-1])
                previous = float(close.iloc[-2])
                average_volume = float(volume.tail(5).mean())
                if (
                    not all(
                        math.isfinite(value) for value in (latest, previous, average_volume)
                    )
                    or previous <= 0
                    or latest <= 0
                    or average_volume < 0
                ):
                    continue

                change_pct = ((latest - previous) / previous) * 100
                average_turnover = latest * average_volume
                if not math.isfinite(average_turnover):
                    continue
                if coverage is not None:
                    stats["histories_returned"] = stats.get("histories_returned", 0) + 1
                ranked.append((ticker, exchange, change_pct, average_turnover))
            except (KeyError, TypeError, ValueError, IndexError):
                continue

    if jobs:
        with ThreadPoolExecutor(max_workers=SCREEN_DOWNLOAD_WORKERS) as executor:
            future_jobs = {
                executor.submit(_download_chunk, chunk): (exchange, chunk)
                for exchange, chunk in jobs
            }
            for future in as_completed(future_jobs):
                exchange, chunk = future_jobs[future]
                try:
                    history = future.result()
                except Exception:
                    history = pd.DataFrame()
                screen_result(exchange, chunk, history)

    ranked.sort(key=lambda row: abs(row[2]), reverse=True)
    return ranked


def _analyze_history(
    ticker: str,
    history: pd.DataFrame,
    average_turnover: float | None = None,
) -> dict[str, Any] | None:
    """Run the scanner's technical analysis locally on already-downloaded data."""
    df = _extract_history_frame(history, ticker)
    if len(df) < 50:
        return None

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
            return None

        last = df.iloc[-1]
        exchange = "BSE" if ticker.endswith(".BO") else "NSE"
        symbol = ticker.removesuffix(".NS").removesuffix(".BO")
        return {
            "Symbol": symbol,
            "Exchange": exchange,
            "Sector": sector_for_symbol(symbol),
            "Price": round(float(last["Close"]), 2),
            "Avg Turnover (₹)": (
                round(average_turnover, 0) if average_turnover is not None else None
            ),
            "Trend": trend["Trend"],
            "RSI": round(float(last["RSI_14"]), 2),
            "MACD": round(float(last["MACD"]), 2),
            "ATR": round(float(last["ATR"]), 2),
            "AI Score": signal["Score"],
            "Confidence": signal["Confidence"],
            "Confidence Status": signal.get("Confidence Status", "Not calibrated"),
            "Data Frequency": "Daily",
            "Risk": signal.get("Risk", "Medium"),
            "Recommendation": signal["Recommendation"],
        }
    except (KeyError, TypeError, ValueError, IndexError):
        return None


def market_scan(
    exchange_filter: str = "NSE + BSE", universe_mode: str = "fast"
) -> pd.DataFrame:
    """Screen a curated basket or the official NSE/BSE equity universes."""
    if exchange_filter not in {"NSE", "BSE", "NSE + BSE"}:
        raise ValueError(f"Unsupported exchange filter: {exchange_filter}")
    if universe_mode not in {"fast", "full"}:
        raise ValueError(f"Unsupported universe mode: {universe_mode}")

    started = time.perf_counter()
    selected = ("NSE", "BSE") if exchange_filter == "NSE + BSE" else (exchange_filter,)
    timings: dict[str, float] = {}
    coverage: dict[str, dict[str, Any]] = {
        exchange: {
            "candidates": 0,
            "tickers_requested": 0,
            "histories_returned": 0,
            "screen_chunks_requested": 0,
            "screen_chunks_empty": 0,
            "analysis_requested": 0,
            "analysis_download_failed": 0,
            "analyses_completed": 0,
            "final_rows": 0,
        }
        for exchange in selected
    }

    def finish(frame: pd.DataFrame) -> pd.DataFrame:
        timings["total_seconds"] = round(time.perf_counter() - started, 6)
        frame.attrs["scanner_timings"] = dict(timings)
        frame.attrs["scanner_coverage"] = {
            exchange: dict(values) for exchange, values in coverage.items()
        }
        frame.attrs["scanner_universe_mode"] = universe_mode
        if universe_mode == "full":
            frame.attrs["scanner_universe_sources"] = universe_source_status()
        return frame

    universe_started = time.perf_counter()
    if universe_mode == "fast":
        candidates = {
            exchange: list(NSE_CANDIDATES if exchange == "NSE" else BSE_CANDIDATES)
            for exchange in selected
        }
        for exchange, symbols in candidates.items():
            coverage[exchange]["source"] = "curated basket"
            coverage[exchange]["candidates"] = len(symbols)
    else:
        candidates = {}
        for exchange in selected:
            symbols = dynamic_nse_symbols() if exchange == "NSE" else dynamic_bse_symbols()
            source = universe_source_status()[exchange]
            is_official = source.get("origin") == "official"
            # Never label a curated fallback as a full-universe scan.
            candidates[exchange] = list(symbols) if is_official else []
            coverage[exchange]["source"] = source.get("source", "unknown")
            coverage[exchange]["source_status"] = source.get("official_source_status", "unknown")
            coverage[exchange]["source_symbols"] = int(source.get("source_symbols", 0))
            coverage[exchange]["source_reason"] = source.get("reason", "")
            coverage[exchange]["candidates"] = len(candidates[exchange])
    timings["universe_build_seconds"] = round(time.perf_counter() - universe_started, 6)

    screen_started = time.perf_counter()
    movers = _batch_change_screen(candidates, coverage)
    timings["screen_seconds"] = round(time.perf_counter() - screen_started, 6)
    if not movers:
        return finish(pd.DataFrame())

    analysis_tickers: list[str] = []
    seen_companies: set[str] = set()
    exchange_counts = {exchange: 0 for exchange in selected}
    for ticker, exchange, _change, _turnover in movers:
        company_key = ticker.rsplit(".", maxsplit=1)[0]
        if company_key in seen_companies or exchange_counts[exchange] >= MAX_CANDIDATES_PER_EXCHANGE:
            continue
        analysis_tickers.append(ticker)
        seen_companies.add(company_key)
        exchange_counts[exchange] += 1
        if len(analysis_tickers) >= TOP_CANDIDATES_TO_ANALYZE:
            break

    for exchange, count in exchange_counts.items():
        coverage[exchange]["analysis_requested"] = count
    if not analysis_tickers:
        return finish(pd.DataFrame())

    analysis_download_started = time.perf_counter()
    history = _download_analysis_chunk(analysis_tickers)
    timings["analysis_download_seconds"] = round(time.perf_counter() - analysis_download_started, 6)
    if history.empty:
        for exchange, count in exchange_counts.items():
            coverage[exchange]["analysis_download_failed"] = count
        return finish(pd.DataFrame())

    turnover_by_ticker = {ticker: turnover for ticker, _exchange, _change, turnover in movers}
    ticker_exchange = {ticker: exchange for ticker, exchange, _change, _turnover in movers}

    analysis_started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    for ticker in analysis_tickers:
        row = _analyze_history(ticker, history, turnover_by_ticker.get(ticker))
        if row is not None:
            rows.append(row)
            exchange = ticker_exchange[ticker]
            coverage[exchange]["analyses_completed"] += 1
            coverage[exchange]["final_rows"] += 1
    timings["analysis_seconds"] = round(time.perf_counter() - analysis_started, 6)

    result = pd.DataFrame(rows)
    if result.empty:
        return finish(result)

    result = (
        result.sort_values(by="AI Score", ascending=False)
        .head(DISPLAY_COUNT)
        .reset_index(drop=True)
    )
    return finish(result)
