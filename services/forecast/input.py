from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from services.forecast.assumption_engine import ManagementGuidance


@dataclass(frozen=True, slots=True)
class ForecastInput:
    """Input payload containing historical financials and configuration for forecasting."""

    ticker: str
    historical_years: tuple[int, ...]
    historical_revenue: tuple[float, ...]
    historical_margins: tuple[float, ...]
    historical_capex: tuple[float, ...]
    historical_depreciation: tuple[float, ...]
    historical_working_capital: tuple[float, ...]
    historical_taxes: tuple[float, ...]
    forecast_years: tuple[int, ...]
    custom_growth_rate: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    tax_rate_assumption: float | None = None
    ebit_margin_assumption: float | None = None
    capex_pct_revenue_assumption: float | None = None
    working_capital_pct_revenue_assumption: float | None = None
    management_guidance: ManagementGuidance | None = None
