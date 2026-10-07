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
)
from services.sector_mapping import sector_for_symbol

TOP_CANDIDATES_TO_ANALYZE = 20
DISPLAY_COUNT = 20
DOWNLOAD_CHUNK_SIZE = 40
MAX_CANDIDATES_PER_EXCHANGE = 10
ANALYSIS_PERIOD = "1y"


def _ticker(symbol: str, exchange: str) -> str:
    suffix = "NS" if exchange == "NSE" else "BO"
    return f"{symbol}.{suffix}"


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
) -> list[tuple[str, str, float, float]]:
    """Find liquid movers across the current NSE universe and BSE fallback list."""
    ranked: list[tuple[str, str, float, float]] = []

    for exchange, symbols in candidates.items():
        tickers = [_ticker(symbol, exchange) for symbol in symbols]
        for start in range(0, len(tickers), DOWNLOAD_CHUNK_SIZE):
            chunk = tickers[start : start + DOWNLOAD_CHUNK_SIZE]
            history = _download_chunk(chunk)
            if history.empty:
                continue

            for ticker in chunk:
                try:
                    close = _extract_series(history, ticker, "Close")
                    volume = _extract_series(history, ticker, "Volume")
                    if len(close) < 2 or volume.empty:
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


def _analyze_history(ticker: str, history: pd.DataFrame) -> dict[str, Any] | None:
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
            "Trend": trend["Trend"],
            "RSI": round(float(last["RSI_14"]), 2),
            "MACD": round(float(last["MACD"]), 2),
            "ATR": round(float(last["ATR"]), 2),
            "AI Score": signal["Score"],
            "Confidence": abs(signal["Score"]),
            "Risk": signal.get("Risk", "Medium"),
            "Recommendation": signal["Recommendation"],
        }
    except (KeyError, TypeError, ValueError, IndexError):
        return None


def market_scan() -> pd.DataFrame:
    """Scan a refreshed universe using batched market data and local analysis."""
    candidates = {
        "NSE": merge_nse_universe(),
        "BSE": merge_bse_universe(),
    }
    movers = _batch_change_screen(candidates)
    if not movers:
        return pd.DataFrame()

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

    if not analysis_tickers:
        return pd.DataFrame()

    history = _download_analysis_chunk(analysis_tickers)
    if history.empty:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for ticker in analysis_tickers:
        row = _analyze_history(ticker, history)
        if row is not None:
            rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    return (
        df.sort_values(by=["AI Score", "Confidence"], ascending=[False, False])
        .head(DISPLAY_COUNT)
        .reset_index(drop=True)
    )
