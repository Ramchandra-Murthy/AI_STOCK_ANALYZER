import numpy as np
import pandas as pd
import pytest

from algorithmic_trading.impact_calibration import calibrate_market_impact


def test_calibration_recovers_synthetic_square_root_parameters() -> None:
    index = pd.RangeIndex(6)
    participation = pd.Series([0.01, 0.02, 0.04, 0.08, 0.12, 0.20], index=index)
    volatility = pd.Series([0.01, 0.015, 0.02, 0.025, 0.03, 0.04], index=index)
    feature = volatility * np.sqrt(participation) * 10_000
    observed = 1.5 + 0.7 * feature

    fitted = calibrate_market_impact(observed, participation, volatility)

    assert fitted.half_spread_bps == pytest.approx(1.5)
    assert fitted.impact_coefficient == pytest.approx(0.7)
    assert fitted.rmse_bps == pytest.approx(0.0, abs=1e-10)
    assert fitted.r_squared == pytest.approx(1.0)
    assert fitted.observations == 6


def test_calibration_keeps_parameters_non_negative_with_noisy_data() -> None:
    index = pd.RangeIndex(4)
    participation = pd.Series([0.02, 0.05, 0.10, 0.20], index=index)
    volatility = pd.Series([0.01, 0.02, 0.03, 0.04], index=index)
    observed = pd.Series([0.1, 0.2, 0.1, 0.0], index=index)

    fitted = calibrate_market_impact(observed, participation, volatility)

    assert fitted.half_spread_bps >= 0.0
    assert fitted.impact_coefficient >= 0.0
    assert fitted.rmse_bps >= 0.0


def test_calibration_rejects_misaligned_indexes() -> None:
    with pytest.raises(ValueError, match="identical indexes"):
        calibrate_market_impact(
            pd.Series([1.0, 2.0, 3.0]),
            pd.Series([0.1, 0.2, 0.3], index=[0, 1, 3]),
            pd.Series([0.01, 0.02, 0.03]),
        )


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1.0])
def test_calibration_rejects_invalid_shortfall(bad: float) -> None:
    with pytest.raises(ValueError):
        calibrate_market_impact(
            pd.Series([1.0, 2.0, bad]),
            pd.Series([0.1, 0.2, 0.3]),
            pd.Series([0.01, 0.02, 0.03]),
        )


def test_calibration_rejects_invalid_participation() -> None:
    with pytest.raises(ValueError, match="participation_rate"):
        calibrate_market_impact(
            pd.Series([1.0, 2.0, 3.0]),
            pd.Series([0.1, 0.0, 0.3]),
            pd.Series([0.01, 0.02, 0.03]),
        )


def test_calibration_requires_feature_variation_and_three_samples() -> None:
    with pytest.raises(ValueError, match="at least three"):
        calibrate_market_impact(
            pd.Series([1.0, 2.0]),
            pd.Series([0.1, 0.2]),
            pd.Series([0.01, 0.02]),
        )
    with pytest.raises(ValueError, match="variation"):
        calibrate_market_impact(
            pd.Series([1.0, 2.0, 3.0]),
            pd.Series([0.1, 0.1, 0.1]),
            pd.Series([0.01, 0.01, 0.01]),
        )
