from __future__ import annotations

import logging
from typing import List

logger = logging.getLogger(__name__)


class CAGRCalculator:
    """Calculates Compound Annual Growth Rate and projects future values."""

    def calculate_cagr(self, start_value: float, end_value: float, periods: int) -> float:
        if periods <= 0 or start_value <= 0:
            return 0.10 # Default 10% baseline growth
        return (end_value / start_value) ** (1 / periods) - 1

    def project(self, last_value: float, cagr: float, periods: int = 5) -> List[float]:
        projections = []
        current = last_value
        for _ in range(periods):
            current *= (1 + cagr)
            projections.append(current)
        return projections
