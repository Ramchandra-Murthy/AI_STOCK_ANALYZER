from __future__ import annotations

import logging
from typing import List

logger = logging.getLogger(__name__)


class RegressionForecaster:
    """Projects future values using Least Squares Linear Regression."""

    def project(self, historical_values: List[float], periods: int = 5) -> List[float]:
        n = len(historical_values)
        if n < 2:
            base = historical_values[-1] if historical_values else 1000.0
            return [base * (1 + 0.1 * (i + 1)) for i in range(periods)]

        x = list(range(n))
        y = historical_values
        mean_x = sum(x) / n
        mean_y = sum(y) / n

        num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        den = sum((x[i] - mean_x) ** 2 for i in range(n))

        slope = num / den if den != 0 else 0.0
        intercept = mean_y - slope * mean_x

        projections = []
        for i in range(periods):
            future_x = n + i
            val = intercept + slope * future_x
            projections.append(max(0.0, val))
        return projections
