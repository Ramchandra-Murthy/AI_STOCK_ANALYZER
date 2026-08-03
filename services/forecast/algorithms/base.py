"""
Module: services.forecast.algorithms.base
Description: Base protocol definition for institutional forecasting algorithms.
Author: Engineering Team
Python Version: 3.13+
"""

from __future__ import annotations

from typing import Protocol, Tuple, runtime_checkable


@runtime_checkable
class ForecastAlgorithmProtocol(Protocol):
    """Protocol defining the structural interface for pure mathematical forecasting engines."""

    def calculate(
        self, historical: Tuple[float, ...], periods: int, **kwargs: float
    ) -> Tuple[float, ...]:
        """Projects future time-series values based on historical data and algorithm-specific parameters."""
        ...
