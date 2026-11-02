from __future__ import annotations

import pandas as pd
import pytest

from ai_trading.strategy_quality_gate import evaluate_strategy_quality


def _evidence():
    return (
        {"observations": 100, "sharpe_ratio": 1.2, "max_drawdown": 0.12},
        pd.DataFrame({"total_return": [0.02, 0.01, -0.005, 0.03]}),
        pd.DataFrame({"net_return": [0.12, 0.08, 0.03]}),
        pd.DataFrame({"total_return": [0.1, 0.08], "sharpe_ratio": [1.1, 0.9]}),
    )


def test_quality_gate_passes_complete_robust_evidence():
    tournament, walk_forward, slippage, parameters = _evidence()
    result = evaluate_strategy_quality(
        tournament,
        walk_forward_metrics=walk_forward,
        slippage_report=slippage,
        parameter_report=parameters,
    )
    assert result["status"] == "eligible_for_paper_trading"
    assert result["checks_passed"]
    assert result["live_trading_authorized"] is False


def test_missing_evidence_keeps_strategy_research_only():
    tournament, _, _, _ = _evidence()
    result = evaluate_strategy_quality(
        tournament,
        walk_forward_metrics=None,
        slippage_report=None,
        parameter_report=None,
    )
    assert result["status"] == "research_only"
    assert len(result["missing_evidence"]) == 3


def test_failed_drawdown_threshold_is_reported():
    tournament, walk_forward, slippage, parameters = _evidence()
    tournament["max_drawdown"] = 0.4
    result = evaluate_strategy_quality(
        tournament,
        walk_forward_metrics=walk_forward,
        slippage_report=slippage,
        parameter_report=parameters,
    )
    assert result["status"] == "failed_validation"
    assert any("drawdown" in reason for reason in result["reasons"])


def test_negative_worst_case_slippage_fails_validation():
    tournament, walk_forward, slippage, parameters = _evidence()
    slippage.loc[2, "net_return"] = -0.01
    result = evaluate_strategy_quality(
        tournament,
        walk_forward_metrics=walk_forward,
        slippage_report=slippage,
        parameter_report=parameters,
    )
    assert result["status"] == "failed_validation"
    assert any("slippage" in reason for reason in result["reasons"])


def test_invalid_threshold_is_rejected():
    tournament, walk_forward, slippage, parameters = _evidence()
    with pytest.raises(ValueError):
        evaluate_strategy_quality(
            tournament,
            walk_forward_metrics=walk_forward,
            slippage_report=slippage,
            parameter_report=parameters,
            max_drawdown=1.5,
        )
