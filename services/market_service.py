"""Canonical market-data service.

Yahoo Finance is used as the external market-data boundary.  This service
reports the latest available observation and its observation timestamp; it
does not label daily Yahoo data as exchange-tick live data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import yfinance as yf


MARKET_INDICES = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANK NIFTY": "^NSEBANK",
    "INDIA VIX": "^INDIAVIX",
    "USD/INR": "INR=X",
    "GOLD": "GC=F",
}

WATCHLIST = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "SBIN": "SBIN.NS",
    "LT": "LT.NS",
    "ITC": "ITC.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "HINDUNILVR": "HINDUNILVR.NS",
}


def _clean_close_series(history: pd.DataFrame) -> pd.Series:
    """Return a numeric close series, handling yfinance shape variations."""
    if history is None or history.empty or "Close" not in history:
        return pd.Series(dtype="float64")

    close = history["Close"]

    if isinstance(close, pd.DataFrame):
        if close.shape[1] != 1:
            return pd.Series(dtype="float64")
        close = close.iloc[:, 0]

    return pd.to_numeric(close, errors="coerce").dropna()


def _get_last_observation(ticker: str) -> tuple[float | None, float | None, str | None]:
    """Return latest available close, daily change %, and observation timestamp."""
    try:
        history = yf.Ticker(ticker).history(
            period="5d",
            interval="1d",
            auto_adjust=True,
        )
        close = _clean_close_series(history)

        if len(close) < 1:
            return None, None, None

        latest = float(close.iloc[-1])
        previous = float(close.iloc[-2]) if len(close) >= 2 else None

        change_pct = None
        if previous is not None and previous != 0:
            change_pct = ((latest - previous) / previous) * 100

        timestamp = close.index[-1]
        if isinstance(timestamp, datetime):
            observed_at = timestamp.isoformat()
        else:
            observed_at = str(timestamp)

        return (
            round(latest, 2),
            round(change_pct, 2) if change_pct is not None else None,
            observed_at,
        )
    except Exception:
        return None, None, None


def _get_last_change(ticker: str) -> tuple[float | None, float | None]:
    """Backward-compatible value/change helper."""
    value, change, _ = _get_last_observation(ticker)
    return value, change


def get_latest_available_price(symbol: str) -> dict[str, Any]:
    """Return the latest available daily price with explicit freshness metadata."""
    normalized = symbol.strip().upper()
    if "." not in normalized:
        normalized += ".NS"

    value, change, observed_at = _get_last_observation(normalized)

    return {
        "symbol": normalized,
        "price": value,
        "change_pct": change,
        "observed_at": observed_at,
        "source": "Yahoo Finance",
        "frequency": "daily",
        "is_tick_live": False,
    }


def get_market_indices() -> dict[str, dict[str, Any]]:
    """Return latest available market observations using a stable schema."""
    result: dict[str, dict[str, Any]] = {}

    for name, ticker in MARKET_INDICES.items():
        value, change, observed_at = _get_last_observation(ticker)
        result[name] = {
            "value": value,
            "change": change,
            "observed_at": observed_at,
            "source": "Yahoo Finance",
            "frequency": "daily",
            "is_tick_live": False,
        }

    return result


def get_top_movers() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return top five gainers and losers from the configured watchlist."""
    rows: list[dict[str, Any]] = []

    for name, ticker in WATCHLIST.items():
        value, change, observed_at = _get_last_observation(ticker)

        if value is None or change is None:
            continue

        rows.append(
            {
                "Symbol": name,
                "Price": value,
                "Change %": change,
                "Observed": observed_at,
            }
        )

    columns = ["Symbol", "Price", "Change %", "Observed"]
    if not rows:
        empty = pd.DataFrame(columns=columns)
        return empty, empty.copy()

    frame = pd.DataFrame(rows, columns=columns)
    gainers = frame.sort_values("Change %", ascending=False).head(5).reset_index(drop=True)
    losers = frame.sort_values("Change %", ascending=True).head(5).reset_index(drop=True)
    return gainers, losers
