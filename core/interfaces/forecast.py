from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, runtime_checkable

import pandas as pd


@runtime_checkable
class IForecastEngine(ABC):
    """Interface for projecting future financial statements and metrics."""

    @abstractmethod
    async def project_statements(
        self,
        historical_financials: dict[str, pd.DataFrame],
        periods: int = 5,
        assumptions: dict[str, Any] | None = None,
    ) -> dict[str, pd.DataFrame]:
        """Generate future income statements, balance sheets, and cash flows asynchronously."""
        pass
