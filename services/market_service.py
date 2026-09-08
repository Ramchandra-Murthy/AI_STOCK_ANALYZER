"""Canonical market-data service.

The dashboard needs a single, defensive boundary around yfinance.  The values
returned here are the latest *available daily observations*, not guaranteed
exchange-tick live prices.  This distinction prevents stale/unavailable data
from being presented as live market truth.
"""

from __future__ import annotations

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

    # Some yfinance versions/providers return a one-column MultiIndex.
    if isinstance(close, pd.DataFrame):
        if close.shape[1] != 1:
            return pd.Series(dtype="float64")
        close = close.iloc[:, 0]

    return pd.to_numeric(close, errors="coerce").dropna()


def _get_last_change(ticker: str) -> tuple[float | None, float | None]:
    """Return latest available close and percentage change versus prior close."""
    try:
        history = yf.Ticker(ticker).history(
            period="5d",
            interval="1d",
            auto_adjust=True,
        )
        close = _clean_close_series(history)

        if len(close) < 2:
            return None, None

        latest = float(close.iloc[-1])
        previous = float(close.iloc[-2])

        if previous == 0:
            return round(latest, 2), None

        change_pct = ((latest - previous) / previous) * 100
        return round(latest, 2), round(change_pct, 2)
    except Exception:
        return None, None


def get_market_indices() -> dict[str, dict[str, Any]]:
    """Return the latest available market observations using a stable schema."""
    return {
        name: {"value": value, "change": change}
        for name, ticker in MARKET_INDICES.items()
        for value, change in [_get_last_change(ticker)]
    }


def get_top_movers() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return top five gainers and losers from the configured watchlist."""
    rows: list[dict[str, Any]] = []

    for name, ticker in WATCHLIST.items():
        value, change = _get_last_change(ticker)

        if value is None or change is None:
            continue

        rows.append(
            {
                "Symbol": name,
                "Price": value,
                "Change %": change,
            }
        )

    columns = ["Symbol", "Price", "Change %"]
    if not rows:
        empty = pd.DataFrame(columns=columns)
        return empty, empty.copy()

    frame = pd.DataFrame(rows, columns=columns)
    gainers = frame.sort_values("Change %", ascending=False).head(5).reset_index(drop=True)
    losers = frame.sort_values("Change %", ascending=True).head(5).reset_index(drop=True)
    return gainers, losers
