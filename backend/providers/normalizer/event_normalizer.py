from __future__ import annotations

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class EventNormalizer:
    """Normalizes disparate provider payloads into a unified EROS institutional event schema."""
    
    @staticmethod
    def normalize_quote(raw_payload: Dict[str, Any], provider_name: str) -> Dict[str, Any]:
        try:
            symbol = raw_payload.get("symbol") or raw_payload.get("ticker", "UNKNOWN")
            price = float(raw_payload.get("price") or raw_payload.get("last", 0.0))
            volume = int(raw_payload.get("volume") or raw_payload.get("qty", 0))
            timestamp = raw_payload.get("timestamp") or datetime.utcnow().isoformat()

            normalized = {
                "symbol": symbol.upper(),
                "price": price,
                "volume": volume,
                "timestamp": timestamp,
                "provider": provider_name,
                "normalized": True
            }
            logger.info("Successfully normalized quote for %s from provider %s", symbol, provider_name)
            return normalized
        except Exception as e:
            logger.error("Failed to normalize payload from %s: %s", provider_name, e)
            raise ValueError(f"Event normalization error: {e}")