from __future__ import annotations

from dataclasses import dataclass

from core.events.event import BaseDomainEvent


@dataclass(frozen=True, slots=True)
class ForecastCompleted(BaseDomainEvent):
    """Event emitted when financial forecasting is completed."""

    name: str = "forecast.completed"
