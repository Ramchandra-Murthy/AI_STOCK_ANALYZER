from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from ai_trading.mean_reversion_quality_gate import evaluate_mean_reversion_quality


def _evidence(*, trades=(4, 5, 3), profit_factor=1.4):
    folds = pd.DataFrame(
        {
            "total_return": [0.03, 0.02, 0.01],
            "trade_count": list(trades),
        }
    )
    walk_forward = SimpleNamespace(
        fold_metrics=folds,
        positive_fold_fraction=1.0,
    )
    tournament = {
        "observations": 100,
        "sharpe_ratio": 1.2,
        "max_drawdown": 0.12,
        "profit_factor": profit_factor,
    }
    slippage = pd.DataFrame({"net_return": [0.12, 0.08, 0.03]})
    parameters = pd.DataFrame(
        {"total_return": [0.1, 0.08], "sharpe_ratio": [1.1, 0.9]}
    )
    return tournament, walk_forward, slippage, parameters


def test_mean_reversion_quality_gate_passes_complete_evidence():
    tournament, walk_forward, slippage, parameters = _evidence()
    result = evaluate_mean_reversion_quality(
        tournament,
        walk_forward,
        slippage_report=slippage,
        parameter_report=parameters,
    )
    assert result["status"] == "eligible_for_paper_trading"
    assert result["checks_passed"]
    assert result["total_out_of_sample_trades"] == 12
    assert result["positive_fold_fraction"] == 1.0
    assert result["live_trading_authorized"] is False


def test_insufficient_out_of_sample_trades_remain_research_only():
    tournament, walk_forward, slippage, parameters = _evidence(trades=(2, 1, 2))
    result = evaluate_mean_reversion_quality(
        tournament,
        walk_forward,
        slippage_report=slippage,
        parameter_report=parameters,
        min_total_trades=10,
    )
    assert result["status"] == "research_only"
    assert any("minimum out-of-sample trades" in item for item in result["missing_evidence"])


def test_profit_factor_below_threshold_fails_validation():
    tournament, walk_forward, slippage, parameters = _evidence(profit_factor=0.8)
    result = evaluate_mean_reversion_quality(
        tournament,
        walk_forward,
        slippage_report=slippage,
        parameter_report=parameters,
    )
    assert result["status"] == "failed_validation"
    assert any("profit factor" in item for item in result["reasons"])


def test_missing_profit_factor_remains_research_only():
    tournament, walk_forward, slippage, parameters = _evidence()
    tournament.pop("profit_factor")
    result = evaluate_mean_reversion_quality(
        tournament,
        walk_forward,
        slippage_report=slippage,
        parameter_report=parameters,
    )
    assert result["status"] == "research_only"
    assert "profit factor" in result["missing_evidence"]


def test_invalid_trade_threshold_is_rejected():
    tournament, walk_forward, slippage, parameters = _evidence()
    with pytest.raises(ValueError, match="min_total_trades"):
        evaluate_mean_reversion_quality(
            tournament,
            walk_forward,
            slippage_report=slippage,
            parameter_report=parameters,
            min_total_trades=0,
        )


def test_invalid_profit_factor_threshold_is_rejected():
    tournament, walk_forward, slippage, parameters = _evidence()
    with pytest.raises(ValueError, match="min_profit_factor"):
        evaluate_mean_reversion_quality(
            tournament,
            walk_forward,
            slippage_report=slippage,
            parameter_report=parameters,
            min_profit_factor=-1.0,
        )
