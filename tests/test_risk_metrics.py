"""Tests for book-aligned EROS risk and performance metrics."""

import numpy as np
import pandas as pd
import pytest

from ai_trading.risk_metrics import (
    annualized_volatility,
    conditional_value_at_risk,
    max_drawdown,
    omega_ratio,
    risk_performance_summary,
    sharpe_ratio,
)


def test_annualized_volatility_and_sharpe_are_positive_for_positive_returns() -> None:
    returns = pd.Series([0.01, 0.02, -0.005, 0.015, 0.01])
    assert annualized_volatility(returns) > 0.0
    assert sharpe_ratio(returns) > 0.0


def test_max_drawdown_matches_equity_path() -> None:
    returns = pd.Series([0.10, -0.05, -0.10, 0.02])
    expected = 1.0 - (1.10 * 0.95 * 0.90) / 1.10
    assert max_drawdown(returns) == pytest.approx(expected)


def test_omega_ratio_uses_positive_and_negative_excess_returns() -> None:
    returns = pd.Series([0.02, -0.02, 0.03, -0.03])
    assert omega_ratio(returns) == pytest.approx(1.0)


def test_cvar_is_tail_loss_magnitude() -> None:
    returns = pd.Series([0.02, 0.01, -0.01, -0.04, -0.08])
    assert conditional_value_at_risk(returns, confidence=0.8) > 0.04


def test_summary_contains_composite_metrics() -> None:
    summary = risk_performance_summary(pd.Series([0.01, -0.005, 0.02, -0.01]))
    assert set(summary) == {
        "annualized_volatility",
        "sharpe_ratio",
        "omega_ratio",
        "conditional_value_at_risk",
        "max_drawdown",
    }


def test_invalid_parameters_are_rejected() -> None:
    with pytest.raises(ValueError):
        annualized_volatility(pd.Series([0.01, 0.02]), periods_per_year=0)
    with pytest.raises(ValueError):
        conditional_value_at_risk(pd.Series([0.01, 0.02]), confidence=1.0)


@pytest.mark.parametrize("infinite", [float("inf"), float("-inf")])
def test_risk_metrics_reject_infinite_returns(infinite: float) -> None:
    returns = pd.Series([0.01, infinite, -0.02])

    with pytest.raises(ValueError, match="finite"):
        annualized_volatility(returns)
    with pytest.raises(ValueError, match="finite"):
        sharpe_ratio(returns)
    with pytest.raises(ValueError, match="finite"):
        omega_ratio(returns)
    with pytest.raises(ValueError, match="finite"):
        conditional_value_at_risk(returns)
    with pytest.raises(ValueError, match="finite"):
        max_drawdown(returns)


@pytest.mark.parametrize(
    ("metric", "kwargs"),
    [
        (annualized_volatility, {"periods_per_year": float("nan")}),
        (annualized_volatility, {"periods_per_year": float("inf")}),
        (sharpe_ratio, {"periods_per_year": float("nan")}),
        (sharpe_ratio, {"risk_free_rate": float("inf")}),
        (sharpe_ratio, {"risk_free_rate": -1.0}),
        (omega_ratio, {"threshold": float("nan")}),
        (conditional_value_at_risk, {"confidence": float("nan")}),
    ],
)
def test_risk_metrics_reject_non_finite_or_invalid_parameters(metric, kwargs) -> None:
    with pytest.raises(ValueError):
        metric(pd.Series([0.01, -0.02, 0.03]), **kwargs)


@pytest.mark.parametrize(
    "metric",
    [
        annualized_volatility,
        sharpe_ratio,
        omega_ratio,
        conditional_value_at_risk,
        max_drawdown,
    ],
)
def test_risk_metrics_reject_returns_below_minus_100_percent(metric) -> None:
    with pytest.raises(ValueError, match="below -100%"):
        metric(pd.Series([0.02, -1.01, -0.03]))


def test_risk_metrics_accept_exact_minus_100_percent_loss() -> None:
    returns = pd.Series([0.10, -1.0, 0.05])

    assert max_drawdown(returns) == pytest.approx(1.0)
    assert conditional_value_at_risk(returns, confidence=0.5) >= 0.0


@pytest.mark.parametrize(
    ("metric", "kwargs"),
    [
        (annualized_volatility, {"periods_per_year": True}),
        (annualized_volatility, {"periods_per_year": np.bool_(False)}),
        (sharpe_ratio, {"risk_free_rate": True}),
        (sharpe_ratio, {"periods_per_year": "invalid"}),
        (omega_ratio, {"threshold": False}),
        (omega_ratio, {"threshold": "invalid"}),
        (conditional_value_at_risk, {"confidence": True}),
        (conditional_value_at_risk, {"confidence": "invalid"}),
    ],
)
def test_risk_metrics_reject_boolean_and_non_numeric_parameters(metric, kwargs) -> None:
    with pytest.raises(ValueError, match="finite and numeric"):
        metric(pd.Series([0.01, -0.02, 0.03]), **kwargs)


def test_max_drawdown_rejects_equity_curve_overflow() -> None:
    returns = pd.Series([1e308, 1e308])

    with pytest.raises(ValueError, match="equity curve overflowed"):
        max_drawdown(returns)


def test_omega_ratio_rejects_excess_return_overflow() -> None:
    returns = pd.Series([1e308, -0.5])

    with pytest.raises(ValueError, match="excess returns overflowed"):
        omega_ratio(returns, threshold=-1e308)


def test_omega_ratio_rejects_gain_total_overflow() -> None:
    returns = pd.Series([1e308, 1e308])

    with pytest.raises(ValueError, match="gain/loss totals overflowed"):
        omega_ratio(returns)


def test_annualized_volatility_rejects_result_overflow() -> None:
    returns = pd.Series([1e308, -0.5])

    with pytest.raises(ValueError, match="annualized volatility overflowed"):
        annualized_volatility(returns)


def test_sharpe_ratio_rejects_result_overflow() -> None:
    returns = pd.Series([1e308, -0.5])

    with pytest.raises(ValueError, match="Sharpe ratio volatility overflowed"):
        sharpe_ratio(returns)


def test_sharpe_ratio_rejects_risk_free_rate_annualization_overflow() -> None:
    returns = pd.Series([0.01, -0.02, 0.03])

    with pytest.raises(ValueError, match="risk-free rate calculation"):
        sharpe_ratio(returns, periods_per_year=1e-320)


def test_cvar_rejects_tail_mean_overflow() -> None:
    returns = pd.Series([1e308, 1e308])

    with pytest.raises(ValueError, match="CVaR tail mean"):
        conditional_value_at_risk(returns, confidence=0.5)


def test_omega_ratio_rejects_result_overflow() -> None:
    returns = pd.Series([1e308, -1e-10])

    with pytest.raises(ValueError, match="omega ratio calculation produced a non-finite result"):
        omega_ratio(returns)
