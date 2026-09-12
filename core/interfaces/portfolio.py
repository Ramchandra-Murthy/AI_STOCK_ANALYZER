from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, runtime_checkable


@runtime_checkable
class IPortfolioManager(ABC):
    """Interface for portfolio analytics, position tracking, and allocation modeling."""

    @abstractmethod
    async def calculate_metrics(
        self, holdings: list[dict[str, Any]], benchmark_returns: Any
    ) -> dict[str, Any]:
        """Calculate portfolio performance metrics (Sharpe, Alpha, Beta, Drawdown) asynchronously."""
        pass

    @abstractmethod
    async def optimize_allocation(
        self, symbols: list[str], constraints: dict[str, Any]
    ) -> dict[str, float]:
        """Compute optimal asset weights asynchronously based on target strategies."""
        pass
