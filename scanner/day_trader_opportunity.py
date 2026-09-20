"""Intraday opportunity screening for momentum and low-priced stocks.

The scanner ranks observable intraday conditions; it does not predict profits or
provide guaranteed trade signals. The candidate universe is the repository's
current NSE+BSE symbol list and is therefore not an exchange-wide screener.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import yfinance as yf

from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES

CHUNK_SIZE = 10


def _ticker(symbol: str, exchange: str) -> str:
    cleaned = str(symbol).strip().upper()
    suffix = ".NS" if exchange == "NSE" else ".BO"
    return cleaned if cleaned.endswith((".NS", ".BO")) else f"{cleaned}{suffix}"


def _frame(history: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if history is None or history.empty:
        return pd.DataFrame()
    if isinstance(history.columns, pd.MultiIndex):
        if ticker not in history.columns.get_level_values(0):
            return pd.DataFrame()
        data = history[ticker].copy()
    else:
        data = history.copy()
    required = {"High", "Low", "Close", "Volume"}
    if not required.issubset(data.columns):
        return pd.DataFrame()
    data = data.dropna(subset=list(required)).sort_index()
    return data[~data.index.duplicated(keep="last")]


def score_opportunity_rows(rows: pd.DataFrame) -> pd.DataFrame:
    """Score observable momentum, volume, range, and breakout conditions."""
    if rows is None or rows.empty:
        return pd.DataFrame()

    result = rows.copy()
    momentum = (result["5-min change %"].clip(lower=0) / 2.0 * 35).clip(upper=35)
    volume = ((result["Volume surge x"] - 1.0).clip(lower=0) / 2.0 * 30).clip(
        upper=30
    )
    volatility = (result["Session range %"].clip(lower=0) / 4.0 * 20).clip(
        upper=20
    )
    breakout = result["Breakout"].eq("YES").astype(float) * 15
    result["Opportunity score"] = (
        momentum + volume + volatility + breakout
    ).round(1)

    result["Setup"] = "Momentum watch"
    result.loc[
        (result["Volume surge x"] >= 1.5) & (result["5-min change %"] >= 0.75),
        "Setup",
    ] = "Volume + momentum"
    result.loc[result["Breakout"].eq("YES"), "Setup"] = "Breakout watch"
    result.loc[
        result["Low-price flag"].eq("YES") & (result["Volume surge x"] >= 1.5),
        "Setup",
    ] = "Low-price volume watch"

    return result.sort_values(
        ["Opportunity score", "5-min change %", "Volume surge x"],
        ascending=[False, False, False],
        na_position="last",
    ).reset_index(drop=True)


def scan_day_trader_opportunities(
    limit: int = 20,
    exchange_category: str = "Both",
    max_price: float = 50.0,
    lookback_minutes: int = 5,
    min_change_percent: float = 0.5,
    min_volume_surge: float = 1.2,
    low_price_only: bool = False,
) -> pd.DataFrame:
    """Find intraday momentum candidates, including configurable low-price mode.

    max_price is a configurable low-price threshold, not a formal definition
    of a penny stock. Prices and eligibility use the latest Yahoo Finance
    candle returned by the provider.
    """
    if (
        limit < 1
        or max_price <= 0
        or lookback_minutes < 1
        or min_change_percent < 0
        or min_volume_surge < 0
    ):
        return pd.DataFrame()

    exchanges = (
        ("NSE", "BSE")
        if exchange_category == "Both"
        else (exchange_category,)
    )
    universe = [(symbol, "NSE") for symbol in NSE_CANDIDATES] + [
        (symbol, "BSE") for symbol in BSE_CANDIDATES
    ]
    universe = [(symbol, venue) for symbol, venue in universe if venue in exchanges]

    candle_minutes = 1 if lookback_minutes in (2, 3) else 5
    interval = f"{candle_minutes}m"
    bars = max(1, int(round(lookback_minutes / candle_minutes)))
    rows: list[dict[str, Any]] = []

    for exchange in exchanges:
        tickers = [
            _ticker(symbol, exchange)
            for symbol, venue in universe
            if venue == exchange
        ]
        for start in range(0, len(tickers), CHUNK_SIZE):
            chunk = tickers[start : start + CHUNK_SIZE]
            try:
                history = yf.download(
                    tickers=chunk,
                    period="5d",
                    interval=interval,
                    progress=False,
                    auto_adjust=False,
                    group_by="ticker",
                    threads=False,
                )
            except Exception:
                continue

            for ticker in chunk:
                try:
                    data = _frame(history, ticker)
                    if len(data) <= bars:
                        continue

                    close = pd.to_numeric(data["Close"], errors="coerce").dropna()
                    high = pd.to_numeric(data["High"], errors="coerce").dropna()
                    volume = pd.to_numeric(data["Volume"], errors="coerce").dropna()
                    if len(close) <= bars or len(volume) < 6:
                        continue

                    price = float(close.iloc[-1])
                    prior = float(close.iloc[-1 - bars])
                    if price <= 0 or prior <= 0:
                        continue

                    change = (price / prior - 1.0) * 100.0
                    baseline = float(
                        volume.iloc[-min(21, len(volume) - 1) : -1].median()
                    )
                    latest_volume = float(volume.iloc[-1])
                    volume_surge = latest_volume / baseline if baseline > 0 else 0.0

                    session_date = data.index[-1].date()
                    session_mask = [stamp.date() == session_date for stamp in data.index]
                    session = data.loc[session_mask]
                    session_high = float(
                        pd.to_numeric(session["High"], errors="coerce").max()
                    )
                    session_low = float(
                        pd.to_numeric(session["Low"], errors="coerce").min()
                    )
                    session_range = (
                        (session_high - session_low) / price * 100.0
                        if price > 0
                        else 0.0
                    )

                    prior_highs = (
                        high.iloc[-21:-1] if len(high) >= 21 else high.iloc[:-1]
                    )
                    breakout = (
                        len(prior_highs) > 0 and price > float(prior_highs.max())
                    )

                    if change < min_change_percent or volume_surge < min_volume_surge:
                        continue
                    low_price = price <= max_price
                    if low_price_only and not low_price:
                        continue

                    rows.append(
                        {
                            "Symbol": ticker.rsplit(".", 1)[0],
                            "Exchange": exchange,
                            "Price": round(price, 2),
                            "5-min change %": round(change, 2),
                            "Volume surge x": round(volume_surge, 2),
                            "Session range %": round(session_range, 2),
                            "Breakout": "YES" if breakout else "—",
                            "Low-price flag": "YES" if low_price else "—",
                            "Latest candle": str(data.index[-1]),
                        }
                    )
                except (KeyError, TypeError, ValueError, IndexError):
                    continue

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows)
    result = score_opportunity_rows(result)
    result["Screen"] = result["Low-price flag"].map(
        {"YES": f"Low-price <= ₹{max_price:g}", "—": "Momentum"}
    )
    return result.head(max(1, min(int(limit), 100))).reset_index(drop=True)
