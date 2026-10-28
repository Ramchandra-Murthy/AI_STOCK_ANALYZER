"""Tests for slippage sensitivity diagnostics."""

import pandas as pd
import pytest

from ai_trading.slippage_sensitivity import (
    slippage_sensitivity,
    slippage_sensitivity_summary,
)


def test_slippage_sensitivity_measures_execution_drag() -> None:
    returns = pd.Series([0.02, -0.01, 0.03])
    turnover = pd.Series([1.0, 2.0, 1.0])

    report = slippage_sensitivity(
        returns,
        turnover=turnover,
        slippage_bps=(0.0, 10.0),
    )

    assert report["slippage_bps"].tolist() == [0.0, 10.0]
    assert report["total_turnover"].tolist() == [4.0, 4.0]
    assert report.loc[0, "net_return"] == pytest.approx((1.02 * 0.99 * 1.03) - 1.0)
    assert report.loc[1, "slippage_drag"] > 0.0
    assert report.loc[1, "net_return"] < report.loc[0, "net_return"]


def test_slippage_sensitivity_summary_returns_worst_case() -> None:
    result = slippage_sensitivity_summary(
        pd.Series([0.01, 0.02]),
        turnover=pd.Series([1.0, 1.0]),
        slippage_bps=(0.0, 20.0),
    )

    assert result["gross_return"] == pytest.approx(0.0302)
    assert result["worst_slippage_bps"] == 20.0
    assert result["worst_net_return"] < result["gross_return"]


def test_slippage_sensitivity_rejects_invalid_assumptions() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        slippage_sensitivity(pd.Series([0.01]), slippage_bps=(-1.0,))

@pytest.mark.parametrize("bad_rate", [float("nan"), float("inf"), float("-inf")])
def test_slippage_sensitivity_rejects_non_finite_rates(bad_rate: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        slippage_sensitivity(pd.Series([0.01]), slippage_bps=(bad_rate,))


@pytest.mark.parametrize("bad_return", [float("nan"), float("inf"), float("-inf")])
def test_slippage_sensitivity_rejects_non_finite_returns(bad_return: float) -> None:
    with pytest.raises(ValueError, match="returns must contain only finite"):
        slippage_sensitivity(pd.Series([bad_return]))


@pytest.mark.parametrize("bad_turnover", [float("nan"), float("inf"), float("-inf")])
def test_slippage_sensitivity_rejects_non_finite_turnover(bad_turnover: float) -> None:
    with pytest.raises(ValueError, match="turnover must contain only finite"):
        slippage_sensitivity(
            pd.Series([0.01]),
            turnover=pd.Series([bad_turnover]),
        )


def test_slippage_sensitivity_rejects_unaligned_turnover() -> None:
    returns = pd.Series([0.01, 0.02], index=[0, 1])
    turnover = pd.Series([1.0], index=[0])

    with pytest.raises(ValueError, match="turnover must contain only finite"):
        slippage_sensitivity(returns, turnover=turnover)
