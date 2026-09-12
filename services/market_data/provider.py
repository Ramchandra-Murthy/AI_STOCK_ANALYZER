from __future__ import annotations

import logging
from datetime import UTC, datetime
from math import isfinite

from services.market_data.adapter import MarketDataPacket

logger = logging.getLogger(__name__)


class YahooFinanceDataProvider:
    """Fetch provider-backed market data and fail closed on invalid responses."""

    @staticmethod
    def fetch_live_market_data(symbol: str) -> MarketDataPacket:
        normalized_symbol = symbol.strip().upper() if isinstance(symbol, str) else ""
        now = datetime.now(UTC).isoformat()
        if not normalized_symbol:
            return MarketDataPacket(
                symbol="",
                current_price=None,
                previous_close=None,
                volume=None,
                ohlcv_history=[],
                freshness_timestamp=now,
                is_stale=True,
                details={
                    "source": "provider-error",
                    "error": "symbol is required",
                    "currency": "INR",
                },
            )
        try:
            import yfinance as yf

            hist = yf.Ticker(normalized_symbol).history(period="5d", auto_adjust=False)
            if hist.empty or "Close" not in hist.columns:
                raise ValueError(f"No usable price history returned for {normalized_symbol}")

            closes = [float(v) for v in hist["Close"].tolist() if isfinite(float(v))]
            if not closes or closes[-1] <= 0:
                raise ValueError(f"Invalid close price returned for {normalized_symbol}")
            current_price = closes[-1]
            previous_close = closes[-2] if len(closes) >= 2 and closes[-2] > 0 else None

            volume = None
            if "Volume" in hist.columns:
                raw_volume = hist["Volume"].iloc[-1]
                if isfinite(float(raw_volume)) and float(raw_volume) >= 0:
                    volume = int(raw_volume)

            ohlcv_history: list[dict[str, float | str | int]] = []
            for date_idx, row in hist.iterrows():
                close = float(row["Close"])
                if not isfinite(close) or close <= 0:
                    continue
                raw_volume = row["Volume"] if "Volume" in hist.columns else 0
                row_volume = (
                    int(raw_volume) if isfinite(float(raw_volume)) and float(raw_volume) >= 0 else 0
                )
                ohlcv_history.append(
                    {"date": str(date_idx.date()), "close": close, "volume": row_volume}
                )
            if not ohlcv_history:
                raise ValueError(f"No valid OHLCV rows returned for {normalized_symbol}")

            return MarketDataPacket(
                symbol=normalized_symbol,
                current_price=current_price,
                previous_close=previous_close,
                volume=volume,
                ohlcv_history=ohlcv_history,
                freshness_timestamp=now,
                is_stale=False,
                details={"source": "yfinance-live-api", "currency": "INR"},
            )
        except Exception as exc:
            logger.warning("Live data fetch failed for %s: %s", normalized_symbol, exc)
            return MarketDataPacket(
                symbol=normalized_symbol,
                current_price=None,
                previous_close=None,
                volume=None,
                ohlcv_history=[],
                freshness_timestamp=now,
                is_stale=True,
                details={
                    "source": "provider-error",
                    "error": str(exc),
                    "currency": "INR",
                },
            )
