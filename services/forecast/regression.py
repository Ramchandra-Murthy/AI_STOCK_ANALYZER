from __future__ import annotations

import math


class RegressionForecaster:
    """Project future values using least-squares linear regression."""

    def project(self, historical_values: list[float], periods: int = 5) -> list[float]:
        if periods < 0:
            raise ValueError("periods must be non-negative")
        if len(historical_values) < 2:
            raise ValueError("at least two historical values are required")

        y = [float(value) for value in historical_values]
        if any(not math.isfinite(value) for value in y):
            raise ValueError("historical values must be finite")

        n = len(y)
        x = list(range(n))
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator = sum((value - mean_x) ** 2 for value in x)
        slope = numerator / denominator
        intercept = mean_y - slope * mean_x

        projections: list[float] = []
        for index in range(periods):
            future_x = n + index
            value = intercept + slope * future_x
            projections.append(max(0.0, value))
        return projections
