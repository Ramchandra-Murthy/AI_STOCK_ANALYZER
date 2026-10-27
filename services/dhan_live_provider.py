"""Dhan-backed read-only intraday market-data provider for live scanners."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from services.dhan_market_data import DhanCredentials, DhanMarketData

_IST = timezone(timedelta(hours=5, minutes=30))


def _security_map() -> dict[str, int]:
    raw = os.getenv("DHAN_SECURITY_MAP_JSON", "").strip()
    if not raw:
        try:
            import streamlit as st

            raw = str(st.secrets.get("DHAN_SECURITY_MAP_JSON", "")).strip()
        except Exception:
            raw = ""
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    result: dict[str, int] = {}
    for symbol, security_id in parsed.items():
        try:
            result[str(symbol).strip().upper()] = int(security_id)
        except (TypeError, ValueError):
            continue
    return result


def dhan_provider_enabled() -> bool:
    """Return True only when Dhan credentials and an instrument map are configured."""
    try:
        DhanCredentials.from_env()
    except Exception:
        return False
    return bool(_security_map())


def _response_frame(response: dict[str, Any]) -> pd.DataFrame:
    """Convert Dhan's column-oriented candle response or raise on API failures."""
    if not isinstance(response, dict):
        raise ValueError("Dhan returned a non-object response")
    status = str(response.get("status", "")).strip().lower()
    if status and status not in {"success", "ok"}:
        details = (
            response.get("remarks")
            or response.get("errorMessage")
            or response.get("message")
            or response.get("error_code")
            or "no error details"
        )
        raise ValueError(f"Dhan API status={status}: {str(details)[:180]}")
    data = response.get("data", response)
    if not isinstance(data, dict):
        raise ValueError("Dhan response has no candle data object")
    timestamps = data.get("timestamp", [])
    closes = data.get("close", [])
    opens = data.get("open", [])
    highs = data.get("high", [])
    lows = data.get("low", [])
    volumes = data.get("volume", [])
    if not timestamps or not closes:
        raise ValueError("Dhan response contains no intraday candles")
    size = min(len(timestamps), len(closes))
    frame = pd.DataFrame(
        {
            "Open": list(opens)[:size],
            "High": list(highs)[:size],
            "Low": list(lows)[:size],
            "Close": list(closes)[:size],
            "Volume": list(volumes)[:size],
        }
    )
    timestamp_values = list(timestamps)[:size]
    if all(isinstance(value, (int, float)) for value in timestamp_values):
        index = pd.to_datetime(timestamp_values, unit="s", utc=True).tz_convert(_IST)
    else:
        index = pd.to_datetime(timestamp_values, utc=True, errors="coerce").tz_convert(_IST)
    frame.index = index
    frame["Close"] = pd.to_numeric(frame["Close"], errors="coerce")
    frame = frame.dropna(subset=["Close"])
    if frame.empty:
        raise ValueError("Dhan response contains no valid closing prices")
    return frame.sort_index()


def _security_id_for_ticker(ticker: str, mapping: dict[str, int]) -> int | None:
    """Resolve exchange-specific keys before allowing a legacy NSE-only symbol key."""
    normalized = ticker.strip().upper()
    symbol, dot, suffix = normalized.rpartition(".")
    if not dot:
        symbol, suffix = normalized, ""
    exchange = "NSE" if suffix == "NS" else "BSE" if suffix == "BO" else ""
    for key in (normalized, f"{exchange}:{symbol}", f"{exchange}_{symbol}"):
        if key in mapping:
            return mapping[key]
    # Backward compatibility: unqualified symbol IDs are assumed NSE only.
    # BSE must use a BSE-qualified key because IDs differ by exchange.
    return mapping.get(symbol) if exchange == "NSE" else None


def download_dhan_symbol_frames(
    tickers: list[str],
    *,
    interval: int = 1,
) -> tuple[dict[str, pd.DataFrame], list[str]]:
    """Download recent Dhan candles for mapped NSE/BSE tickers."""
    mapping = _security_map()
    if not mapping or not dhan_provider_enabled():
        return {}, list(tickers)

    client = DhanMarketData()
    now = datetime.now(_IST)
    from_date = (now - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
    to_date = now.strftime("%Y-%m-%d %H:%M:%S")
    frames: dict[str, pd.DataFrame] = {}
    missing: list[str] = []

    for ticker in tickers:
        security_id = _security_id_for_ticker(ticker, mapping)
        if security_id is None:
            logging.info(
                "Dhan instrument mapping missing ticker=%s; expected an exchange-qualified "
                "key such as NSE:%s or BSE:%s",
                ticker,
                ticker.rsplit(".", 1)[0].upper(),
                ticker.rsplit(".", 1)[0].upper(),
            )
            missing.append(ticker)
            continue
        exchange_segment = "NSE_EQ" if ticker.endswith(".NS") else "BSE_EQ"
        try:
            response = client.intraday_minute_data(
                security_id,
                exchange_segment,
                "EQUITY",
                from_date,
                to_date,
                interval=interval,
            )
            frame = _response_frame(response)
        except Exception as exc:
            # Keep provider failures visible in deployment logs without exposing credentials.
            logging.warning(
                "Dhan intraday quote failed ticker=%s error_type=%s error=%s",
                ticker,
                type(exc).__name__,
                str(exc)[:240],
            )
            frame = pd.DataFrame()
        if frame.empty:
            missing.append(ticker)
        else:
            frames[ticker] = frame

    return frames, missing
