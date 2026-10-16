"""Compare backtest outcomes across explicitly supplied parameter variants.

This research helper does not fetch data, optimize parameters, or execute trades.
Callers supply each named BacktestConfig so the tested assumptions remain auditable.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite

from modules.fibonacci_gann.backtest import BacktestConfig, BacktestResult, Candle, run_backtest


@dataclass(frozen=True)
class ParameterSensitivityResult:
    """Backtest outcome for one named parameter configuration."""

    variant: str
    config: BacktestConfig
    result: BacktestResult


def evaluate_parameter_sensitivity(
    candles: Sequence[Candle],
    signals: Sequence[bool],
    variants: Mapping[str, BacktestConfig],
) -> tuple[ParameterSensitivityResult, ...]:
    """Run the same candles/signals independently under named configurations.

    Variants are evaluated in mapping order. Each run starts with the capital
    specified by its own config; returns are not compounded across variants.
    """
    if len(candles) != len(signals):
        raise ValueError("signals length must equal candles length")
    if not variants:
        raise ValueError("at least one parameter variant is required")
    if any(not isinstance(signal, bool) for signal in signals):
        raise ValueError("signals must contain only booleans")

    results: list[ParameterSensitivityResult] = []
    for name, config in variants.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("variant names must be non-empty strings")
        if not isinstance(config, BacktestConfig):
            raise ValueError(f"variant {name!r} must use a BacktestConfig")
        result = run_backtest(candles, signals, config)
        metrics = (
            result.total_return_pct,
            result.win_rate_pct,
            result.expectancy_per_trade,
            result.profit_factor,
            result.max_drawdown_pct,
        )
        if not all(isfinite(value) for value in metrics):
            raise ValueError(f"variant {name!r} produced non-finite performance metrics")
        results.append(ParameterSensitivityResult(name, config, result))
    return tuple(results)
