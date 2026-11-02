"""Scan symbols saved in the user's personal watchlist."""

from typing import Any

import pandas as pd

from services.analyzer import analyze_stock
from services.intraday_market_context import intraday_market_context
from services.resilient_market_data import download_symbol_frames


def _normalize_ticker(symbol: str) -> str:
    value = str(symbol).strip().upper()
    if value.endswith((".NS", ".BO")):
        return value
    # The existing watchlist stores exchange-qualified symbols. For older or
    # manually entered unqualified entries, default to NSE convention.
    return f"{value}.NS" if value else ""


def _observation_columns(observation: Any) -> dict[str, Any]:
    """Expose canonical quote freshness separately from historical analysis values."""
    if not isinstance(observation, dict):
        observation = {}
    return {
        "Latest Observation Price": observation.get("price"),
        "Observed At": observation.get("observed_at") or "UNKNOWN",
        "Observation Frequency": observation.get("frequency") or "unknown",
        "Observation Status": observation.get("session_status") or "MARKET DATA STATUS UNAVAILABLE",
        "Tick Live": bool(observation.get("is_tick_live", False)),
    }


_CONTEXT_FIELDS = {
    "Gap %": None,
    "Intraday change %": None,
    "Session volume": None,
    "Cumulative RVOL": None,
    "Session turnover": None,
    "Turnover ratio": None,
    "Context status": "INTRADAY CONTEXT UNAVAILABLE",
    "Cumulative RVOL basis": "Not time-of-day normalized",
}


def _intraday_context_columns(
    intraday: pd.DataFrame | None,
    daily: pd.DataFrame | None,
) -> dict[str, Any]:
    """Build descriptive context from intraday candles and prior daily baselines."""
    if intraday is None or intraday.empty:
        return dict(_CONTEXT_FIELDS)

    session_date = pd.Timestamp(intraday.index[-1]).date()
    baselines = pd.DataFrame() if daily is None else daily.copy()
    if not baselines.empty:
        baselines = baselines.loc[
            [pd.Timestamp(index).date() < session_date for index in baselines.index]
        ]
        required = {"Close", "Volume"}
        if not required.issubset(baselines.columns):
            baselines = pd.DataFrame()
        else:
            baselines = baselines.loc[:, ["Close", "Volume"]].apply(
                pd.to_numeric, errors="coerce"
            )
            baselines = baselines.replace([float("inf"), float("-inf")], float("nan"))
            baselines = baselines.dropna(subset=["Close", "Volume"])
            baselines = baselines.loc[(baselines["Close"] > 0) & (baselines["Volume"] >= 0)]
            baselines = baselines.tail(20)

    average_volume = float(baselines["Volume"].mean()) if not baselines.empty else None
    average_turnover = (
        float((baselines["Close"] * baselines["Volume"]).mean())
        if not baselines.empty
        else None
    )
    context = intraday_market_context(
        intraday,
        previous_close=(
            float(baselines["Close"].iloc[-1]) if not baselines.empty else None
        ),
        average_daily_volume=average_volume,
        average_daily_turnover=average_turnover,
    )
    if not context:
        return dict(_CONTEXT_FIELDS)
    return {
        **_CONTEXT_FIELDS,
        **context,
        "Context status": context.get("Context status", "INTRADAY CONTEXT UNAVAILABLE"),
    }


def scan_watchlist(symbols: list[str]) -> pd.DataFrame:
    """Analyze each saved symbol directly; do not substitute broad-universe movers."""
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    tickers = list(
        dict.fromkeys(
            ticker for symbol in symbols if (ticker := _normalize_ticker(symbol))
        )
    )
    intraday_frames: dict[str, pd.DataFrame] = {}
    daily_frames: dict[str, pd.DataFrame] = {}
    if tickers:
        try:
            intraday_frames, _ = download_symbol_frames(
                tickers,
                period="1d",
                interval="1m",
                auto_adjust=True,
                batch_size=10,
                timeout=15,
                retries=0,
                recover_missing=False,
            )
            daily_frames, _ = download_symbol_frames(
                tickers,
                period="1mo",
                interval="1d",
                auto_adjust=True,
                batch_size=10,
                timeout=15,
                retries=0,
                recover_missing=False,
            )
        except Exception:
            # Context is optional; existing analysis should remain available.
            intraday_frames, daily_frames = {}, {}
    for symbol in symbols:
        ticker = _normalize_ticker(symbol)
        if not ticker or ticker in seen:
            continue
        seen.add(ticker)
        try:
            result = analyze_stock(ticker)
            last = result["last"]
            signal = result["signal"]
            trend = result["trend"]
            rows.append(
                {
                    "Symbol": ticker.removesuffix(".NS").removesuffix(".BO"),
                    "Exchange": "BSE" if ticker.endswith(".BO") else "NSE",
                    "Price": round(float(last["Close"]), 2),
                    "Analysis Data Frequency": "DAILY HISTORY",
                    **_observation_columns(signal.get("MarketObservation")),
                    **_intraday_context_columns(
                        intraday_frames.get(ticker), daily_frames.get(ticker)
                    ),
                    "Trend": trend["Trend"],
                    "RSI": round(float(last["RSI_14"]), 2),
                    "MACD": round(float(last["MACD"]), 2),
                    "ATR": round(float(last["ATR"]), 2),
                    "AI Score": signal["Score"],
                    "Confidence": signal["Confidence"],
                    "Risk": "Medium",
                    "Recommendation": signal["Recommendation"],
                }
            )
        except Exception:
            # One unavailable/invalid ticker must not prevent the rest of the list.
            continue
    if not rows:
        return pd.DataFrame()
    return (
        pd.DataFrame(rows)
        .sort_values(by=["AI Score", "Confidence"], ascending=[False, False])
        .reset_index(drop=True)
    )
