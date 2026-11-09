"""Tests for rolling out-of-sample portfolio evaluation."""

import numpy as np
import pandas as pd
import pytest

from algorithmic_trading.portfolio_walk_forward import walk_forward_portfolio_evaluate


@pytest.fixture
def returns() -> pd.DataFrame:
    rng = np.random.default_rng(851)
    common = rng.normal(0.0003, 0.01, 180)
    return pd.DataFrame(
        {
            "A": common + rng.normal(0.0, 0.002, 180),
            "B": common * 0.8 + rng.normal(0.0, 0.003, 180),
            "C": rng.normal(0.0002, 0.006, 180),
            "D": rng.normal(0.0001, 0.008, 180),
        },
        index=pd.date_range("2025-01-01", periods=180, freq="B"),
    )


def test_evaluator_compares_three_strategies_on_identical_test_periods(
    returns: pd.DataFrame,
) -> None:
    result = walk_forward_portfolio_evaluate(
        returns,
        lookback=60,
        rebalance_every=10,
        cost_bps=12.0,
        max_weight=0.5,
    )

    assert result["strategy"].tolist() == [
        "equal_weight",
        "sample_minimum_variance",
        "shrinkage_turnover_aware",
    ]
    assert result["observations"].eq(120).all()
    assert result["test_start"].eq(str(returns.index[60])).all()
    assert result["test_end"].eq(str(returns.index[-1])).all()
    assert result["gross_turnover"].gt(0).all()
    assert result["estimated_cost_fraction"].gt(0).all()
    assert result["total_return"].map(np.isfinite).all()


def test_transaction_costs_reduce_returns_and_are_consistent(
    returns: pd.DataFrame,
) -> None:
    free = walk_forward_portfolio_evaluate(
        returns, lookback=60, rebalance_every=10, cost_bps=0.0, max_weight=0.5
    )
    charged = walk_forward_portfolio_evaluate(
        returns, lookback=60, rebalance_every=10, cost_bps=20.0, max_weight=0.5
    )

    assert charged["estimated_cost_fraction"].gt(0).all()
    assert (charged["total_return"] < free["total_return"]).all()
    assert charged["gross_turnover"].tolist() == pytest.approx(
        free["gross_turnover"].tolist()
    )


def test_evaluator_is_deterministic(returns: pd.DataFrame) -> None:
    kwargs = {"lookback": 60, "rebalance_every": 15, "cost_bps": 8.0, "max_weight": 0.5}
    first = walk_forward_portfolio_evaluate(returns, **kwargs)
    second = walk_forward_portfolio_evaluate(returns, **kwargs)
    pd.testing.assert_frame_equal(first, second)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"lookback": 1}, "lookback"),
        ({"rebalance_every": 0}, "rebalance_every"),
        ({"cost_bps": -1.0}, "cost_bps"),
        ({"cost_bps": 10000.0, "lookback": 60}, "cost_bps"),
        ({"max_weight": 0.0}, "max_weight"),
        ({"max_weight": 0.2}, "too small"),
    ],
)
def test_evaluator_rejects_invalid_configuration(
    returns: pd.DataFrame, kwargs: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        walk_forward_portfolio_evaluate(returns, **kwargs)


def test_evaluator_rejects_invalid_return_data() -> None:
    invalid = pd.DataFrame({"A": [0.01, np.nan, 0.02], "B": [0.01, 0.02, 0.03]})
    with pytest.raises(ValueError, match="complete and finite"):
        walk_forward_portfolio_evaluate(invalid, lookback=2)

    invalid = pd.DataFrame({"A": [0.01, -1.0, 0.02], "B": [0.01, 0.02, 0.03]})
    with pytest.raises(ValueError, match="greater than -100%"):
        walk_forward_portfolio_evaluate(invalid, lookback=2)


def test_evaluator_rejects_unsorted_or_duplicate_timestamps() -> None:
    index = pd.date_range("2025-01-01", periods=20, freq="B")
    values = pd.DataFrame({"A": np.linspace(0.001, 0.02, 20), "B": np.linspace(0.002, 0.01, 20)}, index=index)
    with pytest.raises(ValueError, match="chronological"):
        walk_forward_portfolio_evaluate(values.iloc[::-1], lookback=5, max_weight=0.6)
    duplicated = pd.concat([values, values.iloc[[4]]])
    with pytest.raises(ValueError, match="chronological"):
        walk_forward_portfolio_evaluate(duplicated, lookback=5, max_weight=0.6)
