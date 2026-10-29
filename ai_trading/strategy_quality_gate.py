"""Evidence-based quality gate for research strategies.

Combines existing diagnostics; does not generate signals or place orders.
Passing means eligible for paper-trading evaluation only.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd


def evaluate_strategy_quality(
    tournament_row: pd.Series | dict[str, object],
    *,
    walk_forward_metrics: pd.DataFrame | None,
    slippage_report: pd.DataFrame | None,
    parameter_report: pd.DataFrame | None = None,
    min_observations: int = 30,
    min_walk_forward_windows: int = 3,
    min_positive_window_fraction: float = 0.5,
    min_sharpe_ratio: float = 0.0,
    max_drawdown: float = 0.25,
    require_nonnegative_worst_slippage_return: bool = True,
) -> dict[str, object]:
    """Evaluate evidence and return a status with transparent reasons."""
    if isinstance(min_observations, bool) or min_observations < 1:
        raise ValueError("min_observations must be positive")
    if isinstance(min_walk_forward_windows, bool) or min_walk_forward_windows < 1:
        raise ValueError("min_walk_forward_windows must be positive")
    if not math.isfinite(float(min_positive_window_fraction)) or not 0 <= min_positive_window_fraction <= 1:
        raise ValueError("min_positive_window_fraction must be between 0 and 1")
    if not math.isfinite(float(min_sharpe_ratio)):
        raise ValueError("min_sharpe_ratio must be finite")
    if not math.isfinite(float(max_drawdown)) or not 0 <= max_drawdown <= 1:
        raise ValueError("max_drawdown must be between 0 and 1")

    reasons: list[str] = []
    missing: list[str] = []
    row = dict(tournament_row)
    observations = row.get("observations")
    sharpe = row.get("sharpe_ratio")
    drawdown = row.get("max_drawdown")

    if observations is None or pd.isna(observations):
        missing.append("tournament observation count")
    elif observations < min_observations:
        reasons.append(f"insufficient observations: {int(observations)} < {min_observations}")

    for label, value in (("Sharpe ratio", sharpe), ("maximum drawdown", drawdown)):
        if value is None or pd.isna(value) or not np.isfinite(float(value)):
            missing.append(label)
    if sharpe is not None and pd.notna(sharpe) and np.isfinite(float(sharpe)):
        if float(sharpe) < min_sharpe_ratio:
            reasons.append(f"Sharpe ratio below minimum: {float(sharpe):.3f}")
    if drawdown is not None and pd.notna(drawdown) and np.isfinite(float(drawdown)):
        if float(drawdown) > max_drawdown:
            reasons.append(f"maximum drawdown exceeds limit: {float(drawdown):.3f}")

    if walk_forward_metrics is None or walk_forward_metrics.empty:
        missing.append("walk-forward window metrics")
    elif "total_return" not in walk_forward_metrics.columns:
        missing.append("walk-forward total_return")
    else:
        window_returns = pd.to_numeric(walk_forward_metrics["total_return"], errors="coerce")
        window_returns = window_returns[np.isfinite(window_returns.to_numpy(dtype=float))]
        if len(window_returns) < min_walk_forward_windows:
            reasons.append(
                f"too few valid walk-forward windows: {len(window_returns)} < {min_walk_forward_windows}"
            )
        elif float((window_returns > 0).mean()) < min_positive_window_fraction:
            reasons.append("positive walk-forward window fraction below minimum")

    if slippage_report is None or slippage_report.empty:
        missing.append("slippage sensitivity report")
    elif "net_return" not in slippage_report.columns:
        missing.append("slippage net_return")
    else:
        net_returns = pd.to_numeric(slippage_report["net_return"], errors="coerce")
        net_returns = net_returns[np.isfinite(net_returns.to_numpy(dtype=float))]
        if net_returns.empty:
            missing.append("valid slippage net returns")
        elif require_nonnegative_worst_slippage_return and float(net_returns.min()) < 0:
            reasons.append("net return is negative under a tested slippage scenario")

    if parameter_report is None or parameter_report.empty:
        missing.append("parameter sensitivity report")
    elif not {"total_return", "sharpe_ratio"}.issubset(parameter_report.columns):
        missing.append("parameter return and Sharpe metrics")
    else:
        values = parameter_report[["total_return", "sharpe_ratio"]].apply(pd.to_numeric, errors="coerce")
        if not np.isfinite(values.to_numpy(dtype=float)).all():
            missing.append("valid parameter sensitivity values")
        elif len(values) < 2:
            missing.append("at least two parameter configurations")

    if missing:
        status = "research_only"
    elif reasons:
        status = "failed_validation"
    else:
        status = "eligible_for_paper_trading"

    return {
        "status": status,
        "reasons": reasons,
        "missing_evidence": missing,
        "checks_passed": not reasons and not missing,
        "live_trading_authorized": False,
    }
