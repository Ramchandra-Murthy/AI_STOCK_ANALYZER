"""Forecast assumption derivation and legacy management-guidance compatibility."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite
from typing import Any

from services.forecast.models import ForecastAssumption, ForecastMethod

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ManagementGuidance:
    """Optional management overrides.

    Source and reason are mandatory when guidance is applied through the
    validated F-10A derivation path. The legacy apply_overrides method keeps
    its historical behaviour for existing callers.
    """

    revenue_cagr_override: float | None = None
    target_ebit_margin_override: float | None = None
    source: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class StatutoryTaxFallback:
    """Explicit, auditable statutory tax-rate fallback configuration."""

    rate: float
    jurisdiction: str
    entity_type: str
    tax_regime: str
    effective_date: str
    source: str

    def __post_init__(self) -> None:
        if not isfinite(float(self.rate)) or not 0.0 <= float(self.rate) <= 1.0:
            raise ValueError("statutory tax rate must be finite and between 0 and 1")
        for name in ("jurisdiction", "entity_type", "tax_regime", "effective_date", "source"):
            if not getattr(self, name).strip():
                raise ValueError(f"statutory tax fallback {name} is required")


@dataclass(frozen=True, slots=True)
class AssumptionDerivationInput:
    """Aligned historical financial observations for canonical assumption derivation."""

    historical_revenue: tuple[float, ...]
    historical_margins: tuple[float, ...]
    historical_capex: tuple[float, ...]
    historical_nwc: tuple[float, ...]
    historical_pbt: tuple[float, ...] = ()
    historical_tax: tuple[float, ...] = ()
    historical_years: tuple[int, ...] = ()
    statutory_tax_fallback: StatutoryTaxFallback | None = None
    management_guidance: ManagementGuidance | None = None
    sector: str | None = None
    sector_peer_values: Mapping[str, tuple[float, ...]] = field(default_factory=dict)
    # Appended to preserve positional construction of the pre-F-10A input contract.
    historical_tax_rates: tuple[float, ...] = ()
    explicit_tax_rate_fallback: float | None = None
    # Appended for positional compatibility; used only when historical NWC is absent.
    working_capital_pct_revenue_fallback: float | None = None


@dataclass(frozen=True, slots=True)
class AssumptionValidationConfig:
    """Configurable warning thresholds; hard checks remain mathematical."""

    lookback_periods: int = 5
    warning_ranges: Mapping[str, tuple[float | None, float | None]] = field(default_factory=dict)
    peer_percentile: float = 95.0
    minimum_peer_sample: int = 10

    def __post_init__(self) -> None:
        if self.lookback_periods < 2:
            raise ValueError("lookback_periods must be at least 2")
        if not isfinite(float(self.peer_percentile)) or not 0.0 < self.peer_percentile < 100.0:
            raise ValueError("peer_percentile must be between 0 and 100")
        if self.minimum_peer_sample < 10:
            raise ValueError("minimum_peer_sample cannot be less than 10")
        for name, bounds in self.warning_ranges.items():
            if len(bounds) != 2:
                raise ValueError(f"warning range for {name} must contain lower and upper bounds")
            lower, upper = bounds
            if lower is not None and not isfinite(float(lower)):
                raise ValueError(f"warning lower bound for {name} must be finite")
            if upper is not None and not isfinite(float(upper)):
                raise ValueError(f"warning upper bound for {name} must be finite")
            if lower is not None and upper is not None and lower > upper:
                raise ValueError(f"warning lower bound exceeds upper bound for {name}")


class AssumptionEngine:
    """Engine for deriving and applying forward-looking assumptions."""

    @staticmethod
    def derive_from_financials(
        data: AssumptionDerivationInput,
        config: AssumptionValidationConfig | None = None,
    ) -> ForecastAssumption:
        """Derive assumptions from the latest valid historical observations.

        The five-year default is a maximum lookback, not a requirement that the
        last five calendar years all be present. Invalid observations are skipped
        and recorded in metadata. Historical working capital and tax rates are
        preferred independently; explicit fallbacks are required for either
        assumption when its historical observations are absent.
        """
        cfg = config or AssumptionValidationConfig()
        revenue = tuple(float(value) for value in data.historical_revenue)
        margins = tuple(float(value) for value in data.historical_margins)
        capex = tuple(float(value) for value in data.historical_capex)
        nwc = tuple(float(value) for value in data.historical_nwc)
        working_capital_fallback = data.working_capital_pct_revenue_fallback
        pbt = tuple(float(value) for value in data.historical_pbt)
        tax = tuple(float(value) for value in data.historical_tax)
        tax_rates = tuple(float(value) for value in data.historical_tax_rates)

        if len(revenue) < 2:
            raise ValueError("historical_revenue must contain at least two observations")
        for name, values in (
            ("historical_margins", margins),
            ("historical_capex", capex),
        ):
            if len(values) != len(revenue):
                raise ValueError(f"{name} must match historical_revenue length")
        if nwc and len(nwc) != len(revenue):
            raise ValueError("historical_nwc must match historical_revenue length")
        if not nwc and working_capital_fallback is None:
            raise ValueError(
                "historical_nwc or an explicit working_capital_pct_revenue_assumption is required"
            )
        if working_capital_fallback is not None and not isfinite(
            float(working_capital_fallback)
        ):
            raise ValueError("working_capital_pct_revenue_assumption must be finite")
        if (
            bool(pbt) != bool(tax)
            or (pbt and len(pbt) != len(revenue))
            or (tax and len(tax) != len(revenue))
        ):
            raise ValueError(
                "historical_pbt and historical_tax must both be empty or match revenue"
            )
        if tax_rates and len(tax_rates) != len(revenue):
            raise ValueError("historical_tax_rates must match historical_revenue length")
        if any(not isfinite(value) or not 0.0 <= value <= 1.0 for value in tax_rates):
            raise ValueError("historical_tax_rates must be finite and between 0 and 1")
        if data.explicit_tax_rate_fallback is not None and (
            not isfinite(float(data.explicit_tax_rate_fallback))
            or not 0.0 <= float(data.explicit_tax_rate_fallback) <= 1.0
        ):
            raise ValueError("explicit_tax_rate_fallback must be finite and between 0 and 1")

        years = (
            tuple(int(year) for year in data.historical_years)
            if data.historical_years
            else tuple(range(len(revenue)))
        )
        if len(years) != len(revenue):
            raise ValueError("historical_years must match historical_revenue length")
        if any(right <= left for left, right in zip(years, years[1:], strict=False)):
            raise ValueError("historical_years must be strictly increasing")

        valid_revenue_indices = [
            index for index, value in enumerate(revenue) if isfinite(value) and value > 0.0
        ]
        selected_revenue_indices = valid_revenue_indices[-cfg.lookback_periods :]
        if len(selected_revenue_indices) < 2:
            raise ValueError("at least two valid positive-revenue observations are required")
        first_index = selected_revenue_indices[0]
        last_index = selected_revenue_indices[-1]
        elapsed_years = years[last_index] - years[first_index]
        if elapsed_years <= 0:
            raise ValueError("revenue CAGR requires a positive historical time interval")
        revenue_growth = (revenue[last_index] / revenue[first_index]) ** (1.0 / elapsed_years) - 1.0
        if not isfinite(revenue_growth) or revenue_growth <= -1.0:
            raise ValueError("derived revenue growth must be finite and greater than -100%")

        valid_margin_indices = [index for index, value in enumerate(margins) if isfinite(value)][
            -cfg.lookback_periods :
        ]
        if not valid_margin_indices:
            raise ValueError("at least one finite historical margin is required")
        ebitda_margin = margins[valid_margin_indices[-1]]

        capex_ratios = [
            abs(capex[index]) / revenue[index]
            for index in range(len(revenue))
            if isfinite(capex[index]) and isfinite(revenue[index]) and revenue[index] > 0.0
        ][-cfg.lookback_periods :]
        if not capex_ratios:
            raise ValueError("at least one valid CapEx/revenue observation is required")
        capex_pct = sum(capex_ratios) / len(capex_ratios)

        nwc_ratios = [
            nwc[index] / revenue[index]
            for index in range(len(revenue))
            if isfinite(nwc[index]) and isfinite(revenue[index]) and revenue[index] > 0.0
        ][-cfg.lookback_periods :]
        if nwc:
            if not nwc_ratios:
                raise ValueError("at least one valid NWC/revenue observation is required")
            nwc_pct = sum(nwc_ratios) / len(nwc_ratios)
            nwc_metadata: dict[str, Any] = {
                "method": "historical_nwc_to_revenue",
                "observations_used": len(nwc_ratios),
                "fallback_used": False,
            }
        else:
            assert working_capital_fallback is not None
            nwc_pct = float(working_capital_fallback)
            nwc_metadata = {
                "method": "explicit_input_fallback",
                "observations_used": 0,
                "fallback_used": True,
                "source": "ForecastService.generate_scenario.working_capital_pct_revenue_assumption",
            }

        valid_tax_indices = [
            index
            for index in range(len(pbt))
            if isfinite(pbt[index]) and pbt[index] > 0.0 and isfinite(tax[index])
        ][-cfg.lookback_periods :]
        if tax_rates:
            selected_tax_rates = [
                value for value in tax_rates[-cfg.lookback_periods :] if isfinite(value)
            ]
            if not selected_tax_rates:
                raise ValueError("at least one finite historical tax-rate observation is required")
            tax_rate = sum(selected_tax_rates) / len(selected_tax_rates)
            tax_metadata: dict[str, Any] = {
                "method": "historical_effective_tax_rate",
                "periods_used": list(years[-len(selected_tax_rates) :]),
                "fallback_used": False,
                "input_contract": "historical_tax_rates",
            }
        elif valid_tax_indices:
            tax_rates_from_financials = [tax[index] / pbt[index] for index in valid_tax_indices]
            tax_rate = sum(tax_rates_from_financials) / len(tax_rates_from_financials)
            tax_metadata = {
                "method": "historical_effective_tax_rate",
                "periods_used": [years[index] for index in valid_tax_indices],
                "fallback_used": False,
                "input_contract": "historical_tax_expense_over_pbt",
            }
        elif data.explicit_tax_rate_fallback is not None:
            tax_rate = float(data.explicit_tax_rate_fallback)
            tax_metadata = {
                "method": "explicit_input_fallback",
                "fallback_used": True,
                "source": "ForecastInput.tax_rate_assumption",
            }
        elif data.statutory_tax_fallback is not None:
            fallback = data.statutory_tax_fallback
            tax_rate = float(fallback.rate)
            tax_metadata = {
                "method": "configured_statutory_fallback",
                "fallback_used": True,
                "jurisdiction": fallback.jurisdiction,
                "entity_type": fallback.entity_type,
                "tax_regime": fallback.tax_regime,
                "effective_date": fallback.effective_date,
                "source": fallback.source,
            }
        else:
            raise ValueError(
                "historical tax rates, an explicit tax_rate_assumption, or a configured "
                "statutory_tax_fallback is required"
            )

        values = {
            "revenue_growth_rate": revenue_growth,
            "ebitda_margin": ebitda_margin,
            "tax_rate": tax_rate,
            "capex_pct_revenue": capex_pct,
            "working_capital_pct_revenue": nwc_pct,
        }
        guidance_metadata: dict[str, Any] | None = None
        guidance = data.management_guidance
        if guidance is not None and (
            guidance.revenue_cagr_override is not None
            or guidance.target_ebit_margin_override is not None
        ):
            if not guidance.source or not guidance.source.strip():
                raise ValueError("management override source is required")
            if not guidance.reason or not guidance.reason.strip():
                raise ValueError("management override reason is required")
            if guidance.revenue_cagr_override is not None:
                override = float(guidance.revenue_cagr_override)
                if not isfinite(override) or override <= -1.0:
                    raise ValueError(
                        "revenue growth override must be finite and greater than -100%"
                    )
                values["revenue_growth_rate"] = override
            if guidance.target_ebit_margin_override is not None:
                override = float(guidance.target_ebit_margin_override)
                if not isfinite(override):
                    raise ValueError("EBIT margin override must be finite")
                values["ebitda_margin"] = override
            guidance_metadata = {
                "source": guidance.source,
                "reason": guidance.reason,
                "revenue_growth_rate": guidance.revenue_cagr_override,
                "ebitda_margin": guidance.target_ebit_margin_override,
            }

        warnings: list[str] = []
        for name, (lower, upper) in cfg.warning_ranges.items():
            if name not in values:
                continue
            value = values[name]
            if lower is not None and value < lower:
                warnings.append(f"{name}={value:.6g} is below configured warning threshold {lower}")
            if upper is not None and value > upper:
                warnings.append(f"{name}={value:.6g} is above configured warning threshold {upper}")

        peer_validation: dict[str, Any] = {}
        for name, peer_values in data.sector_peer_values.items():
            if name not in values:
                continue
            peers = sorted(float(value) for value in peer_values if isfinite(float(value)))
            if len(peers) < cfg.minimum_peer_sample:
                peer_validation[name] = {
                    "status": "insufficient_peer_sample",
                    "sample_size": len(peers),
                    "minimum_sample_size": cfg.minimum_peer_sample,
                }
                continue
            position = (len(peers) - 1) * cfg.peer_percentile / 100.0
            lower_index = int(position)
            upper_index = min(lower_index + 1, len(peers) - 1)
            fraction = position - lower_index
            threshold = peers[lower_index] + (peers[upper_index] - peers[lower_index]) * fraction
            peer_validation[name] = {
                "status": "available",
                "sample_size": len(peers),
                "percentile": cfg.peer_percentile,
                "upper_threshold": threshold,
            }
            if values[name] > threshold:
                warnings.append(
                    f"{name}={values[name]:.6g} exceeds sector peer "
                    f"{cfg.peer_percentile:g}th percentile {threshold:.6g}"
                )

        metadata = {
            "engine": "AssumptionEngine",
            "engine_version": "f10a-1",
            "lookback_periods": cfg.lookback_periods,
            "revenue_periods_used": [years[index] for index in selected_revenue_indices],
            "margin_periods_used": [years[index] for index in valid_margin_indices],
            "capex_observations_used": len(capex_ratios),
            "nwc_observations_used": len(nwc_ratios),
            "working_capital": nwc_metadata,
            "tax": tax_metadata,
            "sector": data.sector,
            "peer_validation": peer_validation,
            "warnings": warnings,
            "management_override": guidance_metadata,
        }
        return ForecastAssumption(
            revenue_growth_rate=values["revenue_growth_rate"],
            ebitda_margin=values["ebitda_margin"],
            tax_rate=values["tax_rate"],
            capex_pct_revenue=values["capex_pct_revenue"],
            working_capital_pct_revenue=values["working_capital_pct_revenue"],
            metadata=metadata,
        )

    @staticmethod
    def derive_assumptions(
        historical_revenue: tuple[float, ...],
        historical_margins: tuple[float, ...],
        historical_capex: tuple[float, ...],
        method: ForecastMethod = ForecastMethod.CAGR,
        **kwargs: Any,
    ) -> ForecastAssumption:
        """Legacy compatibility API.

        New F-10 callers should use derive_from_financials so tax and working
        capital are based on supplied historical data and explicit tax fallback
        configuration. This adapter remains only for callers that still depend
        on the pre-F-10A compatibility contract.
        """
        logger.warning(
            "Legacy derive_assumptions uses compatibility defaults; migrate to "
            "AssumptionEngine.derive_from_financials"
        )
        logger.info("Deriving baseline assumptions using legacy method: %s", method.value)
        rev_growth = (
            0.08
            if len(historical_revenue) < 2 or historical_revenue[0] <= 0
            else (historical_revenue[-1] / historical_revenue[0])
            ** (1.0 / (len(historical_revenue) - 1))
            - 1.0
        )
        ebitda_m = historical_margins[-1] if historical_margins else 0.15
        tax_r = 0.25
        capex_pct = (
            0.05
            if not historical_capex or not historical_revenue or historical_revenue[-1] == 0
            else abs(historical_capex[-1] / historical_revenue[-1])
        )
        return ForecastAssumption(
            revenue_growth_rate=rev_growth,
            ebitda_margin=ebitda_m,
            tax_rate=tax_r,
            capex_pct_revenue=capex_pct,
            working_capital_pct_revenue=0.10,
            metadata={
                "engine": "AssumptionEngine",
                "method": method.value,
                "compatibility_mode": True,
            },
        )

    @staticmethod
    def apply_overrides(
        base_revenues: tuple[float, ...] | list[float],
        base_margins: tuple[float, ...] | list[float],
        guidance: ManagementGuidance,
    ) -> tuple[tuple[float, ...], tuple[float, ...]]:
        """Legacy override adapter retained for existing callers."""
        revenues = list(float(v) for v in base_revenues)
        margins = list(float(v) for v in base_margins)
        if guidance.revenue_cagr_override is not None and revenues:
            growth = float(guidance.revenue_cagr_override)
            last = revenues[0]
            projected: list[float] = []
            for _ in revenues:
                projected.append(last)
                last *= 1.0 + growth
            revenues = projected
        if guidance.target_ebit_margin_override is not None:
            margins = [float(guidance.target_ebit_margin_override) for _ in margins]
        return tuple(revenues), tuple(margins)
