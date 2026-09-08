from __future__ import annotations

from services.market_data.packet import MarketDataPacket
from services.market_data.provider import YahooFinanceDataProvider


class InstitutionalMarketDataAdapter:
    """
    EROS 3.0 canonical market-data adapter.

    The adapter no longer manufactures prices. It delegates acquisition to the
    real Yahoo Finance provider and preserves the provider's freshness/state
    metadata for the integrity and decision gates.
    """

    @staticmethod
    def fetch_market_data(symbol: str) -> MarketDataPacket:
        return YahooFinanceDataProvider.fetch_live_market_data(symbol)


__all__ = ["MarketDataPacket", "InstitutionalMarketDataAdapter"]
