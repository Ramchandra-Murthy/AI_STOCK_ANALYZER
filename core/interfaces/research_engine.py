from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

class ResearchEngine(ABC):
    @abstractmethod
    def analyze(self, symbol: str) -> dict[str, Any]:
        """Run the research pipeline and return structured results."""
        pass
