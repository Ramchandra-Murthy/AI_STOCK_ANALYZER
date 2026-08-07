from __future__ import annotations

import pytest
from services.backtesting.models import BacktestResult
from services.backtesting.strategy_engine import BacktestingEngine

def test_backtest_result_immutability() -> None:
    res = BacktestResult(
        strategy_name="Core Growth",
        cagr=0.18,
        sharpe_ratio=1.40,
        max_drawdown=-0.08,
        alpha=0.05,
        beta=0.95,
        information_ratio=1.20,
        win_rate=0.70
    )
    assert res.strategy_name == "Core Growth"
    assert res.cagr == 0.18
    assert res.timestamp is not None
    assert isinstance(res.metrics, dict)

def test_backtesting_engine() -> None:
    result = BacktestingEngine.run_backtest("Institutional Multi-Factor")
    assert result.strategy_name == "Institutional Multi-Factor"
    assert result.cagr > 0.10
    assert result.sharpe_ratio > 1.0
    assert result.max_drawdown < 0
    assert len(result.metrics) > 0
