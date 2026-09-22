from typing import Any

import pandas as pd
import yfinance as yf

from scanner.dynamic_universe import merge_nse_universe, passes_liquidity_filter
from scanner.universe import BSE_CANDIDATES
from services.analyzer import analyze_stock

# The curated lists remain a fallback, while NSE symbols are refreshed from
# the exchange's current equity list before each cache window.
TOP_CANDIDATES_TO_ANALYZE = 30
DISPLAY_COUNT = 10
DOWNLOAD_CHUNK_SIZE = 40


def _ticker(symbol: str, exchange: str) -> str:
    suffix = "NS" if exchange == "NSE" else "BO"
    return f"{symbol}.{suffix}"


def _batch_change_screen(
    candidates: dict[str, list[str]],
) -> list[tuple[str, str, float]]:
    """Find liquid movers across the current NSE universe and BSE fallback list."""
    ranked: list[tuple[str, str, float]] = []

    for exchange, symbols in candidates.items():
        tickers = [_ticker(symbol, exchange) for symbol in symbols]
        for start in range(0, len(tickers), DOWNLOAD_CHUNK_SIZE):
            chunk = tickers[start : start + DOWNLOAD_CHUNK_SIZE]
            try:
                history = yf.download(
                    tickers=chunk,
                    period="5d",
                    interval="1d",
                    auto_adjust=True,
                    progress=False,
                    group_by="ticker",
                    threads=False,
                )
            except Exception:
                continue

            if history is None or history.empty:
                continue

            for ticker in chunk:
                try:
                    if isinstance(history.columns, pd.MultiIndex):
                        if ticker not in history.columns.get_level_values(0):
                            continue
                        close = pd.to_numeric(
                            history[ticker]["Close"], errors="coerce"
                        ).dropna()
                        volume = pd.to_numeric(
                            history[ticker]["Volume"], errors="coerce"
                        ).dropna()
                    else:
                        close = pd.to_numeric(
                            history["Close"], errors="coerce"
                        ).dropna()
                        volume = pd.to_numeric(
                            history["Volume"], errors="coerce"
                        ).dropna()

                    if len(close) < 2 or volume.empty:
                        continue

                    latest = float(close.iloc[-1])
                    previous = float(close.iloc[-2])
                    average_volume = float(volume.tail(5).mean())

                    if previous == 0 or not passes_liquidity_filter(
                        latest, average_volume
                    ):
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
        return {
            "Symbol": ticker.removesuffix(".NS").removesuffix(".BO"),
            "Exchange": exchange,
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
        # Unavailable symbols should not stop the rest of the scan.
        return None


def market_scan() -> pd.DataFrame:
    """Scan a refreshed NSE universe plus the curated BSE universe."""
    candidates = {
        "NSE": merge_nse_universe(),
        "BSE": BSE_CANDIDATES,
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
