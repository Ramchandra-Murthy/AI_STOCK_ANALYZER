import numpy as np
import pandas as pd
import pytest

from algorithmic_trading.impact_bootstrap import bootstrap_market_impact_calibration


def _inputs() -> tuple[pd.Series, pd.Series, pd.Series]:
    index = pd.RangeIndex(40)
    participation = pd.Series(np.linspace(0.01, 0.20, 40), index=index)
    volatility = pd.Series(np.linspace(0.01, 0.04, 40), index=index)
    feature = volatility * np.sqrt(participation) * 10_000.0
    noise = np.sin(np.arange(40)) * 0.15
    shortfall = pd.Series(1.5 + 0.7 * feature + noise, index=index)
    return shortfall, participation, volatility


def test_bootstrap_market_impact_returns_reproducible_parameter_intervals() -> None:
    inputs = _inputs()

    first = bootstrap_market_impact_calibration(*inputs, samples=200, seed=17)
    second = bootstrap_market_impact_calibration(*inputs, samples=200, seed=17)

    assert first == second
    assert first.successful_samples >= 160
    assert first.half_spread_lower_bps <= first.calibration.half_spread_bps
    assert first.half_spread_upper_bps >= first.calibration.half_spread_bps
    assert first.impact_coefficient_lower <= first.calibration.impact_coefficient
    assert first.impact_coefficient_upper >= first.calibration.impact_coefficient


def test_bootstrap_market_impact_respects_confidence_level() -> None:
    inputs = _inputs()

    narrow = bootstrap_market_impact_calibration(*inputs, samples=300, confidence=0.80)
    wide = bootstrap_market_impact_calibration(*inputs, samples=300, confidence=0.95)

    assert wide.half_spread_lower_bps <= narrow.half_spread_lower_bps
    assert wide.half_spread_upper_bps >= narrow.half_spread_upper_bps
    assert wide.impact_coefficient_lower <= narrow.impact_coefficient_lower
    assert wide.impact_coefficient_upper >= narrow.impact_coefficient_upper


def test_bootstrap_market_impact_rejects_invalid_configuration() -> None:
    inputs = _inputs()

    with pytest.raises(ValueError, match="samples must be at least 1"):
        bootstrap_market_impact_calibration(*inputs, samples=0)

    with pytest.raises(ValueError, match="confidence must be between 0 and 1"):
        bootstrap_market_impact_calibration(*inputs, confidence=1.0)


def test_bootstrap_market_impact_preserves_input_alignment_validation() -> None:
    shortfall, participation, volatility = _inputs()
    volatility.index = volatility.index + 1

    with pytest.raises(ValueError, match="identical indexes"):
        bootstrap_market_impact_calibration(shortfall, participation, volatility)


def test_bootstrap_market_impact_rejects_insufficient_predictor_variation() -> None:
    index = pd.RangeIndex(12)
    participation = pd.Series(0.1, index=index)
    volatility = pd.Series(0.02, index=index)
    shortfall = pd.Series(np.linspace(1.0, 2.0, len(index)), index=index)

    with pytest.raises(ValueError, match="variation"):
        bootstrap_market_impact_calibration(shortfall, participation, volatility)
