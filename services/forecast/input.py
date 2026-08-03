"""
==========================================================
FORECAST INPUT NORMALIZATION & VALIDATION
Module  : services.forecast.input
Layer   : Domain / Forecast
==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, Dict, Any


@dataclass(frozen=True, slots=True)
class FinancialInputData:
    """Normalized container for historical financial statements."""

    company_ticker: str
    historical_revenue: Tuple[float, ...]
    historical_ebitda: Tuple[float, ...]
    historical_capex: Tuple[float, ...]
    historical_working_capital: Tuple[float, ...]
    historical_tax_rate: Tuple[float, ...]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Enforces basic structural invariants on input data."""
        if not self.company_ticker:
            raise ValueError("Company ticker must not be empty.")
        if len(self.historical_revenue) == 0:
            raise ValueError("Historical revenue series cannot be empty.")


# Alias for validation and confidence engines expecting ForecastInput
ForecastInput = FinancialInputData
