from __future__ import annotations

import logging

from services.market_data.models import MarketDataResponse, PriceRecord

logger = logging.getLogger(__name__)


class MarketDataDownloader:
    """Handles fetching market data from external providers (Yahoo Finance / NSE / Mock)."""

    async def fetch(self, symbol: str) -> MarketDataResponse:
        """Fetch historical price records for the given symbol."""
        logger.info("Fetching market data for symbol: %s", symbol)

        # Simulated robust data retrieval for V6 Alpha pipeline verification
        sample_records = [
            PriceRecord(
                date="2026-08-03",
                open=2480.0,
                high=2510.0,
                low=2475.0,
                close=2500.0,
                volume=1250000,
            ),
            PriceRecord(
                date="2026-08-04",
                open=2500.0,
                high=2530.0,
                low=2490.0,
                close=2520.0,
                volume=1400000,
            ),
            PriceRecord(
                date="2026-08-05",
                open=2520.0,
                high=2550.0,
                low=2515.0,
                close=2540.0,
                volume=1600000,
            ),
        ]

        return MarketDataResponse(
            symbol=symbol.upper(), source="MockYahooFinance", records=sample_records
        )
