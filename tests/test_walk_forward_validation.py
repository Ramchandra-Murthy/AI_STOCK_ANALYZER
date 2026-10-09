import pandas as pd
import pytest

from algorithmic_trading.walk_forward_validation import walk_forward_evaluate


def test_walk_forward_evaluates_sequential_non_overlapping_folds() -> None:
    index = pd.date_range("2020-01-01", periods=22, freq="D")
    prices = pd.Series([100.0 + i for i in range(22)], index=index)
    signals = pd.Series(1.0, index=index)

    result = walk_forward_evaluate(
        prices,
        signals,
        min_train_size=10,
        n_splits=3,
        cost_bps=0,
    )

    assert result["fold"].tolist() == [1, 2, 3]
    assert result["observations"].tolist() == [4, 4, 4]
    assert result["test_start"].tolist() == [
        str(index[10]),
        str(index[14]),
        str(index[18]),
    ]
    assert (result["total_return"] > 0).all()
    assert {
        "annualized_volatility",
        "sharpe_ratio",
        "sortino_ratio",
        "calmar_ratio",
    }.issubset(result.columns)
    assert (result["annualized_volatility"] >= 0).all()


def test_walk_forward_risk_ratios_are_nan_when_undefined() -> None:
    index = pd.date_range("2020-01-01", periods=14, freq="D")
    prices = pd.Series(100.0, index=index)
    signals = pd.Series(0.0, index=index)

    result = walk_forward_evaluate(
        prices,
        signals,
        min_train_size=8,
        n_splits=3,
        cost_bps=0,
    )

    assert result["sharpe_ratio"].isna().all()
    assert result["sortino_ratio"].isna().all()
    assert result["calmar_ratio"].isna().all()


def test_walk_forward_rejects_too_short_history() -> None:
    index = pd.date_range("2026-01-01", periods=4, freq="D")
    prices = pd.Series([100.0, 101.0, 102.0, 103.0], index=index)
    signals = pd.Series(1.0, index=index)

    with pytest.raises(ValueError, match="not enough observations"):
        walk_forward_evaluate(prices, signals, min_train_size=4)


def test_walk_forward_rejects_folds_that_are_too_short() -> None:
    index = pd.date_range("2026-01-01", periods=8, freq="D")
    prices = pd.Series([100.0 + i for i in range(8)], index=index)
    signals = pd.Series(1.0, index=index)

    with pytest.raises(ValueError, match="each test fold"):
        walk_forward_evaluate(prices, signals, min_train_size=4, n_splits=3)
