from __future__ import annotations

from dataclasses import dataclass
from core.events.event import BaseDomainEvent


@dataclass(frozen=True, slots=True)
class MarketDataDownloaded(BaseDomainEvent):
    """Event emitted when market data is successfully downloaded/retrieved."""
    name: str = "market.data.downloaded"
