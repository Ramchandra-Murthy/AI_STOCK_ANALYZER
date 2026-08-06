from __future__ import annotations

import logging
from typing import List

logger = logging.getLogger(__name__)


class ExponentialForecaster:
    """Projects future values using exponential curve fitting and continuous compounding growth."""

    def project(self, historical_values: List[float], growth_rate: float = 0.12, periods: int = 5) -> List[float]:
        base = historical_values[-1] if historical_values else 1000.0
        projections = []
        for i in range(periods):
            val = base * ((1 + growth_rate) ** (i + 1))
            projections.append(val)
        return projections
