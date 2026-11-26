"""
==========================================================
EQUITY VALUATION PLATFORM v5.1
Module  : services.forecast.forecast_result
Layer   : Services / Forecast / Output Contracts
Summary : Aggregated immutable output container for complete company
          financial forecasts.
==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from services.forecast.exceptions import ForecastValidationError
from services.forecast.forecast_models import (
    CapexForecast,
    DepreciationForecast,
    ForecastConfidence,
    ForecastScenario,
    MarginForecast,
    RevenueForecast,
    TaxForecast,
    TerminalGrowthForecast,
    WorkingCapitalForecast,
)


@dataclass(frozen=True, slots=True)
class YearlyFinancialForecast:
    """Individual annual forecast statement item."""

    year: int
    revenue: float
    margin: float
    ebit: float
    capex: float
    depreciation: float
    working_capital: float
    tax: float

    @property
    def tax_rate(self) -> float:
        """Explicit name for the tax-rate fraction retained in the legacy tax field."""
        return self.tax

    @property
    def tax_expense(self) -> float:
        """Tax expense in currency units: EBIT multiplied by the tax rate."""
        return round(self.ebit * self.tax_rate, 4)

    @property
    def free_cash_flow(self) -> float:
        """Calculates FCFF using tax expense, not the tax-rate fraction."""
        nopat = self.ebit - self.tax_expense
        return round(nopat + self.depreciation - self.capex - self.working_capital, 4)


@dataclass(frozen=True, slots=True)
class ForecastResult:
    """Master output contract containing complete financial projections for a valuation subject."""

    symbol: str
    revenue: RevenueForecast
    margin: MarginForecast
    capex: CapexForecast
    depreciation: DepreciationForecast
    working_capital: WorkingCapitalForecast
    tax: TaxForecast
    terminal_growth: TerminalGrowthForecast
    confidence: ForecastConfidence
    scenarios: tuple[ForecastScenario, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    # ----------------------------------------------------
    # Subservice Aliases & Compatibility Accessors
    # ----------------------------------------------------
    @property
    def revenue_forecast(self) -> RevenueForecast:
        return self.revenue

    @property
    def margin_forecast(self) -> MarginForecast:
        return self.margin

    @property
    def capex_forecast(self) -> CapexForecast:
        return self.capex

    @property
    def depreciation_forecast(self) -> DepreciationForecast:
        return self.depreciation

    @property
    def working_capital_forecast(self) -> WorkingCapitalForecast:
        return self.working_capital

    @property
    def tax_forecast(self) -> TaxForecast:
        return self.tax

    @property
    def forecast_years(self) -> int:
        """Returns projection horizon length."""
        return len(self.revenue.projected)

    # ----------------------------------------------------
    # Vector Property Accessors
    # ----------------------------------------------------
    @property
    def projected_revenues(self) -> tuple[float, ...]:
        """Direct accessor for projected revenue series."""
        return tuple(self.revenue.projected)

    @property
    def projected_ebit_margins(self) -> list[float]:
        """List accessor for projected EBIT margins matching legacy test expectations."""
        return [round(m, 4) for m in self.margin.projected]

    @property
    def projected_ebit(self) -> tuple[float, ...]:
        """Calculates projected EBIT series: Revenue * Margin."""
        return tuple(
            round(rev * margin, 4)
            for rev, margin in zip(self.revenue.projected, self.margin.projected, strict=False)
        )

    @property
    def projected_tax_expense(self) -> tuple[float, ...]:
        """Projected tax expense in currency units: EBIT multiplied by tax rate."""
        return tuple(
            round(ebit * rate, 4)
            for ebit, rate in zip(self.projected_ebit, self.tax.projected, strict=False)
        )

    @property
    def projected_nopat(self) -> tuple[float, ...]:
        """Calculates NOPAT as EBIT less projected tax expense."""
        return tuple(
            round(ebit - tax_expense, 4)
            for ebit, tax_expense in zip(
                self.projected_ebit, self.projected_tax_expense, strict=False
            )
        )

    @property
    def projected_fcff(self) -> tuple[float, ...]:
        """Calculates projected Free Cash Flow to Firm (FCFF): NOPAT + D&A - CapEx - Delta NWC."""
        nopats = self.projected_nopat
        deps = tuple(self.depreciation.projected)
        capex = tuple(self.capex.projected)
        delta_nwc = tuple(self.working_capital.delta)

        return tuple(
            round(nopat + dep - cap - dnwc, 4)
            for nopat, dep, cap, dnwc in zip(nopats, deps, capex, delta_nwc, strict=False)
        )

    @property
    def projected_fcfs(self) -> tuple[float, ...]:
        """Legacy alias accessor for projected FCFF."""
        return self.projected_fcff

    @property
    def yearly_forecasts(self) -> tuple[YearlyFinancialForecast, ...]:
        """Returns annual structured financial objects using the source forecast years."""
        series = {
            "revenue": self.revenue,
            "margin": self.margin,
            "capex": self.capex,
            "depreciation": self.depreciation,
            "working_capital": self.working_capital,
            "tax": self.tax,
        }
        forecast_years = tuple(self.revenue.years)
        for name, forecast in series.items():
            if tuple(forecast.years) != forecast_years:
                raise ForecastValidationError(
                    f"{name} forecast years must match revenue forecast years."
                )
            if len(forecast.projected) != len(forecast_years):
                raise ForecastValidationError(
                    f"{name} forecast values must match the forecast-year sequence."
                )

        ebits = self.projected_ebit
        yearly = []
        for index, year in enumerate(forecast_years):
            yearly.append(
                YearlyFinancialForecast(
                    year=year,
                    revenue=self.revenue.projected[index],
                    margin=self.margin.projected[index],
                    ebit=ebits[index],
                    capex=self.capex.projected[index],
                    depreciation=self.depreciation.projected[index],
                    working_capital=self.working_capital.delta[index],
                    tax=self.tax.projected[index],
                )
            )
        return tuple(yearly)
