from __future__ import annotations

import logging
from datetime import datetime, timezone

from services.market_data.adapter import MarketDataPacket

logger = logging.getLogger(__name__)


class YahooFinanceDataProvider:
    """Fetch live market data and fail closed when no trustworthy fallback exists."""

    @staticmethod
    def fetch_live_market_data(symbol: str) -> MarketDataPacket:
        normalized_symbol = symbol.strip().upper() if isinstance(symbol, str) else ""
        try:
            import yfinance as yf

            ticker = yf.Ticker(normalized_symbol)
            hist = ticker.history(period="5d")
            if hist.empty:
                raise ValueError(
                    f"No price history returned for symbol {normalized_symbol}"
                )

            current_price = float(hist["Close"].iloc[-1])
            previous_close = (
                float(hist["Close"].iloc[-2])
                if len(hist) >= 2
                else current_price
            )
            volume_value = hist["Volume"].iloc[-1]
            volume = int(volume_value) if volume_value == volume_value else None

            ohlcv_history = [
                {
                    "date": str(date_idx.date()),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                }
                for date_idx, row in hist.iterrows()
            ]

            return MarketDataPacket(
                symbol=normalized_symbol,
                current_price=current_price,
                previous_close=previous_close,
                volume=volume,
                ohlcv_history=ohlcv_history,
                freshness_timestamp=datetime.now(timezone.utc).isoformat(),
                is_stale=False,
                details={"source": "yfinance-live-api", "currency": "INR"},
            )
        except Exception as exc:
            logger.warning(
                "Live data fetch failed for %s: %s",
                normalized_symbol,
                exc,
            )
            # Never substitute invented prices. A failed provider produces an
            # invalid packet so the integrity gate can reject it explicitly.
            return MarketDataPacket(
                symbol=normalized_symbol,
                current_price=None,
                previous_close=None,
                volume=None,
                ohlcv_history=[],
                freshness_timestamp=datetime.now(timezone.utc).isoformat(),
                is_stale=True,
                details={
                    "source": "provider-error",
                    "error": str(exc),
                    "currency": "INR",
                },
            )
