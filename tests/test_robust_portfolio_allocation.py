"""Tests for shrinkage-based cost-aware portfolio allocation."""

import numpy as np
import pandas as pd
import pytest

from algorithmic_trading.robust_portfolio_allocation import (
    cost_aware_minimum_variance_weights,
    estimate_rebalance_cost,
    shrinkage_covariance,
)


@pytest.fixture
def returns() -> pd.DataFrame:
    rng = np.random.default_rng(41)
    common = rng.normal(0.0, 0.01, 120)
    return pd.DataFrame(
        {
            "A": common + rng.normal(0.0, 0.002, 120),
            "B": common * 0.9 + rng.normal(0.0, 0.003, 120),
            "C": rng.normal(0.0, 0.006, 120),
            "D": rng.normal(0.0, 0.008, 120),
        },
        index=pd.date_range("2025-01-01", periods=120, freq="B"),
    )


def test_shrinkage_covariance_is_symmetric_and_finite(returns: pd.DataFrame) -> None:
    covariance = shrinkage_covariance(returns, shrinkage=0.4)

    assert covariance.index.tolist() == returns.columns.tolist()
    assert covariance.columns.tolist() == returns.columns.tolist()
    assert np.isfinite(covariance.to_numpy()).all()
    assert np.allclose(covariance.to_numpy(), covariance.to_numpy().T)
    assert np.linalg.eigvalsh(covariance.to_numpy()).min() > 0.0


def test_cost_aware_weights_respect_simplex_and_position_caps(
    returns: pd.DataFrame,
) -> None:
    weights = cost_aware_minimum_variance_weights(returns, max_weight=0.35)

    assert weights.sum() == pytest.approx(1.0)
    assert weights.min() >= 0.0
    assert weights.max() <= 0.35 + 1e-10


def test_turnover_penalty_keeps_weights_near_current_allocation(
    returns: pd.DataFrame,
) -> None:
    current = pd.Series({"A": 0.25, "B": 0.25, "C": 0.25, "D": 0.25})
    unconstrained = cost_aware_minimum_variance_weights(
        returns,
        previous_weights=current,
        turnover_penalty=0.0,
        max_weight=0.35,
    )
    penalized = cost_aware_minimum_variance_weights(
        returns,
        previous_weights=current,
        turnover_penalty=0.01,
        max_weight=0.35,
    )

    assert (penalized - current).abs().sum() <= (unconstrained - current).abs().sum() + 1e-10


def test_optimizer_is_deterministic(returns: pd.DataFrame) -> None:
    first = cost_aware_minimum_variance_weights(returns)
    second = cost_aware_minimum_variance_weights(returns)

    pd.testing.assert_series_equal(first, second)


