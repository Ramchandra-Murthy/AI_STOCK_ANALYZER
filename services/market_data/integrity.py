from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List
from datetime import datetime, timezone
from services.market_data.adapter import MarketDataPacket

@dataclass(frozen=True, slots=True)
class MarketDataValidationReport:
    symbol: str
    data_state: str  # "LIVE", "FALLBACK", "STALE", "INVALID"
    is_valid: bool
    errors: List[str]
    freshness_age_seconds: float
    details: Dict[str, Any] = field(default_factory=dict)

class MarketDataIntegrityGate:
    """
    EROS 3.0 Block 23D Data Integrity Gate.
    Validates market data packets for price bounds, volume integrity, OHLCV completeness, and freshness.
    """
    @staticmethod
    def validate_packet(packet: MarketDataPacket, max_age_seconds: float = 86400.0) -> MarketDataValidationReport:
        errors: List[str] = []
        
        # 1. Check price validity
        if packet.current_price is None or packet.current_price <= 0.0:
            errors.append(f"Invalid current price: {packet.current_price}")

        # 2. Check volume validity
        if packet.volume is None or packet.volume < 0:
            errors.append(f"Invalid volume: {packet.volume}")

        # 3. Check OHLCV history completeness
        if not packet.ohlcv_history or len(packet.ohlcv_history) == 0:
            errors.append("OHLCV history is missing or empty.")

        # 4. Check freshness timestamp
        age_seconds = 0.0
        try:
            # Parse freshness timestamp
            dt = datetime.fromisoformat(packet.freshness_timestamp.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_seconds = (now - dt).total_seconds()
        except Exception:
            age_seconds = 0.0

        is_stale = packet.is_stale or age_seconds > max_age_seconds

        # Determine explicit data state
        if len(errors) > 0:
            state = "INVALID"
        elif is_stale or "fallback" in packet.details.get("source", "").lower():
            state = "FALLBACK" if "fallback" in packet.details.get("source", "").lower() else "STALE"
        else:
            state = "LIVE"

        is_valid = state in ("LIVE", "FALLBACK") and len(errors) == 0

        return MarketDataValidationReport(
            symbol=packet.symbol,
            data_state=state,
            is_valid=is_valid,
            errors=errors,
            freshness_age_seconds=round(age_seconds, 2),
            details={
                "engine_version": "EROS-3.0-BLOCK-23D",
                "source": packet.details.get("source", "unknown")
            }
        )
