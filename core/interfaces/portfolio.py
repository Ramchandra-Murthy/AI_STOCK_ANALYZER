from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class IPortfolioManager(ABC):
    """Interface for portfolio analytics, position tracking, and allocation modeling."""

    @abstractmethod
    def calculate_metrics(
        self, holdings: List[Dict[str, Any]], benchmark_returns: Any
    ) -> Dict[str, Any]:
        """Calculate portfolio performance metrics (Sharpe, Alpha, Beta, Drawdown)."""
        pass

    @abstractmethod
    def optimize_allocation(
        self, symbols: List[str], constraints: Dict[str, Any]
    ) -> Dict[str, float]:
        """Compute optimal asset weights based on target strategies."""
        pass
