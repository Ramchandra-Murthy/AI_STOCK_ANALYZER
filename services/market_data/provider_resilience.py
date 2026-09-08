from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from services.market_data.packet import MarketDataPacket
from services.market_data.provider import YahooFinanceDataProvider
from services.market_data.integrity import (
    MarketDataIntegrityGate,
    MarketDataValidationReport,
)

logger = logging.getLogger(__name__)


class ResilientMarketDataProvider:
    """
    EROS 3.0 Block 23E resilient provider.

    Resilience means preserving an explicit unavailable/invalid state; it does
    not mean manufacturing a replacement market price.
    """

    @staticmethod
    def get_validated_market_data(
        symbol: str,
        ticker_factory: Optional[Callable[[str], Any]] = None,
    ) -> tuple[MarketDataPacket, MarketDataValidationReport]:
        packet = YahooFinanceDataProvider.fetch_live_market_data(
            symbol,
            ticker_factory=ticker_factory,
        )
        report = MarketDataIntegrityGate.validate_packet(packet)

        if not report.is_valid:
            logger.error(
                "Market data validation failed for %s: state=%s errors=%s",
                symbol,
                report.data_state,
                report.errors,
            )

        return packet, report


__all__ = ["ResilientMarketDataProvider"]
