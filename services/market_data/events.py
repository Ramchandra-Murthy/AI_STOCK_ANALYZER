from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping
from core.events.event import BaseEvent


@dataclass(frozen=True, slots=True)
class MarketDataDownloaded(BaseEvent):
    """Event published when market data is successfully downloaded and cached."""
    symbol: str = ""
    records: int = 0
    source: str = ""
    name: str = "market.data.downloaded"
