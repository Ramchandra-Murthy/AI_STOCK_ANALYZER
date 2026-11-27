from __future__ import annotations

import math

from services.forecast.exceptions import ForecastConfigurationError, ForecastValidationError
from services.forecast.input import ForecastInput


class ForecastValidator:
    """Validates ForecastInput payloads for structural and numerical integrity."""

    @staticmethod
    def _validate_annual_sequence(years: tuple[int, ...], name: str) -> None:
        for previous, current in zip(years, years[1:], strict=False):
            if current <= previous:
                raise ForecastValidationError(
                    f"{name} must be strictly increasing and contain no duplicate years; "
                    f"found {previous}, {current}."
                )
            if current != previous + 1:
                raise ForecastValidationError(
                    f"{name} must contain consecutive annual periods; "
                    f"found a gap between {previous} and {current}."
                )

    @staticmethod
    def validate_input(forecast_input: ForecastInput) -> None:
        if not forecast_input.ticker or not forecast_input.ticker.strip():
            raise ForecastValidationError("Ticker symbol must be a non-empty string.")

        h_years = forecast_input.historical_years
        h_rev = forecast_input.historical_revenue
        h_margins = forecast_input.historical_margins
        h_capex = forecast_input.historical_capex
        h_dep = forecast_input.historical_depreciation
        h_wc = forecast_input.historical_working_capital
        h_tax = forecast_input.historical_taxes
        f_years = forecast_input.forecast_years

        if not h_years:
            raise ForecastValidationError("Historical years sequence cannot be empty.")
        ForecastValidator._validate_annual_sequence(h_years, "historical_years")

        n_years = len(h_years)
        series_map = {
            "historical_revenue": h_rev,
            "historical_margins": h_margins,
            "historical_capex": h_capex,
            "historical_depreciation": h_dep,
            "historical_working_capital": h_wc,
        }
        if h_tax:
            if len(h_tax) != n_years:
                raise ForecastValidationError(
                    f"Length mismatch: historical_taxes length ({len(h_tax)}) "
                    f"must match historical_years length ({n_years})."
                )
        elif forecast_input.tax_rate_assumption is None:
            raise ForecastConfigurationError(
                "A tax_rate_assumption is required when historical tax rates are unavailable."
            )
        elif not 0.0 <= forecast_input.tax_rate_assumption <= 1.0:
            raise ForecastValidationError("tax_rate_assumption must be between 0 and 1.")

        for name, series in series_map.items():
            if len(series) != n_years:
                raise ForecastValidationError(
                    f"Length mismatch: {name} length ({len(series)}) must match historical_years length ({n_years})."
                )
            for val in series:
                if math.isnan(val) or math.isinf(val):
                    raise ForecastValidationError(
                        f"Invalid numeric value (NaN or Inf) found in {name}: {val}"
                    )

        if not f_years:
            raise ForecastValidationError("Forecast years sequence cannot be empty.")
        ForecastValidator._validate_annual_sequence(f_years, "forecast_years")
        if f_years[0] <= h_years[-1]:
            raise ForecastValidationError(
                "forecast_years must begin after the final historical year; "
                f"last historical year is {h_years[-1]} and first forecast year is {f_years[0]}."
            )
        if f_years[0] != h_years[-1] + 1:
            raise ForecastValidationError(
                "forecast_years must begin in the year immediately following "
                f"the final historical year ({h_years[-1]})."
            )

        for val in h_rev:
            if val <= 0.0:
                raise ForecastValidationError(
                    f"Historical revenue must be strictly positive, found: {val}"
                )

        for val in h_margins:
            if not math.isfinite(val):
                raise ForecastValidationError(f"historical_margins must be finite, found: {val}")
        for val in h_tax:
            if not math.isfinite(val) or not (0.0 <= val <= 1.0):
                raise ForecastValidationError(
                    f"historical_taxes must be finite decimal tax rates between 0.0 and 1.0, found: {val}"
                )

        if forecast_input.custom_growth_rate is not None:
            if (
                not math.isfinite(forecast_input.custom_growth_rate)
                or forecast_input.custom_growth_rate <= -1.0
            ):
                raise ForecastValidationError(
                    "Custom growth rate must be finite and greater than -100%."
                )
        for name, value in (
            ("ebit_margin_assumption", forecast_input.ebit_margin_assumption),
            ("capex_pct_revenue_assumption", forecast_input.capex_pct_revenue_assumption),
            ("working_capital_pct_revenue_assumption", forecast_input.working_capital_pct_revenue_assumption),
        ):
            if value is not None and not math.isfinite(value):
                raise ForecastValidationError(f"{name} must be a finite number.")
        if (
            forecast_input.capex_pct_revenue_assumption is not None
            and forecast_input.capex_pct_revenue_assumption < 0.0
        ):
            raise ForecastValidationError(
                "capex_pct_revenue_assumption must be non-negative."
            )
        if forecast_input.tax_rate_assumption is not None and (
            not math.isfinite(forecast_input.tax_rate_assumption)
            or not 0.0 <= forecast_input.tax_rate_assumption <= 1.0
        ):
            raise ForecastValidationError("tax_rate_assumption must be finite and between 0 and 1.")
        guidance = forecast_input.management_guidance
        if guidance is not None:
            for name in ("revenue_cagr_override", "target_ebit_margin_override"):
                value = getattr(guidance, name, None)
                if value is not None and not math.isfinite(float(value)):
                    raise ForecastValidationError(f"management guidance {name} must be finite.")
            if guidance.revenue_cagr_override is not None and guidance.revenue_cagr_override <= -1.0:
                raise ForecastValidationError("management revenue growth override must be greater than -100%.")
            has_overrides = (
                guidance.revenue_cagr_override is not None
                or guidance.target_ebit_margin_override is not None
            )
            if has_overrides and (
                not guidance.source
                or not guidance.source.strip()
                or not guidance.reason
                or not guidance.reason.strip()
            ):
                raise ForecastValidationError(
                    "management guidance overrides require source and reason."
                )
