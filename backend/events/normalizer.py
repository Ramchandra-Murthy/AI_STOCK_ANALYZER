from __future__ import annotations

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class CanonicalEventNormalizer:
    """Normalizes heterogeneous provider payloads into a unified MarketQuoteEvent schema."""

    @staticmethod
    def normalize_quote(raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        symbol = raw_payload.get("symbol") or raw_payload.get("ticker", "UNKNOWN")
        price = float(raw_payload.get("price") or raw_payload.get("last", 0.0))
        volume = int(raw_payload.get("volume") or raw_payload.get("qty", 0))
        timestamp = raw_payload.get("timestamp") or datetime.utcnow().isoformat()
        provider = raw_payload.get("provider", "unknown")

        return {
            "symbol": symbol.upper(),
            "price": price,
            "volume": volume,
            "timestamp": timestamp,
            "provider": provider.lower(),
            "normalized": True
        }