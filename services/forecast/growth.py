from __future__ import annotations

import math


class ExponentialForecaster:
    """Project future values from the historical geometric growth rate."""

    def project(self, historical_values: list[float], periods: int = 5) -> list[float]:
        if periods <= 0:
            return []
        if len(historical_values) < 2:
            raise ValueError("at least two historical values are required")
        values = [float(value) for value in historical_values]
        base = values[-1]
        if base <= 0 or any(not math.isfinite(value) for value in values):
            raise ValueError("historical values must be finite and the latest value positive")
        start = values[0]
        if start <= 0:
            raise ValueError("the first historical value must be positive")
        growth_rate = (base / start) ** (1.0 / (len(values) - 1)) - 1.0
        if not math.isfinite(growth_rate) or growth_rate <= -1.0:
            raise ValueError("historical values do not define a valid geometric growth rate")
        return [base * ((1.0 + growth_rate) ** (index + 1)) for index in range(periods)]
