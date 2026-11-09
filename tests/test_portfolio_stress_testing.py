"""Tests for deterministic portfolio scenario stress testing."""

import numpy as np
import pandas as pd
import pytest

from algorithmic_trading.stress_testing import run_portfolio_stress_scenarios


def test_stress_scenarios_calculate_weighted_pnl_and_worst_contributor() -> None:
    weights = pd.Series({"A": 0.6, "B": 0.3, "C": 0.1})
    scenarios = {
        "market_selloff": {"A": -0.10, "B": -0.20, "C": -0.30},
        "single_name_shock": {"B": -0.50},
    }

    result = run_portfolio_stress_scenarios(
        weights, scenarios, portfolio_value=1_000_000.0
    )

    assert result.loc["market_selloff", "portfolio_return"] == pytest.approx(-0.15)
    assert result.loc["market_selloff", "pnl"] == pytest.approx(-150_000.0)
    assert result.loc["market_selloff", "portfolio_value_after"] == pytest.approx(850_000.0)
    assert result.loc["market_selloff", "worst_contributor"] == "C"
    assert result.loc["single_name_shock", "portfolio_return"] == pytest.approx(-0.15)
    assert result.loc["single_name_shock", "worst_contributor"] == "B"


def test_missing_asset_shocks_are_zero() -> None:
    weights = pd.Series({"A": 0.7, "B": 0.3})

    result = run_portfolio_stress_scenarios(weights, {"A_only": {"A": 0.10}})

    assert result.loc["A_only", "portfolio_return"] == pytest.approx(0.07)
    assert result.loc["A_only", "pnl"] == pytest.approx(0.07)


def test_zero_shock_scenario_preserves_portfolio_value() -> None:
    weights = pd.Series({"A": 0.5, "B": 0.5})

    result = run_portfolio_stress_scenarios(weights, {"flat": {}})

    assert result.loc["flat", "portfolio_return"] == 0.0
    assert result.loc["flat", "portfolio_value_after"] == 1.0


@pytest.mark.parametrize(
    "weights",
    [
        pd.Series(dtype=float),
        pd.Series({"A": 0.7, "B": 0.2}),
        pd.Series({"A": -0.1, "B": 1.1}),
        pd.Series({"A": np.nan, "B": 1.0}),
        pd.Series({"A": 0.5, "A": 0.5}),
    ],
)
def test_invalid_weights_are_rejected(weights: pd.Series) -> None:
    with pytest.raises(ValueError):
        run_portfolio_stress_scenarios(weights, {"stress": {"A": -0.1}})


@pytest.mark.parametrize("shock", [-1.01, np.inf, np.nan, "invalid", True])
def test_invalid_scenario_returns_are_rejected(shock: object) -> None:
    weights = pd.Series({"A": 0.5, "B": 0.5})

    with pytest.raises(ValueError, match="returns must be finite"):
        run_portfolio_stress_scenarios(weights, {"stress": {"A": shock}})


def test_total_loss_is_bounded_at_negative_one_hundred_percent() -> None:
    weights = pd.Series({"A": 0.4, "B": 0.6})

    result = run_portfolio_stress_scenarios(
        weights, {"total_loss": {"A": -1.0, "B": -1.0}}, portfolio_value=250_000
    )

    assert result.loc["total_loss", "portfolio_return"] == pytest.approx(-1.0)
    assert result.loc["total_loss", "portfolio_value_after"] == pytest.approx(0.0)


def test_unknown_symbols_and_invalid_scenario_names_are_rejected() -> None:
    weights = pd.Series({"A": 1.0})

    with pytest.raises(ValueError, match="unknown assets"):
        run_portfolio_stress_scenarios(weights, {"bad": {"UNKNOWN": -0.1}})
    with pytest.raises(ValueError, match="scenario names"):
        run_portfolio_stress_scenarios(weights, {"": {"A": -0.1}})


def test_portfolio_value_must_be_positive_and_finite() -> None:
    weights = pd.Series({"A": 1.0})

    for value in (0.0, -1.0, np.inf, np.nan):
        with pytest.raises(ValueError, match="portfolio_value"):
            run_portfolio_stress_scenarios(weights, {"stress": {"A": -0.1}}, portfolio_value=value)
