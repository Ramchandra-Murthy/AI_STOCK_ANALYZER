from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from services.market_data.adapter import MarketDataPacket


@dataclass(frozen=True, slots=True)
class MarketDataValidationReport:
    symbol: str
    data_state: str
    is_valid: bool
    errors: list[str]
    freshness_age_seconds: float
    details: dict[str, Any] = field(default_factory=dict)


class MarketDataIntegrityGate:
    """Validate market-data bounds, history completeness, and freshness."""

    @staticmethod
    def validate_packet(
        packet: MarketDataPacket, max_age_seconds: float = 86400.0
    ) -> MarketDataValidationReport:
        errors: list[str] = []

        if packet.current_price is None or packet.current_price <= 0.0:
            errors.append(f"Invalid current price: {packet.current_price}")

        if packet.volume is None or packet.volume < 0:
            errors.append(f"Invalid volume: {packet.volume}")

        if not packet.ohlcv_history:
            errors.append("OHLCV history is missing or empty.")

        age_seconds = 0.0
        freshness = getattr(packet, "freshness_timestamp", None)
        if freshness:
            try:
                normalized = freshness.replace("Z", "+00:00")
                dt = datetime.fromisoformat(normalized)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                age_seconds = max(0.0, (datetime.now(UTC) - dt).total_seconds())
            except (TypeError, ValueError):
                errors.append("Invalid freshness timestamp.")

        source = str(packet.details.get("source", "unknown"))
        source_lower = source.lower()
        is_stale = bool(packet.is_stale) or age_seconds > max_age_seconds

        if errors:
            state = "INVALID"
        elif "fallback" in source_lower:
            state = "FALLBACK"
        elif is_stale:
            state = "STALE"
        else:
            state = "LIVE"

        return MarketDataValidationReport(
            symbol=packet.symbol,
            data_state=state,
            is_valid=state in {"LIVE", "FALLBACK"},
            errors=errors,
            freshness_age_seconds=round(age_seconds, 2),
            details={
                "engine_version": "EROS-3.0-BLOCK-23D",
                "source": source,
            },
        )
