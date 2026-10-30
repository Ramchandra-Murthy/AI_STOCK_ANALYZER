import numpy as np
import pandas as pd
import pytest

from ai_trading.mean_reversion_parameter_robustness import (
    evaluate_mean_reversion_parameter_robustness,
)


def _prices(periods: int = 120) -> pd.Series:
    index = pd.date_range("2026-01-01", periods=periods, freq="D")
    trend = np.linspace(100.0, 112.0, periods)
    cycle = np.sin(np.arange(periods) / 3.0) * 3.0
    return pd.Series(trend + cycle, index=index)


def test_parameter_robustness_reports_each_configuration_and_summary():
    result = evaluate_mean_reversion_parameter_robustness(
        _prices(),
        [
            {"lookback": 10, "rsi_period": 3, "entry_z": 0.8, "oversold_rsi": 50.0},
            {"lookback": 15, "rsi_period": 5, "entry_z": 1.0, "oversold_rsi": 45.0},
            {"lookback": 20, "rsi_period": 7, "entry_z": 1.2, "oversold_rsi": 40.0},
        ],
    )

    assert len(result.parameter_report) == 3
    assert {"parameter", "total_return", "sharpe_ratio", "max_drawdown"}.issubset(
        result.parameter_report.columns
    )
    assert result.robustness["configurations"] == 3
    assert 0.0 <= result.robustness["near_best_fraction"] <= 1.0


def test_parameter_robustness_uses_common_cost_assumptions():
    free = evaluate_mean_reversion_parameter_robustness(
        _prices(),
        [{"lookback": 10, "rsi_period": 3, "entry_z": 0.8, "oversold_rsi": 50.0}],
        cost_bps=0.0,
    )
    charged = evaluate_mean_reversion_parameter_robustness(
        _prices(),
        [{"lookback": 10, "rsi_period": 3, "entry_z": 0.8, "oversold_rsi": 50.0}],
        cost_bps=25.0,
    )

    assert charged.parameter_report.loc[0, "total_return"] <= (
        free.parameter_report.loc[0, "total_return"] + 1e-12
    )


def test_parameter_robustness_rejects_empty_configurations():
    with pytest.raises(ValueError, match="configurations must not be empty"):
        evaluate_mean_reversion_parameter_robustness(_prices(), [])


def test_parameter_robustness_rejects_unknown_parameters():
    with pytest.raises(ValueError, match="unsupported configuration parameters"):
        evaluate_mean_reversion_parameter_robustness(_prices(), [{"window": 10}])


def test_parameter_robustness_rejects_duplicate_configurations():
    configuration = {"lookback": 10, "rsi_period": 3}
    with pytest.raises(ValueError, match="duplicate configuration"):
        evaluate_mean_reversion_parameter_robustness(
            _prices(), [configuration, configuration]
        )


def test_parameter_robustness_rejects_invalid_price_input():
    with pytest.raises(ValueError, match="non-empty pandas Series"):
        evaluate_mean_reversion_parameter_robustness(pd.DataFrame(), [{"lookback": 10}])
