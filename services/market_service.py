"""Canonical boundary for externally sourced market observations."""

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

# Keep the existing dashboard universe on NSE, while allowing explicit
# BSE tickers to be passed through the same market-data boundary.
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

EXCHANGE_SUFFIXES = {
    "NSE": ".NS",
    "BSE": ".BO",
}


def normalize_market_symbol(symbol: str, exchange: str = "NSE") -> str:
    """Normalize an Indian equity symbol to a Yahoo Finance ticker.

    Explicit Yahoo Finance suffixes (.NS/.BO) are preserved.  Bare symbols
    default to NSE for backward compatibility with the existing dashboard.
    """
    normalized = symbol.strip().upper()
    if not normalized:
        return ""
    if normalized.endswith((".NS", ".BO")):
        return normalized
    suffix = EXCHANGE_SUFFIXES.get(exchange.strip().upper(), ".NS")
    return f"{normalized}{suffix}"


def _clean_close_series(history: pd.DataFrame) -> pd.Series:
    if history is None or history.empty or "Close" not in history:
        return pd.Series(dtype="float64")
    close = history["Close"]
    if isinstance(close, pd.DataFrame):
        if close.shape[1] != 1:
            return pd.Series(dtype="float64")
        close = close.iloc[:, 0]
    return pd.to_numeric(close, errors="coerce").dropna()


def _get_last_observation(
    ticker: str,
) -> tuple[float | None, float | None, float | None, str | None, str, bool]:
    """Return price, change, previous close, time, frequency and intraday flag."""
    try:
        symbol = yf.Ticker(ticker)
        intraday = symbol.history(period="1d", interval="1m", auto_adjust=True)
        close = _clean_close_series(intraday)
        if not close.empty:
            latest = float(close.iloc[-1])
            previous = None
            try:
                daily = symbol.history(period="5d", interval="1d", auto_adjust=True)
                daily_close = _clean_close_series(daily)
                if len(daily_close) >= 2:
                    previous = float(daily_close.iloc[-2])
                elif len(daily_close) == 1:
                    previous = float(daily_close.iloc[-1])
            except Exception:
                previous = None
            if previous is None and len(close) > 1:
                previous = float(close.iloc[-2])
            change = ((latest - previous) / previous) * 100 if previous else None
            timestamp = close.index[-1]
            observed_at = (
                timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp)
            )
            return (
                round(latest, 2),
                round(change, 2) if change is not None else None,
                round(previous, 2) if previous is not None else None,
                observed_at,
                "intraday_1m",
                True,
            )

        daily = symbol.history(period="5d", interval="1d", auto_adjust=True)
        close = _clean_close_series(daily)
        if close.empty:
            return None, None, None, None, "unavailable", False
        latest = float(close.iloc[-1])
        previous = float(close.iloc[-2]) if len(close) > 1 else None
        change = ((latest - previous) / previous) * 100 if previous else None
        timestamp = close.index[-1]
        observed_at = timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp)
        return (
            round(latest, 2),
            round(change, 2) if change is not None else None,
            round(previous, 2) if previous is not None else None,
            observed_at,
            "daily",
            False,
        )
    except Exception:
        return None, None, None, None, "unavailable", False


def get_latest_available_price(symbol: str, exchange: str = "NSE") -> dict[str, Any]:
    normalized = normalize_market_symbol(symbol, exchange)
    value, change, _previous_close, observed_at, frequency, is_intraday = _get_last_observation(
        normalized
    )
    resolved_exchange = "BSE" if normalized.endswith(".BO") else "NSE"
    return {
        "symbol": normalized,
        "exchange": resolved_exchange,
        "price": value,
        "change_pct": change,
        "observed_at": observed_at,
        "source": "Yahoo Finance",
        "frequency": frequency,
        "is_tick_live": False,
        "is_intraday": is_intraday,
    }


def get_market_indices() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name, ticker in MARKET_INDICES.items():
        value, change, _previous_close, observed_at, frequency, is_intraday = _get_last_observation(
            ticker
        )
        result[name] = {
            "value": value,
            "change": change,
            "observed_at": observed_at,
            "source": "Yahoo Finance",
            "frequency": frequency,
            "is_tick_live": False,
            "is_intraday": is_intraday,
        }
    return result


def get_top_movers() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    for name, ticker in WATCHLIST.items():
        value, change, _previous_close, observed_at, frequency, is_intraday = _get_last_observation(
            ticker
        )
        if value is not None and change is not None:
            rows.append(
                {
                    "Symbol": name,
                    "Exchange": "NSE" if ticker.endswith(".NS") else "BSE",
                    "Price": value,
                    "Change %": change,
                    "Observed": observed_at,
                    "Frequency": frequency,
                    "Intraday": is_intraday,
                }
            )
    columns = ["Symbol", "Exchange", "Price", "Change %", "Observed", "Frequency", "Intraday"]
    if not rows:
        empty = pd.DataFrame(columns=columns)
        return empty, empty.copy()
    frame = pd.DataFrame(rows, columns=columns)
    return frame.sort_values("Change %", ascending=False).head(5).reset_index(
        drop=True
    ), frame.sort_values("Change %", ascending=True).head(5).reset_index(drop=True)
