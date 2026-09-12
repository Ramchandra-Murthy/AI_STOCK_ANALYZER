from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ForecastEngine(ABC):
    @abstractmethod
    def forecast(self, symbol: str) -> dict[str, Any]:
        """Run the forecasting model and return structured results."""
        pass
