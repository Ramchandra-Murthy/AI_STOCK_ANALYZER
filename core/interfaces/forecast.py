from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict
import pandas as pd


class IForecastEngine(ABC):
    """Interface for projecting future financial statements and metrics."""

    @abstractmethod
    def project_statements(
        self,
        historical_financials: Dict[str, pd.DataFrame],
        periods: int = 5,
        assumptions: Dict[str, Any] = None,
    ) -> Dict[str, pd.DataFrame]:
        """Generate future income statements, balance sheets, and cash flows."""
        pass
