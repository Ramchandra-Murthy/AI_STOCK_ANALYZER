"""Tests for backtest trade-return distribution diagnostics."""

import numpy as np
import pandas as pd
import pytest

from neural_networks.strategy_backtest import summarize_backtest_trade_distribution


def test_trade_distribution_reports_net_trade_statistics() -> None:
    trades = pd.DataFrame({"Net return after costs": [0.10, -0.05, 0.0, 0.15, -0.10]})

    summary = summarize_backtest_trade_distribution(trades)
    row = summary.iloc[0]

    assert row["Trades"] == 5
    assert row["Win rate"] == pytest.approx(0.4)
    assert row["Mean net return"] == pytest.approx(0.02)
    assert row["Median net return"] == pytest.approx(0.0)
    assert row["Best net trade"] == pytest.approx(0.15)
    assert row["Worst net trade"] == pytest.approx(-0.10)
    assert row["Profit factor"] == pytest.approx(0.25 / 0.15)
    assert row["Gross profit from winning trades"] == pytest.approx(0.25)
    assert row["Gross loss from losing trades"] == pytest.approx(0.15)


def test_trade_distribution_handles_empty_trade_list() -> None:
    summary = summarize_backtest_trade_distribution(
        pd.DataFrame(columns=["Net return after costs"])
    )

    assert summary.iloc[0]["Trades"] == 0
    assert np.isnan(summary.iloc[0]["Win rate"])
    assert np.isnan(summary.iloc[0]["Mean net return"])
    assert np.isnan(summary.iloc[0]["Profit factor"])


def test_profit_factor_is_undefined_when_there_are_no_losing_trades() -> None:
    summary = summarize_backtest_trade_distribution(
        pd.DataFrame({"Net return after costs": [0.02, 0.05, 0.0]})
    )

    assert np.isnan(summary.iloc[0]["Profit factor"])


@pytest.mark.parametrize("invalid", [np.nan, np.inf, -np.inf, "bad"])
def test_trade_distribution_rejects_invalid_returns(invalid: object) -> None:
    trades = pd.DataFrame({"Net return after costs": [0.02, invalid]})

    with pytest.raises(ValueError, match="must be finite numeric values"):
        summarize_backtest_trade_distribution(trades)


def test_trade_distribution_requires_net_return_column() -> None:
    with pytest.raises(ValueError, match="missing columns"):
        summarize_backtest_trade_distribution(pd.DataFrame({"Gross return": [0.1]}))
