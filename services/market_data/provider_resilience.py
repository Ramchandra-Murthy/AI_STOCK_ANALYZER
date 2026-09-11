from __future__ import annotations

import logging

from services.market_data.adapter import MarketDataPacket
from services.market_data.integrity import (
    MarketDataIntegrityGate,
    MarketDataValidationReport,
)
from services.market_data.provider import YahooFinanceDataProvider

logger = logging.getLogger(__name__)


class ResilientMarketDataProvider:
    """Fetch provider data and enforce the market-data integrity boundary."""

    @staticmethod
    def get_validated_market_data(
        symbol: str,
    ) -> tuple[MarketDataPacket, MarketDataValidationReport]:
        """Return provider output together with its unmodified validation report."""
        normalized_symbol = symbol.strip().upper() if isinstance(symbol, str) else ""
        packet = YahooFinanceDataProvider.fetch_live_market_data(normalized_symbol)
        report = MarketDataIntegrityGate.validate_packet(packet)

        if not report.is_valid:
            logger.error(
                "Market data validation failed for %s: %s",
                normalized_symbol,
                report.errors,
            )

        return packet, report
