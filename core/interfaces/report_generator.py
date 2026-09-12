from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ReportGenerator(ABC):
    @abstractmethod
    def generate_report(self, symbol: str, data: dict[str, Any]) -> str:
        """Generate a structured report and return its path or contents."""
        pass
