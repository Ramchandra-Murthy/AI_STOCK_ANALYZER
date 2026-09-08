from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from services.market_data.packet import MarketDataPacket


ENGINE_VERSION = "EROS-3.0-BLOCK-23D-REPAIRED"


@dataclass(frozen=True, slots=True)
class MarketDataValidationReport:
    symbol: str
    data_state: str
    is_valid: bool
    errors: List[str]
    freshness_age_seconds: float
    details: Dict[str, Any] = field(default_factory=dict)


class MarketDataIntegrityGate:
    """
    Strict market-data integrity boundary.

    LIVE means a positive price, valid volume/history, a usable freshness
    timestamp, and a non-stale provider packet. FALLBACK/STALE/INVALID data
    remains observable for diagnostics but is never considered valid input for
    live scoring.
    """

    @staticmethod
    def validate_packet(
        packet: MarketDataPacket,
        max_age_seconds: float = 900.0,
    ) -> MarketDataValidationReport:
        errors: List[str] = []

        if packet.current_price is None or packet.current_price <= 0.0:
            errors.append(f"Invalid current price: {packet.current_price}")

        if packet.previous_close is None or packet.previous_close <= 0.0:
            errors.append(f"Invalid previous close: {packet.previous_close}")

        if packet.volume is None or packet.volume < 0:
            errors.append(f"Invalid volume: {packet.volume}")

        if not packet.ohlcv_history:
            errors.append("OHLCV/intraday history is missing or empty.")

        age_seconds = float("inf")
        try:
            dt = datetime.fromisoformat(
                str(packet.freshness_timestamp).replace("Z", "+00:00")
            )
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_seconds = max(
                0.0,
                (datetime.now(timezone.utc) - dt).total_seconds(),
            )
        except Exception:
            errors.append("Freshness timestamp is missing or invalid.")

        source = str(packet.details.get("source", "")).lower()
        provider_failed = (
            source in {"", "market-data-unavailable"}
            or "fallback" in source
            or "mock" in source
            or "sample" in source
        )
        stale = bool(packet.is_stale) or age_seconds > max_age_seconds

        if provider_failed:
            state = "INVALID" if not packet.ohlcv_history else "FALLBACK"
        elif stale:
            state = "STALE"
        elif errors:
            state = "INVALID"
        else:
            state = "LIVE"

        # Only LIVE packets are valid for live scoring/execution decisions.
        is_valid = state == "LIVE" and not errors

        return MarketDataValidationReport(
            symbol=packet.symbol,
            data_state=state,
            is_valid=is_valid,
            errors=errors,
            freshness_age_seconds=(
                round(age_seconds, 2) if age_seconds != float("inf") else age_seconds
            ),
            details={
                "engine_version": ENGINE_VERSION,
                "source": packet.details.get("source", "unknown"),
                "max_age_seconds": max_age_seconds,
                "live_scoring_allowed": is_valid,
            },
        )


__all__ = [
    "ENGINE_VERSION",
    "MarketDataIntegrityGate",
    "MarketDataValidationReport",
]
