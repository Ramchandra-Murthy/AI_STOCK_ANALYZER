from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class MarketDataPacket:
    symbol: str
    current_price: float | None
    previous_close: float | None
    volume: int | None
    ohlcv_history: list[dict[str, Any]]
    freshness_timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    is_stale: bool = False
    details: dict[str, Any] = field(default_factory=dict)


class InstitutionalMarketDataAdapter:
    """Compatibility adapter; never manufactures unknown market prices."""

    @staticmethod
    def fetch_market_data(symbol: str) -> MarketDataPacket:
        normalized_symbol = symbol.strip().upper() if isinstance(symbol, str) else ""
        if not normalized_symbol:
            return MarketDataPacket(
                symbol="",
                current_price=None,
                previous_close=None,
                volume=None,
                ohlcv_history=[],
                details={"source": "compatibility-adapter", "error": "symbol is required"},
            )

        return MarketDataPacket(
            symbol=normalized_symbol,
            current_price=None,
            previous_close=None,
            volume=None,
            ohlcv_history=[],
            details={
                "source": "compatibility-adapter",
                "status": "NO_LIVE_PROVIDER_CONFIGURED",
            },
        )