def test_optimizer_rejects_infeasible_cap(returns: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="too small"):
        cost_aware_minimum_variance_weights(returns, max_weight=0.20)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"shrinkage": -0.1},
        {"shrinkage": 1.1},
        {"ridge": 0.0},
        {"max_weight": 0.0},
        {"turnover_penalty": -1.0},
        {"tolerance": 0.0},
        {"max_iter": 0},
    ],
)
def test_optimizer_rejects_invalid_configuration(
    returns: pd.DataFrame,
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        cost_aware_minimum_variance_weights(returns, **kwargs)


def test_optimizer_rejects_invalid_previous_weights(returns: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="sum to 1"):
        cost_aware_minimum_variance_weights(
            returns,
            previous_weights=pd.Series({"A": 0.4, "B": 0.4}),
        )
    with pytest.raises(ValueError, match="unknown assets"):
        cost_aware_minimum_variance_weights(
            returns,
            previous_weights=pd.Series({"A": 0.25, "B": 0.25, "C": 0.25, "UNKNOWN": 0.25}),
        )


@pytest.mark.parametrize(
    "returns",
    [
        pd.DataFrame({"A": [0.01, np.nan, 0.02], "B": [0.01, 0.02, 0.03]}),
        pd.DataFrame({"A": [0.01, np.inf, 0.02], "B": [0.01, 0.02, 0.03]}),
        pd.DataFrame({"A": [0.01, -1.1, 0.02], "B": [0.01, 0.02, 0.03]}),
        pd.DataFrame({"A": ["bad", 0.01, 0.02], "B": [0.01, 0.02, 0.03]}),
    ],
)
def test_optimizer_rejects_invalid_return_data(returns: pd.DataFrame) -> None:
    with pytest.raises(ValueError):
        cost_aware_minimum_variance_weights(returns)


def test_estimate_rebalance_cost_includes_buys_and_sells() -> None:
    current = pd.Series({"A": 0.6, "B": 0.4})
    target = pd.Series({"A": 0.4, "B": 0.6})

    result = estimate_rebalance_cost(target, current, cost_bps=25.0)

    assert result["gross_turnover"] == pytest.approx(0.4)
    assert result["estimated_cost_fraction"] == pytest.approx(0.001)
    assert result["estimated_cost_bps_of_nav"] == pytest.approx(10.0)


def test_estimate_rebalance_cost_rejects_negative_cost() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        estimate_rebalance_cost(
            pd.Series({"A": 1.0}),
            pd.Series({"A": 1.0}),
            cost_bps=-1.0,
        )


def test_optimizer_matches_independent_two_asset_grid_search() -> None:
    rng = np.random.default_rng(2026)
    returns = pd.DataFrame(
        {
            "A": rng.normal(0.0005, 0.012, 180),
            "B": rng.normal(0.0002, 0.007, 180),
        }
    )
    covariance = shrinkage_covariance(returns, shrinkage=0.15).to_numpy()
    weights = cost_aware_minimum_variance_weights(
        returns,
        shrinkage=0.15,
        max_weight=0.8,
        tolerance=1e-12,
    ).to_numpy()
    actual_variance = float(weights @ covariance @ weights)

    grid = np.linspace(0.2, 0.8, 30_001)
    candidates = np.column_stack([grid, 1.0 - grid])
    grid_variances = np.einsum("ij,jk,ik->i", candidates, covariance, candidates)

    assert actual_variance <= float(grid_variances.min()) + 1e-12


def test_optimizer_handles_zero_variance_and_highly_correlated_assets() -> None:
    constant = np.full(80, 0.01)
    varying = np.linspace(-0.02, 0.02, 80)
    returns = pd.DataFrame(
        {
            "constant_a": constant,
            "constant_b": constant.copy(),
            "correlated_a": varying,
            "correlated_b": varying * 0.999 + 1e-7 * np.sin(np.arange(80)),
        }
    )

    covariance = shrinkage_covariance(returns, shrinkage=0.2)
    weights = cost_aware_minimum_variance_weights(returns, max_weight=0.4)

    assert np.isfinite(covariance.to_numpy()).all()
    assert np.linalg.eigvalsh(covariance.to_numpy()).min() > 0.0
    assert weights.sum() == pytest.approx(1.0)
    assert weights.min() >= 0.0
    assert weights.max() <= 0.4 + 1e-10


@pytest.mark.parametrize(
    ("target", "current"),
    [
        ({"A": 0.8, "B": 0.1}, {"A": 0.6, "B": 0.4}),
        ({"A": 0.5, "B": 0.5}, {"A": -0.1, "B": 1.1}),
        ({"A": np.nan, "B": 0.0}, {"A": 0.5, "B": 0.5}),
    ],
)
def test_estimate_rebalance_cost_rejects_invalid_portfolio_weights(
    target: dict[str, float],
    current: dict[str, float],
) -> None:
    with pytest.raises(ValueError):
        estimate_rebalance_cost(
            pd.Series(target),
            pd.Series(current),
            cost_bps=20.0,
        )


def test_estimate_rebalance_cost_requires_series_inputs() -> None:
    with pytest.raises(ValueError, match="pandas Series"):
        estimate_rebalance_cost(
            {"A": 1.0},  # type: ignore[arg-type]
            pd.Series({"A": 1.0}),
            cost_bps=20.0,
        )
