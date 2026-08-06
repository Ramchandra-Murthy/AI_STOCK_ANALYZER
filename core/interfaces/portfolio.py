from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, runtime_checkable


@runtime_checkable
class IPortfolioManager(ABC):
    """Interface for portfolio analytics, position tracking, and allocation modeling."""

    @abstractmethod
    async def calculate_metrics(
        self, holdings: List[Dict[str, Any]], benchmark_returns: Any
    ) -> Dict[str, Any]:
        """Calculate portfolio performance metrics (Sharpe, Alpha, Beta, Drawdown) asynchronously."""
        pass

    @abstractmethod
    async def optimize_allocation(
        self, symbols: List[str], constraints: Dict[str, Any]
    ) -> Dict[str, float]:
        """Compute optimal asset weights asynchronously based on target strategies."""
        pass
