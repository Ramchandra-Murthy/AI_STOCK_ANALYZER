import numpy as np
import pandas as pd
import pytest

from algorithmic_trading.impact_walk_forward import validate_market_impact_walk_forward


def _observations(periods: int = 30) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=periods, freq="D")
    participation = np.linspace(0.01, 0.20, periods)
    volatility = np.linspace(0.01, 0.04, periods)
    feature = volatility * np.sqrt(participation) * 10_000.0
    return pd.DataFrame(
        {
            "observed_shortfall_bps": 1.5 + 0.7 * feature,
            "participation_rate": participation,
            "volatility": volatility,
        },
        index=index,
    )


def test_walk_forward_uses_expanding_calibration_and_scores_each_holdout_once() -> None:
    data = _observations()

    result = validate_market_impact_walk_forward(data, min_train_size=12, n_splits=3)

    assert result["fold"].tolist() == [1, 2, 3]
    assert result["calibration_observations"].tolist() == [12, 18, 24]
    assert result["holdout_observations"].tolist() == [6, 6, 6]
    assert result["holdout_start"].tolist() == [
        str(data.index[12]),
        str(data.index[18]),
        str(data.index[24]),
    ]
    assert result["holdout_end"].tolist() == [
        str(data.index[17]),
        str(data.index[23]),
        str(data.index[29]),
    ]
    assert result["half_spread_bps"].tolist() == pytest.approx([1.5, 1.5, 1.5])
    assert result["impact_coefficient"].tolist() == pytest.approx([0.7, 0.7, 0.7])
    assert result["rmse_bps"].tolist() == pytest.approx([0.0, 0.0, 0.0], abs=1e-9)


def test_walk_forward_distributes_remainder_without_dropping_observations() -> None:
    data = _observations(29)

    result = validate_market_impact_walk_forward(data, min_train_size=12, n_splits=4)

    assert result["holdout_observations"].tolist() == [5, 4, 4, 4]
    assert result["holdout_observations"].sum() == len(data) - 12
    assert result["calibration_observations"].tolist() == [12, 17, 21, 25]


def test_walk_forward_rejects_invalid_configuration_and_short_history() -> None:
    data = _observations()

    with pytest.raises(ValueError, match="min_train_size"):
        validate_market_impact_walk_forward(data, min_train_size=2)

    with pytest.raises(ValueError, match="n_splits"):
        validate_market_impact_walk_forward(data, n_splits=0)

    with pytest.raises(ValueError, match="not enough observations"):
        validate_market_impact_walk_forward(data.iloc[:10], min_train_size=6, n_splits=3)


def test_walk_forward_rejects_duplicate_and_unsorted_timestamps() -> None:
    data = _observations()

    duplicate = pd.concat([data, data.iloc[[0]]]).sort_index()
    with pytest.raises(ValueError, match="duplicate"):
        validate_market_impact_walk_forward(duplicate, min_train_size=12, n_splits=3)

    with pytest.raises(ValueError, match="chronological"):
        validate_market_impact_walk_forward(data.iloc[::-1], min_train_size=12, n_splits=3)


def test_walk_forward_rejects_invalid_values_in_any_fold() -> None:
    data = _observations()
    data.iloc[-1, data.columns.get_loc("participation_rate")] = 0.0

    with pytest.raises(ValueError, match="participation_rate"):
        validate_market_impact_walk_forward(data, min_train_size=12, n_splits=3)
