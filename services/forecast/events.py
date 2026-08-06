from __future__ import annotations

from dataclasses import dataclass
from core.events.event import BaseEvent


@dataclass(frozen=True, slots=True)
class ForecastCompleted(BaseEvent):
    """Event published when financial forecasts are successfully computed."""
    symbol: str = ""
    model_type: str = ""
    name: str = "forecast.completed"
