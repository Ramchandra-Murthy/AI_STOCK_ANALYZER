from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True, slots=True)
class MarketDataPacket:
    """Canonical market-data packet shared by EROS market-data adapters."""

    symbol: str
    current_price: float
    previous_close: float
    volume: int
    ohlcv_history: List[Dict[str, Any]]
    freshness_timestamp: str
    is_stale: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


__all__ = ["MarketDataPacket"]
