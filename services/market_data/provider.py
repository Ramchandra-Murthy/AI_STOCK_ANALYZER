from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from services.market_data.packet import MarketDataPacket

logger = logging.getLogger(__name__)

ENGINE_VERSION = "EROS-3.0-BLOCK-23C-REPAIRED"


def _utc_iso(value: Any) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        dt = value.to_pydatetime() if hasattr(value, "to_pydatetime") else value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


class YahooFinanceDataProvider:
    """
    Canonical real-market provider for EROS.

    Important safety rule:
      - No fabricated price is ever returned as market data.
      - A provider failure becomes an unavailable/invalid packet.
      - Historical fallback data is not silently promoted to LIVE.

    yfinance is used as the external market-data source. Its fast_info API is
    used for the latest available price where possible, with recent intraday
    history supplying the freshness timestamp and previous close.
    """

    @staticmethod
    def fetch_live_market_data(
        symbol: str,
        ticker_factory: Optional[Callable[[str], Any]] = None,
    ) -> MarketDataPacket:
        normalized = str(symbol).strip().upper()
        if not normalized:
            return YahooFinanceDataProvider._unavailable_packet(
                normalized, "Empty market symbol"
            )

        try:
            import yfinance as yf

            factory = ticker_factory or yf.Ticker
            ticker = factory(normalized)

            # Recent intraday data is deliberately used for freshness. Yahoo
            # documents 1m data as available only for a limited recent window.
            intraday = ticker.history(
                period="1d",
                interval="1m",
                prepost=False,
                auto_adjust=False,
                repair=True,
                timeout=10,
            )

            if intraday is None or intraday.empty:
                raise ValueError("No intraday market data returned")

            intraday = intraday.dropna(subset=["Close"])
            if intraday.empty:
                raise ValueError("Intraday market data contains no valid close")

            latest_row = intraday.iloc[-1]
            latest_close = float(latest_row["Close"])
            if not math.isfinite(latest_close) or latest_close <= 0:
                raise ValueError(f"Invalid latest market price: {latest_close}")

            previous_close = latest_close
            volume = 0

            try:
                fast_info = ticker.fast_info
                fast_price = fast_info.get("last_price")
                if fast_price is not None:
                    fast_price = float(fast_price)
                    if math.isfinite(fast_price) and fast_price > 0:
                        latest_close = fast_price
                prev = fast_info.get("previous_close")
                if prev is not None:
                    prev = float(prev)
                    if math.isfinite(prev) and prev > 0:
                        previous_close = prev
            except Exception:
                # Intraday history remains the source of truth if fast_info is
                # unavailable; do not invent a value.
                pass

            if len(intraday) >= 2 and previous_close == latest_close:
                prev_row = intraday.iloc[-2]
                prev_close = float(prev_row["Close"])
                if math.isfinite(prev_close) and prev_close > 0:
                    previous_close = prev_close

            if "Volume" in intraday.columns:
                raw_volume = latest_row["Volume"]
                if raw_volume is not None and math.isfinite(float(raw_volume)):
                    volume = max(0, int(raw_volume))

            history = []
            for date_idx, row in intraday.tail(120).iterrows():
                close = float(row["Close"])
                if not math.isfinite(close) or close <= 0:
                    continue
                raw_volume = row.get("Volume", 0)
                row_volume = (
                    max(0, int(raw_volume))
                    if raw_volume is not None and math.isfinite(float(raw_volume))
                    else 0
                )
                history.append(
                    {
                        "date": _utc_iso(date_idx),
                        "close": close,
                        "volume": row_volume,
                    }
                )

            freshness = _utc_iso(intraday.index[-1])

            return MarketDataPacket(
                symbol=normalized,
                current_price=latest_close,
                previous_close=previous_close,
                volume=volume,
                ohlcv_history=history,
                freshness_timestamp=freshness,
                is_stale=False,
                details={
                    "source": "yfinance-live-api",
                    "provider": "YahooFinanceDataProvider",
                    "currency": "INR",
                    "engine_version": ENGINE_VERSION,
                },
            )

        except Exception as exc:
            logger.warning("Live market fetch failed for %s: %s", normalized, exc)
            return YahooFinanceDataProvider._unavailable_packet(normalized, str(exc))

    @staticmethod
    def _unavailable_packet(symbol: str, error: str) -> MarketDataPacket:
        return MarketDataPacket(
            symbol=symbol,
            current_price=0.0,
            previous_close=0.0,
            volume=0,
            ohlcv_history=[],
            freshness_timestamp=datetime.now(timezone.utc).isoformat(),
            is_stale=True,
            details={
                "source": "market-data-unavailable",
                "provider": "YahooFinanceDataProvider",
                "error": error,
                "engine_version": ENGINE_VERSION,
            },
        )


__all__ = ["ENGINE_VERSION", "YahooFinanceDataProvider"]
