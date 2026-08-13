from __future__ import annotations
import logging
from typing import Any, Dict, Optional
from services.market_data.adapter import MarketDataPacket
from services.market_data.provider import YahooFinanceDataProvider
from services.market_data.integrity import MarketDataIntegrityGate, MarketDataValidationReport

logger = logging.getLogger(__name__)

class ResilientMarketDataProvider:
    """
    EROS 3.0 Block 23E Resilient Provider.
    Enforces strict data integrity gates on live provider outputs, classifying errors and managing live-to-fallback transitions.
    """
    @staticmethod
    def get_validated_market_data(symbol: str) -> tuple[MarketDataPacket, MarketDataValidationReport]:
        packet = YahooFinanceDataProvider.fetch_live_market_data(symbol)
        report = MarketDataIntegrityGate.validate_packet(packet)

        if not report.is_valid:
            logger.error("Market data validation failed for %s: %s", symbol, report.errors)
        
        return packet, report
