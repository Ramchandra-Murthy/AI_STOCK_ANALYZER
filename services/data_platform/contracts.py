from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class QualityCheckResult:
    metric_name: str
    value: float | str
    passed: bool
    confidence: float
    message: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class FinancialProvider(ABC):
    """Abstract interface contract for all institutional data providers (Yahoo, NSE, BSE, Screener, etc.)."""

    @abstractmethod
    def download_financials(self, symbol: str) -> dict[str, Any]:
        pass

    @abstractmethod
    def download_prices(self, symbol: str) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def download_actions(self, symbol: str) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def validate_data(self, data: dict[str, Any]) -> QualityCheckResult:
        pass
