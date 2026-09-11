"""
==========================================================
FORECAST INPUT DOMAIN MODEL
Module  : services.forecast.forecast_input
Version : 5.1.0
Layer   : Services / Forecast / Input
==========================================================
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from services.forecast.exceptions import ValuationError
from services.forecast.forecast_models import ForecastMethod

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class HistoricalFinancials:
    """Container for historical financial time-series data."""

    revenue: tuple[float, ...]
    ebitda: tuple[float, ...] = field(default_factory=tuple)
    capex: tuple[float, ...] = field(default_factory=tuple)
    depreciation: tuple[float, ...] = field(default_factory=tuple)
    nwc: tuple[float, ...] = field(default_factory=tuple)


@dataclass(slots=True, frozen=True)
class ScenarioOverrides:
    """Container for scenario-specific growth and margin overrides."""

    revenue_growth_override: tuple[float, ...] | None = None
    margin_override: tuple[float, ...] | None = None


@dataclass(slots=True, frozen=True)
class ForecastInput:
    """
    Immutable domain payload supplied to the Forecast Engine.
    Supports both nested domain objects and legacy flat keyword arguments.
    """

    symbol: str = "GENERIC"
    historical_data: HistoricalFinancials | None = None
    forecast_horizon: int = 5

    # Direct flat/legacy parameter accessors
    historical_revenues: tuple[float, ...] = field(default_factory=tuple)
    historical_ebits: tuple[float, ...] = field(default_factory=tuple)
    historical_nwc: tuple[float, ...] = field(default_factory=tuple)
    historical_capex: tuple[float, ...] = field(default_factory=tuple)
    historical_depreciation: tuple[float, ...] = field(default_factory=tuple)
    forecast_years: int = 5
    method: ForecastMethod = ForecastMethod.CAGR
    management_guidance_revenue: tuple[float, ...] | None = None
    scenario_overrides: ScenarioOverrides | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalizes and validates input state upon instantiation."""

        # 1. Symbol validation
        if not self.symbol or not isinstance(self.symbol, str) or not self.symbol.strip():
            raise ValuationError("Ticker symbol cannot be empty.")

        # 2. Extract and freeze revenue series from flat arg or sub-container
        revs = self.historical_revenues
        if not revs and self.historical_data and self.historical_data.revenue:
            revs = self.historical_data.revenue

        revs_tuple = tuple(revs)
        if len(revs_tuple) < 2:
            raise ValuationError("Historical revenues must contain at least 2 periods.")

        # 3. Horizon validation & sync
        horizon = self.forecast_years if self.forecast_years != 5 else self.forecast_horizon
        if horizon < 1 or horizon > 10:
            raise ValuationError(f"Forecast horizon ({horizon}) must be between 1 and 10 years.")

        # 4. Series length checks
        ebits_tuple = tuple(self.historical_ebits)
        if ebits_tuple and len(ebits_tuple) != len(revs_tuple):
            raise ValuationError(
                f"historical_ebits length ({len(ebits_tuple)}) must match historical_revenues length ({len(revs_tuple)})."
            )

        # 5. Guidance validation
        if self.management_guidance_revenue is not None:
            guidance_tuple = tuple(self.management_guidance_revenue)
            if len(guidance_tuple) != horizon:
                raise ValuationError(
                    f"management_guidance_revenue length ({len(guidance_tuple)}) must match forecast_years ({horizon})."
                )
            object.__setattr__(self, "management_guidance_revenue", guidance_tuple)

        # Freeze synchronized tuple states
        object.__setattr__(self, "historical_revenues", revs_tuple)
        object.__setattr__(self, "historical_ebits", ebits_tuple)
        object.__setattr__(self, "historical_nwc", tuple(self.historical_nwc))
        object.__setattr__(self, "historical_capex", tuple(self.historical_capex))
        object.__setattr__(self, "historical_depreciation", tuple(self.historical_depreciation))
        object.__setattr__(self, "forecast_horizon", horizon)
        object.__setattr__(self, "forecast_years", horizon)

        # Construct or align historical_data container
        if self.historical_data is None:
            object.__setattr__(
                self,
                "historical_data",
                HistoricalFinancials(
                    revenue=revs_tuple,
                    ebitda=ebits_tuple,
                    capex=self.historical_capex,
                    depreciation=self.historical_depreciation,
                    nwc=self.historical_nwc,
                ),
            )
