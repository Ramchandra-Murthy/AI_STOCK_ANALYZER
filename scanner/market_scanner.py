import time
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
    merge_bse_universe,
    merge_nse_universe,
    yahoo_symbol_for_bse_code,
)
from services.sector_mapping import sector_for_symbol

TOP_CANDIDATES_TO_ANALYZE = 20
DISPLAY_COUNT = 20
DOWNLOAD_CHUNK_SIZE = 40
MAX_CANDIDATES_PER_EXCHANGE = 10
ANALYSIS_PERIOD = "1y"
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
    return frame.dropna(subset=required)


def _format_last_data_date(index: pd.Index) -> str:
    """Format the last daily candle date without inventing a date for unknown indexes."""
    if not isinstance(index, pd.DatetimeIndex) or index.empty:
        return "UNKNOWN"
    return index[-1].date().isoformat()


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
            threads=True,
            timeout=10,
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
    coverage: dict[str, dict[str, int]] | None = None,
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

        while pending_chunks:
            chunk = pending_chunks.pop(0)

            if coverage is not None:
                coverage[exchange]["screen_chunks_requested"] += 1

            history = _download_chunk(chunk)

            if history.empty:
                if coverage is not None:
                    coverage[exchange]["screen_chunks_empty"] += 1

                # Keep the existing NSE recovery behavior. For BSE, split a
                # failed batch only when it is larger than half the normal
                # chunk size, limiting repeated downloads during data failures.
                should_split = len(chunk) > 5 and (
                    exchange != "BSE" or len(chunk) > DOWNLOAD_CHUNK_SIZE // 2
                )

                if should_split:
                    midpoint = len(chunk) // 2
                    pending_chunks[0:0] = [chunk[:midpoint], chunk[midpoint:]]
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
                        _failed_tickers_until[ticker] = time.monotonic() + FAILED_TICKER_TTL_SECONDS
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
    """Run the scanner's technical analysis locally on already-downloaded data."""
    df = _extract_history_frame(history, ticker)
    if len(df) < 50:
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
            return None

        last = df.iloc[-1]
        exchange = "BSE" if ticker.endswith(".BO") else "NSE"
        symbol = ticker.removesuffix(".NS").removesuffix(".BO")
        return {
            "Symbol": symbol,
            "Exchange": exchange,
            "Sector": sector_for_symbol(symbol),
            "Price": round(float(last["Close"]), 2),
            "Data Frequency": "DAILY",
            "Last Data Date": last_data_date,
            "Data Status": "DAILY DATA · NOT INTRADAY",
            "Avg Turnover (₹)": (
                round(average_turnover, 0) if average_turnover is not None else None
            ),
            "Trend": trend["Trend"],
            "RSI": round(float(last["RSI_14"]), 2),
            "MACD": round(float(last["MACD"]), 2),
            "ATR": round(float(last["ATR"]), 2),
            "AI Score": signal["Score"],
            "Confidence": signal["Confidence"],
            "Risk": signal.get("Risk", "Medium"),
            "Recommendation": signal["Recommendation"],
        }
    except (KeyError, TypeError, ValueError, IndexError):
        return None


def market_scan(exchange_filter: str = "NSE + BSE") -> pd.DataFrame:
    """Scan the selected exchange universe using batched market data and local analysis."""
    selected = exchange_filter.strip().upper()
    candidates = {}
    if selected in ("NSE", "NSE + BSE", "BOTH"):
        candidates["NSE"] = merge_nse_universe()
    if selected in ("BSE", "NSE + BSE", "BOTH"):
        candidates["BSE"] = merge_bse_universe()
    if not candidates:
        raise ValueError(f"Unsupported exchange filter: {exchange_filter}")
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
    movers = _batch_change_screen(candidates, coverage=coverage)
    for exchange in coverage:
        coverage[exchange]["histories_rejected"] = max(
            0, coverage[exchange]["tickers_requested"] - coverage[exchange]["histories_returned"]
        )
        coverage[exchange]["history_coverage_pct"] = round(
            100
            * coverage[exchange]["histories_returned"]
            / max(1, coverage[exchange]["tickers_requested"]), 1
        )
    if not movers:
        empty = pd.DataFrame()
        empty.attrs["scanner_coverage"] = coverage
        return empty

    analysis_tickers: list[str] = []
    seen: set[str] = set()
    exchange_counts = {"NSE": 0, "BSE": 0}
    for ticker, exchange, _change, _turnover in movers:
        if ticker in seen or exchange_counts[exchange] >= MAX_CANDIDATES_PER_EXCHANGE:
            continue
        analysis_tickers.append(ticker)
        seen.add(ticker)
        exchange_counts[exchange] += 1
        if len(analysis_tickers) >= TOP_CANDIDATES_TO_ANALYZE:
            break

    for ticker in analysis_tickers:
        exchange = coverage_by_ticker.get(ticker)
        if exchange in coverage:
            coverage[exchange]["analysis_requested"] = (
                coverage[exchange].get("analysis_requested", 0) + 1
            )
    if not analysis_tickers:
        empty = pd.DataFrame()
        empty.attrs["scanner_coverage"] = coverage
        return empty

    history = _download_analysis_chunk(analysis_tickers)
    if history.empty:
        for exchange in coverage:
            if any(coverage_by_ticker.get(ticker) == exchange for ticker in analysis_tickers):
                coverage[exchange]["analysis_download_failed"] = 1
        empty = pd.DataFrame()
        empty.attrs["scanner_coverage"] = coverage
        return empty

    turnover_by_ticker = {ticker: turnover for ticker, _exchange, _change, turnover in movers}

    rows: list[dict[str, Any]] = []
    for ticker in analysis_tickers:
        row = _analyze_history(ticker, history, turnover_by_ticker.get(ticker))
        exchange = coverage_by_ticker.get(ticker)
        if row is not None:
            rows.append(row)
            if exchange in coverage:
                coverage[exchange]["analyses_completed"] += 1

    df = pd.DataFrame(rows)
    if df.empty:
        df.attrs["scanner_coverage"] = coverage
        return df

    result = (
        df.sort_values(by=["AI Score", "Confidence"], ascending=[False, False])
        .head(DISPLAY_COUNT)
        .reset_index(drop=True)
    )
    for exchange in coverage:
        coverage[exchange]["final_rows"] = int((result["Exchange"] == exchange).sum())
    result.attrs["scanner_coverage"] = coverage
    return result
