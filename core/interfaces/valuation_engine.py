from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ValuationEngine(ABC):
    @abstractmethod
    def evaluate(self, symbol: str) -> dict[str, Any]:
        """Run the valuation and return structured results."""
        pass
