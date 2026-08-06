from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True, slots=True)
class PriceRecord:
    """Represents a single daily price record."""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass(frozen=True, slots=True)
class MarketDataResponse:
    """Structured response for market data retrieval."""
    symbol: str
    source: str
    records: List[PriceRecord] = field(default_factory=list)
