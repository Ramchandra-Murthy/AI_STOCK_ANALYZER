"""Tests for combinatorially symmetric strategy-selection diagnostics."""

import numpy as np
import pandas as pd
import pytest

from ai_trading.strategy_selection_bias import probability_of_backtest_overfitting


def test_pbo_returns_all_combinatorial_splits_and_bounded_probability() -> None:
    index = pd.date_range("2024-01-01", periods=80, freq="B")
    rng = np.random.default_rng(17)
    returns = pd.DataFrame(
        {
            f"strategy_{number}": rng.normal(0.0005 * number, 0.01, len(index))
            for number in range(5)
        },
        index=index,
    )

    summary, splits = probability_of_backtest_overfitting(returns, n_blocks=8)

    assert summary["split_count"] == 70
    assert summary["strategy_count"] == 5
    assert summary["observation_count"] == 80
    assert 0.0 <= summary["probability_of_backtest_overfitting"] <= 1.0
    assert len(splits) == 70
    assert splits["omega"].between(0.0, 1.0, inclusive="neither").all()


def test_pbo_is_deterministic_for_same_input() -> None:
    returns = pd.DataFrame(
        {
            "trend": np.tile([0.02, 0.01, -0.01, -0.02], 10),
            "reversal": np.tile([-0.01, -0.02, 0.02, 0.01], 10),
        }
    )

    first_summary, first_splits = probability_of_backtest_overfitting(returns)
    second_summary, second_splits = probability_of_backtest_overfitting(returns)

    assert first_summary == second_summary
    pd.testing.assert_frame_equal(first_splits, second_splits)


@pytest.mark.parametrize("n_blocks", [True, 3, 5, 0, 8.0])
def test_pbo_rejects_invalid_block_count(n_blocks) -> None:
    returns = pd.DataFrame({"a": np.zeros(32), "b": np.ones(32) * 0.001})

    with pytest.raises(ValueError, match="n_blocks"):
        probability_of_backtest_overfitting(returns, n_blocks=n_blocks)


def test_pbo_rejects_insufficient_observations() -> None:
    returns = pd.DataFrame({"a": np.zeros(15), "b": np.ones(15) * 0.001})

    with pytest.raises(ValueError, match="two observations per block"):
        probability_of_backtest_overfitting(returns)


@pytest.mark.parametrize(
    "returns",
    [
        pd.DataFrame({"a": [0.01, np.nan] * 20, "b": [0.02, 0.01] * 20}),
        pd.DataFrame({"a": [0.01, np.inf] * 20, "b": [0.02, 0.01] * 20}),
        pd.DataFrame({"a": [0.01, -1.01] * 20, "b": [0.02, 0.01] * 20}),
        pd.DataFrame({"a": ["bad", 0.01] * 20, "b": [0.02, 0.01] * 20}),
    ],
)
def test_pbo_rejects_invalid_or_incomplete_returns(returns) -> None:
    with pytest.raises(ValueError):
        probability_of_backtest_overfitting(returns)


def test_pbo_rejects_duplicate_or_unordered_timestamps() -> None:
    duplicate_index = pd.DataFrame(
        {"a": np.zeros(40), "b": np.ones(40) * 0.001},
        index=[0, 0, *range(2, 40)],
    )
    unordered_index = pd.DataFrame(
        {"a": np.zeros(40), "b": np.ones(40) * 0.001},
        index=list(range(20)) + list(range(39, 19, -1)),
    )

    with pytest.raises(ValueError, match="unique, chronological"):
        probability_of_backtest_overfitting(duplicate_index)
    with pytest.raises(ValueError, match="unique, chronological"):
        probability_of_backtest_overfitting(unordered_index)


def test_pbo_rejects_invalid_risk_parameters() -> None:
    returns = pd.DataFrame({"a": np.zeros(40), "b": np.ones(40) * 0.001})

    with pytest.raises(ValueError, match="periods_per_year"):
        probability_of_backtest_overfitting(returns, periods_per_year=0)
    with pytest.raises(ValueError, match="risk_free_rate"):
        probability_of_backtest_overfitting(returns, risk_free_rate=-1.0)
