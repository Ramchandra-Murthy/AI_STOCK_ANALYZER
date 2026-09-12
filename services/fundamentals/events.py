from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.events.event import BaseDomainEvent


@dataclass(frozen=True, slots=True)
class FundamentalsDownloaded(BaseDomainEvent):
    """Event emitted when company fundamental financial statements are successfully downloaded and normalized."""

    name: str = "fundamentals.downloaded"
    provider: str = "YahooFinance"
    timestamp: float = 0.0
    payload: dict[str, Any] = field(default_factory=dict)
