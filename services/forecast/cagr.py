from __future__ import annotations

import math


class CAGRCalculator:
    """Calculate CAGR and project future values from validated inputs."""

    def calculate_cagr(self, start_value: float, end_value: float, periods: int) -> float:
        if periods <= 0:
            raise ValueError("periods must be positive")
        start = float(start_value)
        end = float(end_value)
        if not math.isfinite(start) or not math.isfinite(end):
            raise ValueError("start_value and end_value must be finite")
        if start <= 0 or end <= 0:
            raise ValueError("start_value and end_value must be positive")
        return (end / start) ** (1.0 / periods) - 1.0

    def project(self, last_value: float, cagr: float, periods: int = 5) -> list[float]:
        if periods < 0:
            raise ValueError("periods must be non-negative")
        current = float(last_value)
        rate = float(cagr)
        if not math.isfinite(current) or not math.isfinite(rate):
            raise ValueError("last_value and cagr must be finite")
        if current <= 0:
            raise ValueError("last_value must be positive")
        return [
            (current := current * (1.0 + rate))
            for _ in range(periods)
        ]
