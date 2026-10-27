import numpy as np
import pandas as pd
import pytest

from algorithmic_trading.neural_network_benchmark import evaluate_mlp_return_strategy


def _returns(count: int = 120) -> pd.Series:
    rng = np.random.default_rng(7)
    values = rng.normal(0.0003, 0.01, count)
    return pd.Series(values, index=pd.date_range("2020-01-01", periods=count, freq="B"))


def test_mlp_benchmark_uses_chronological_train_validation_test_splits() -> None:
    result = evaluate_mlp_return_strategy(_returns(), random_state=1)

    assert result["train_observations"] > result["validation_observations"]
    assert result["validation_observations"] > 0
    assert result["test_observations"] > 0
    assert result["train_end"] < result["validation_start"]
    assert result["validation_end"] < result["test_start"]
    assert pd.Timestamp(result["test_end"]) == pd.Timestamp("2020-06-15")


def test_mlp_benchmark_returns_comparable_test_metrics() -> None:
    result = evaluate_mlp_return_strategy(_returns(), cost_bps=10)

    assert np.isfinite(result["validation_mse"])
    assert np.isfinite(result["test_mse"])
    assert np.isfinite(result["strategy_cumulative_return"])
    assert np.isfinite(result["buy_hold_cumulative_return"])
    assert result["cost_bps"] == 10.0
    assert result["test_turnover"] >= 0


def test_mlp_benchmark_rejects_short_history() -> None:
    returns = _returns(20)

    with pytest.raises(ValueError, match="at least 40"):
        evaluate_mlp_return_strategy(returns)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"train_fraction": 1.0}, "train_fraction"),
        ({"validation_fraction": 1.0}, "validation_fraction"),
        ({"train_fraction": 0.8, "validation_fraction": 0.2}, "less than 1"),
        ({"cost_bps": -1}, "cost_bps"),
    ],
)
def test_mlp_benchmark_rejects_invalid_configuration(
    kwargs: dict[str, float], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        evaluate_mlp_return_strategy(_returns(), **kwargs)


def test_mlp_benchmark_rejects_duplicate_timestamps() -> None:
    returns = _returns()
    duplicated = pd.concat([returns, returns.iloc[[0]]])

    with pytest.raises(ValueError, match="duplicate timestamps"):
        evaluate_mlp_return_strategy(duplicated)


$3_on_same_test_period() -> None:
    from algorithmic_trading.neural_network_benchmark import evaluate_mlp_seed_stability

    result = evaluate_mlp_seed_stability(_returns(), random_states=(1, 2))

    assert result["seed_count"] == 2
    assert len(result["runs"]) == 2
    assert result["runs"][0]["test_start"] == result["runs"][1]["test_start"]
    assert result["runs"][0]["test_end"] == result["runs"][1]["test_end"]
    assert 0 <= result["outperformance_count"] <= 2
    assert np.isfinite(result["median_strategy_return"])
    assert result["minimum_strategy_return"] <= result["maximum_strategy_return"]


def test_mlp_seed_stability_rejects_empty_or_duplicate_seeds() -> None:
    from algorithmic_trading.neural_network_benchmark import evaluate_mlp_seed_stability

    with pytest.raises(ValueError, match="at least one"):
        evaluate_mlp_seed_stability(_returns(), random_states=())

    with pytest.raises(ValueError, match="must be unique"):
        evaluate_mlp_seed_stability(_returns(), random_states=(7, 7))
