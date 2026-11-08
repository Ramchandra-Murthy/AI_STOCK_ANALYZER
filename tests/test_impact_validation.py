import numpy as np
import pandas as pd
import pytest

from algorithmic_trading.impact_validation import (
    validate_market_impact_out_of_sample,
)


def _observations(start: str, periods: int, noise: float = 0.0) -> pd.DataFrame:
    index = pd.date_range(start, periods=periods, freq="D")
    participation = np.linspace(0.01, 0.20, periods)
    volatility = np.linspace(0.01, 0.04, periods)
    feature = volatility * np.sqrt(participation) * 10_000.0
    shortfall = 1.5 + 0.7 * feature + noise
    return pd.DataFrame(
        {
            "observed_shortfall_bps": shortfall,
            "participation_rate": participation,
            "volatility": volatility,
        },
        index=index,
    )


def test_holdout_validation_recovers_parameters_without_refitting() -> None:
    calibration = _observations("2024-01-01", 8)
    holdout = _observations("2024-02-01", 5, noise=0.25)

    result = validate_market_impact_out_of_sample(calibration, holdout)

    assert result.calibration.half_spread_bps == pytest.approx(1.5)
    assert result.calibration.impact_coefficient == pytest.approx(0.7)
    assert result.observations == 5
    assert result.rmse_bps == pytest.approx(0.25)
    assert result.mae_bps == pytest.approx(0.25)
    assert result.bias_bps == pytest.approx(0.25)
    assert len(result.predictions) == 5


def test_holdout_must_be_strictly_later_than_calibration() -> None:
    calibration = _observations("2024-01-01", 8)
    overlapping = _observations("2024-01-08", 5)

    with pytest.raises(ValueError, match="strictly after"):
        validate_market_impact_out_of_sample(calibration, overlapping)


def test_holdout_rejects_duplicate_or_unsorted_timestamps() -> None:
    calibration = _observations("2024-01-01", 8)
    holdout = _observations("2024-02-01", 5)
    duplicate = pd.concat([holdout, holdout.iloc[[0]]]).sort_index()
    with pytest.raises(ValueError, match="duplicate"):
        validate_market_impact_out_of_sample(calibration, duplicate)

    unsorted = holdout.iloc[::-1]
    with pytest.raises(ValueError, match="chronological"):
        validate_market_impact_out_of_sample(calibration, unsorted)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("observed_shortfall_bps", -1.0),
        ("participation_rate", 0.0),
        ("participation_rate", 1.1),
        ("volatility", np.inf),
    ],
)
def test_holdout_rejects_invalid_observations(column: str, value: float) -> None:
    calibration = _observations("2024-01-01", 8)
    holdout = _observations("2024-02-01", 5)
    holdout.loc[holdout.index[0], column] = value

    with pytest.raises(ValueError):
        validate_market_impact_out_of_sample(calibration, holdout)


def test_constant_holdout_target_has_undefined_r_squared() -> None:
    calibration = _observations("2024-01-01", 8)
    holdout = _observations("2024-02-01", 5)
    holdout["observed_shortfall_bps"] = 2.0

    result = validate_market_impact_out_of_sample(calibration, holdout)

    assert result.r_squared is None
