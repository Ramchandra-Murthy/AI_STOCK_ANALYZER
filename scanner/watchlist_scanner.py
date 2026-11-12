"""Scan symbols saved in the user's personal watchlist."""

from datetime import datetime
from typing import Any

import pandas as pd

from services.analyzer import analyze_stock
from services.intraday_context_freshness import intraday_context_freshness
from services.intraday_data_quality import completed_ohlcv_bars
from services.intraday_market_context import intraday_market_context
from services.market_calendar import IST, equity_market_session_status
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
    "Context rejection reason": None,
    "Context freshness": "TIMESTAMP_UNAVAILABLE",
    "Market Session": "CALENDAR_UNAVAILABLE",
    "Cumulative RVOL basis": "Not time-of-day normalized",
}


def _market_session_status(now: datetime | None = None) -> str:
    """Return the shared equity calendar status for watchlist context."""
    return equity_market_session_status(now or datetime.now(tz=IST))


def _intraday_context_columns(
    intraday: pd.DataFrame | None,
    daily: pd.DataFrame | None,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build descriptive context from intraday candles and prior daily baselines."""
    market_session = _market_session_status(now)
    if intraday is None or intraday.empty:
        return {**_CONTEXT_FIELDS, "Market Session": market_session}
    evaluation_time = now or datetime.now(tz=IST)
    completed, rejected = completed_ohlcv_bars(intraday, evaluation_time, interval_minutes=1)
    reasons = {
        "incomplete": rejected["incomplete_candles"],
        "future": rejected["future_candles"],
        "duplicates": rejected["duplicate_candles"],
        "invalid timestamp": rejected["invalid_timestamps"],
        "missing OHLCV": rejected["missing_ohlcv"],
        "invalid OHLCV": rejected["invalid_ohlcv"],
        "missing OHLCV columns": rejected["missing_ohlcv_columns"],
    }
    rejection_reason = (
        " · ".join(f"{reason}: {count}" for reason, count in reasons.items() if count) or None
    )
    if rejected["future_candles"]:
        return {
            **_CONTEXT_FIELDS,
            "Context status": "INVALID INTRADAY DATA",
            "Context freshness": "FUTURE_TIMESTAMP",
            "Context rejection reason": rejection_reason,
            "Market Session": market_session,
        }
    if (
        completed.empty
        or rejected["missing_ohlcv"]
        or rejected["invalid_ohlcv"]
        or rejected["missing_ohlcv_columns"]
    ):
        return {
            **_CONTEXT_FIELDS,
            "Context status": (
                "INVALID INTRADAY DATA" if rejection_reason else "INTRADAY CONTEXT UNAVAILABLE"
            ),
            "Context rejection reason": rejection_reason,
            "Market Session": market_session,
        }

    latest_timestamp = completed.index[-1] + pd.Timedelta(minutes=1)
    freshness = intraday_context_freshness(latest_timestamp, now=evaluation_time)
    if freshness != "FRESH":
        return {
            **_CONTEXT_FIELDS,
            "Context status": "STALE INTRADAY CONTEXT",
            "Context freshness": freshness,
            "Context rejection reason": "Latest completed candle is stale.",
            "Market Session": market_session,
        }

    session_date = completed.index[-1].date()
    baselines = pd.DataFrame() if daily is None else daily.copy()
    if not baselines.empty:
        baselines = baselines.loc[
            [pd.Timestamp(index).date() < session_date for index in baselines.index]
        ]
        required = {"Close", "Volume"}
        if not required.issubset(baselines.columns):
            baselines = pd.DataFrame()
        else:
            baselines = baselines.loc[:, ["Close", "Volume"]].apply(pd.to_numeric, errors="coerce")
            baselines = baselines.replace([float("inf"), float("-inf")], float("nan"))
            baselines = baselines.dropna(subset=["Close", "Volume"])
            baselines = baselines.loc[(baselines["Close"] > 0) & (baselines["Volume"] >= 0)]
            baselines = baselines.tail(20)

    average_volume = float(baselines["Volume"].mean()) if not baselines.empty else None
    average_turnover = (
        float((baselines["Close"] * baselines["Volume"]).mean()) if not baselines.empty else None
    )
    context = intraday_market_context(
        completed,
        previous_close=(float(baselines["Close"].iloc[-1]) if not baselines.empty else None),
        average_daily_volume=average_volume,
        average_daily_turnover=average_turnover,
    )
    if not context:
        return {**_CONTEXT_FIELDS, "Market Session": market_session}
    return {
        **_CONTEXT_FIELDS,
        **context,
        "Context status": context.get("Context status", "INTRADAY CONTEXT UNAVAILABLE"),
        "Context freshness": freshness,
        "Context rejection reason": rejection_reason,
        "Market Session": market_session,
    }


def scan_watchlist(symbols: list[str], *, now: datetime | None = None) -> pd.DataFrame:
    """Analyze each saved symbol directly; do not substitute broad-universe movers."""
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    tickers = list(
        dict.fromkeys(ticker for symbol in symbols if (ticker := _normalize_ticker(symbol)))
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
                        intraday_frames.get(ticker), daily_frames.get(ticker), now=now
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
