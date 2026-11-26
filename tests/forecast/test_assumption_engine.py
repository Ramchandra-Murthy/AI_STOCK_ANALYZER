"""
==========================================================
TEST ASSUMPTION & CONFIDENCE ENGINES
Module  : tests.forecast.test_assumption_engine
==========================================================
"""

from __future__ import annotations

import pytest

from services.forecast.assumption_engine import (
    AssumptionDerivationInput,
    AssumptionEngine,
    AssumptionValidationConfig,
    ManagementGuidance,
    StatutoryTaxFallback,
)
from services.forecast.confidence_engine import ConfidenceEngine
from services.forecast.models import ConfidenceLevel, ForecastMethod


def _historical_input(**overrides) -> AssumptionDerivationInput:
    values = {
        "historical_revenue": (100.0, 110.0, 121.0, 133.1, 146.41, 161.051),
        "historical_margins": (0.15, 0.16, 0.17, 0.18, 0.19, 0.20),
        "historical_capex": (10.0, 11.0, 12.1, 13.31, 14.641, 16.1051),
        "historical_nwc": (10.0, 22.0, 24.2, 26.62, 29.282, 32.2102),
        "historical_pbt": (20.0, 22.0, 24.0, 26.0, 28.0, 30.0),
        "historical_tax": (5.0, 5.5, 6.0, 6.5, 7.0, 7.5),
        "historical_years": (2020, 2021, 2022, 2023, 2024, 2025),
        "sector": "technology",
    }
    values.update(overrides)
    return AssumptionDerivationInput(**values)


def test_assumption_engine_derivation() -> None:
    revenue = (1000.0, 1100.0, 1210.0)
    margins = (0.15, 0.16, 0.165)
    capex = (50.0, 55.0, 60.0)

    assumption = AssumptionEngine.derive_assumptions(
        historical_revenue=revenue,
        historical_margins=margins,
        historical_capex=capex,
        method=ForecastMethod.CAGR,
    )

    assert assumption.revenue_growth_rate > 0.0
    assert assumption.ebitda_margin == 0.165
    assert assumption.tax_rate == 0.25
    assert "engine" in assumption.metadata


def test_canonical_derivation_uses_five_latest_valid_periods() -> None:
    assumption = AssumptionEngine.derive_from_financials(_historical_input())

    assert assumption.revenue_growth_rate == pytest.approx(0.10)
    assert assumption.ebitda_margin == pytest.approx(0.20)
    assert assumption.tax_rate == pytest.approx(0.25)
    assert assumption.capex_pct_revenue == pytest.approx(0.10)
    assert assumption.working_capital_pct_revenue == pytest.approx(0.20)
    assert assumption.metadata["revenue_periods_used"] == [2021, 2022, 2023, 2024, 2025]
    assert assumption.metadata["tax"]["method"] == "historical_effective_tax_rate"


def test_canonical_derivation_uses_explicit_statutory_tax_fallback() -> None:
    fallback = StatutoryTaxFallback(
        rate=0.25,
        jurisdiction="India",
        entity_type="domestic_company",
        tax_regime="configured_regime",
        effective_date="2026-04-01",
        source="approved statutory tax configuration",
    )
    data = _historical_input(
        historical_pbt=(0.0, -1.0, 0.0, -2.0, 0.0, -3.0),
        historical_tax=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        statutory_tax_fallback=fallback,
    )

    assumption = AssumptionEngine.derive_from_financials(data)

    assert assumption.tax_rate == pytest.approx(0.25)
    assert assumption.metadata["tax"]["fallback_used"] is True
    assert assumption.metadata["tax"]["source"] == "approved statutory tax configuration"


def test_canonical_derivation_requires_explicit_tax_fallback() -> None:
    data = _historical_input(
        historical_pbt=(0.0, -1.0, 0.0, -2.0, 0.0, -3.0),
        historical_tax=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    )

    with pytest.raises(ValueError, match="statutory_tax_fallback"):
        AssumptionEngine.derive_from_financials(data)


def test_canonical_derivation_preserves_negative_working_capital() -> None:
    data = _historical_input(historical_nwc=(-10.0, -11.0, -12.1, -13.31, -14.641, -16.1051))

    assumption = AssumptionEngine.derive_from_financials(data)

    assert assumption.working_capital_pct_revenue == pytest.approx(-0.10)


def test_canonical_derivation_skips_zero_revenue_and_records_periods() -> None:
    data = _historical_input(historical_revenue=(100.0, 0.0, 121.0, 133.1, 146.41, 161.051))

    assumption = AssumptionEngine.derive_from_financials(data)

    assert assumption.metadata["revenue_periods_used"] == [2020, 2022, 2023, 2024, 2025]
    assert assumption.revenue_growth_rate == pytest.approx(0.10)


def test_canonical_derivation_requires_aligned_historical_series() -> None:
    data = _historical_input(historical_nwc=(10.0, 11.0))

    with pytest.raises(ValueError, match="historical_nwc must match"):
        AssumptionEngine.derive_from_financials(data)


def test_management_overrides_require_provenance_and_valid_growth() -> None:
    missing_provenance = _historical_input(
        management_guidance=ManagementGuidance(revenue_cagr_override=0.12)
    )
    with pytest.raises(ValueError, match="source is required"):
        AssumptionEngine.derive_from_financials(missing_provenance)

    invalid_growth = _historical_input(
        management_guidance=ManagementGuidance(
            revenue_cagr_override=-1.0,
            source="management",
            reason="approved plan",
        )
    )
    with pytest.raises(ValueError, match="greater than -100%"):
        AssumptionEngine.derive_from_financials(invalid_growth)


def test_management_overrides_are_applied_with_provenance() -> None:
    data = _historical_input(
        management_guidance=ManagementGuidance(
            revenue_cagr_override=0.12,
            target_ebit_margin_override=0.24,
            source="management guidance FY27",
            reason="board-approved operating plan",
        )
    )

    assumption = AssumptionEngine.derive_from_financials(data)

    assert assumption.revenue_growth_rate == pytest.approx(0.12)
    assert assumption.ebitda_margin == pytest.approx(0.24)
    assert assumption.metadata["management_override"]["source"] == "management guidance FY27"


def test_hybrid_validation_warns_on_configured_range_and_peer_percentile() -> None:
    peers = tuple(value / 1000 for value in range(10, 110, 10))
    data = _historical_input(sector_peer_values={"capex_pct_revenue": peers})
    config = AssumptionValidationConfig(
        warning_ranges={"capex_pct_revenue": (None, 0.08)},
        peer_percentile=95.0,
        minimum_peer_sample=10,
    )

    assumption = AssumptionEngine.derive_from_financials(data, config)

    assert any(
        "configured warning threshold" in warning for warning in assumption.metadata["warnings"]
    )
    assert any("95th percentile" in warning for warning in assumption.metadata["warnings"])
    assert assumption.metadata["peer_validation"]["capex_pct_revenue"]["sample_size"] == 10


def test_peer_percentile_is_not_used_with_fewer_than_ten_peers() -> None:
    data = _historical_input(sector_peer_values={"capex_pct_revenue": (0.01,) * 9})

    assumption = AssumptionEngine.derive_from_financials(data)

    assert assumption.metadata["peer_validation"]["capex_pct_revenue"]["status"] == (
        "insufficient_peer_sample"
    )
    assert not any("95th percentile" in warning for warning in assumption.metadata["warnings"])


def test_confidence_engine_evaluation() -> None:
    data = (100.0, 105.0, 110.0, 115.0)
    confidence = ConfidenceEngine.evaluate_confidence(data)
    assert confidence in list(ConfidenceLevel)
