from typing import Any

import pandas as pd
import yfinance as yf

from scanner.dynamic_universe import (
    merge_bse_universe,
    merge_nse_universe,
    passes_liquidity_filter,
)
from services.analyzer import analyze_stock
from services.sector_mapping import sector_for_symbol

# The curated lists remain a fallback, while NSE symbols are refreshed from
# the exchange's current equity list before each cache window.
TOP_CANDIDATES_TO_ANALYZE = 30
DISPLAY_COUNT = 10
DOWNLOAD_CHUNK_SIZE = 40


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


def _batch_change_screen(
    candidates: dict[str, list[str]],
) -> list[tuple[str, str, float]]:
    """Find liquid movers across the current NSE universe and BSE fallback list."""
    ranked: list[tuple[str, str, float]] = []

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
                    if previous == 0 or not passes_liquidity_filter(latest, average_volume):
                        continue

                    change_pct = ((latest - previous) / previous) * 100
                    ranked.append((ticker, exchange, change_pct))
                except (KeyError, TypeError, ValueError, IndexError):
                    continue

    ranked.sort(key=lambda row: abs(row[2]), reverse=True)
    return ranked


def _analyze_candidate(ticker: str) -> dict[str, Any] | None:
    try:
        result = analyze_stock(ticker)
        last = result["last"]
        signal = result["signal"]
        trend = result["trend"]
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
            "Risk": "Medium",
            "Recommendation": signal["Recommendation"],
        }
    except Exception:
        return None


def market_scan() -> pd.DataFrame:
    """Scan a refreshed NSE universe plus the curated BSE universe."""
    candidates = {
        "NSE": merge_nse_universe(),
        "BSE": merge_bse_universe(),
    }
    movers = _batch_change_screen(candidates)
    if not movers:
        return pd.DataFrame()

    analysis_tickers: list[str] = []
    seen: set[str] = set()
    for ticker, _exchange, _change in movers:
        if ticker not in seen:
            analysis_tickers.append(ticker)
            seen.add(ticker)
        if len(analysis_tickers) >= TOP_CANDIDATES_TO_ANALYZE:
            break

    rows: list[dict[str, Any]] = []
    for ticker in analysis_tickers:
        row = _analyze_candidate(ticker)
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
