"""Tests for NR4/NR7 backtest evaluation reports."""

import pytest

from ai_trading.narrow_range_breakout_evaluation import evaluate_narrow_range_backtest


def _trade(
    pnl: float, r: float, pattern: str = "NR4", side: str = "LONG", exit_reason: str = "TARGET"
) -> dict[str, object]:
    return {
        "net_pnl": pnl,
        "r_multiple": r,
        "pattern": pattern,
        "side": side,
        "exit_reason": exit_reason,
    }


def test_empty_report_has_zero_metrics() -> None:
    report = evaluate_narrow_range_backtest({"trades": []})
    assert report["summary"]["trade_count"] == 0
    assert report["summary"]["net_pnl"] == 0.0
    assert report["summary"]["profit_factor"] is None


def test_summary_and_breakdowns_use_net_pnl() -> None:
    result = {
        "trades": [
            _trade(200.0, 2.0, "NR4", "LONG", "TARGET"),
            _trade(-100.0, -1.0, "NR7", "SHORT", "STOP"),
            _trade(50.0, 0.5, "NR4", "LONG", "SESSION_CLOSE"),
        ]
    }
    report = evaluate_narrow_range_backtest(result, initial_capital=1_000.0)
    summary = report["summary"]
    assert summary["trade_count"] == 3
    assert summary["win_rate_pct"] == pytest.approx(200.0 / 3.0)
    assert summary["net_pnl"] == pytest.approx(150.0)
    assert summary["expectancy"] == pytest.approx(50.0)
    assert summary["profit_factor"] == pytest.approx(2.5)
    assert summary["average_r"] == pytest.approx(0.5)
    assert summary["max_drawdown_pct"] == pytest.approx(-100.0 / 12.0)
    assert summary["consecutive_wins"] == 1
    assert summary["consecutive_losses"] == 1
    assert report["breakdowns"]["pattern"]["NR4"]["trade_count"] == 2
    assert report["breakdowns"]["side"]["SHORT"]["net_pnl"] == -100.0


def test_no_losses_has_undefined_profit_factor() -> None:
    report = evaluate_narrow_range_backtest({"trades": [_trade(10.0, 1.0)]})
    assert report["summary"]["profit_factor"] is None


def test_invalid_capital_and_missing_fields_are_rejected() -> None:
    with pytest.raises(ValueError, match="initial_capital"):
        evaluate_narrow_range_backtest({"trades": []}, initial_capital=0)
    with pytest.raises(ValueError, match="missing required fields"):
        evaluate_narrow_range_backtest({"trades": [{"net_pnl": 1.0}]})
