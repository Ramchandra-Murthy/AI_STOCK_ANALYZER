"""Parameter robustness evaluation for RSI-confirmed price mean-reversion research."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from ai_trading.mean_reversion_backtest import run_price_mean_reversion_backtest
from ai_trading.parameter_robustness import parameter_robustness_summary
from ai_trading.parameter_sensitivity import parameter_sensitivity_report
from algorithmic_trading.trading_costs import IndiaEquityCostModel


@dataclass(frozen=True)
class MeanReversionRobustnessResult:
    """Per-configuration metrics and aggregate robustness diagnostics."""

    parameter_report: pd.DataFrame
    robustness: dict[str, float | int | None]


def evaluate_mean_reversion_parameter_robustness(
    close: pd.Series,
    configurations: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    *,
    initial_capital: float = 100_000.0,
    cost_bps: float = 10.0,
    cost_model: IndiaEquityCostModel | None = None,
    periods_per_year: float = 252.0,
    near_best_tolerance: float = 0.10,
) -> MeanReversionRobustnessResult:
    """Backtest explicit parameter configurations and summarize net-return stability.

    Configuration dictionaries accept the same signal parameters as
    `run_price_mean_reversion_backtest`: lookback, rsi_period, entry_z,
    exit_z, oversold_rsi, overbought_rsi and allow_short. No optimization or
    parameter selection is performed; all configurations are evaluated on
    the supplied historical series with identical capital and cost settings.
    """
    if not isinstance(close, pd.Series) or close.empty:
        raise ValueError("close must be a non-empty pandas Series")
    if not configurations:
        raise ValueError("configurations must not be empty")

    allowed = {
        "lookback",
        "rsi_period",
        "entry_z",
        "exit_z",
        "oversold_rsi",
        "overbought_rsi",
        "allow_short",
    }
    returns_by_parameter: dict[str, pd.Series] = {}
    metadata: list[dict[str, Any]] = []
    seen: set[str] = set()

    for index, configuration in enumerate(configurations):
        if not isinstance(configuration, dict):
            raise ValueError("each configuration must be a dictionary")
        unknown = sorted(set(configuration).difference(allowed))
        if unknown:
            raise ValueError(f"unsupported configuration parameters: {unknown}")
        label = ", ".join(f"{key}={configuration[key]}" for key in sorted(configuration))
        label = label or f"configuration_{index + 1}"
        if label in seen:
            raise ValueError(f"duplicate configuration: {label}")
        seen.add(label)

        backtest = run_price_mean_reversion_backtest(
            close,
            initial_capital=initial_capital,
            cost_bps=cost_bps,
            cost_model=cost_model,
            **configuration,
        )
        returns_by_parameter[label] = backtest.equity_curve["strategy_return"]
        metadata.append({"parameter": label, **configuration})

    report = parameter_sensitivity_report(
        returns_by_parameter,
        periods_per_year=periods_per_year,
    )
    report = report.merge(pd.DataFrame(metadata), on="parameter", how="left", validate="one_to_one")
    robustness = parameter_robustness_summary(
        report,
        metric_column="sharpe_ratio",
        parameter_columns=("parameter",),
        near_best_tolerance=near_best_tolerance,
    )
    return MeanReversionRobustnessResult(parameter_report=report, robustness=robustness)
