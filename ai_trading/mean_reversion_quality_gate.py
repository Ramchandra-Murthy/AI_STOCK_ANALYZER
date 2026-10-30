"""Quality-gate adapter for price mean-reversion walk-forward evidence.

This composes the shared strategy quality gate; it does not generate signals
or authorize live trading.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pandas as pd

from ai_trading.strategy_quality_gate import evaluate_strategy_quality

if TYPE_CHECKING:
    from ai_trading.mean_reversion_walk_forward import MeanReversionWalkForwardResult


def evaluate_mean_reversion_quality(
    tournament_row: pd.Series | dict[str, object],
    walk_forward_result: MeanReversionWalkForwardResult,
    *,
    slippage_report: pd.DataFrame | None,
    parameter_report: pd.DataFrame | None,
    min_total_trades: int = 10,
    min_profit_factor: float = 1.0,
    min_positive_fold_fraction: float = 0.5,
    min_sharpe_ratio: float = 0.0,
    max_drawdown: float = 0.25,
) -> dict[str, object]:
    """Evaluate mean-reversion evidence and preserve explicit research-only states.

    Trade count is summed across non-overlapping out-of-sample folds. The
    existing quality gate remains responsible for observations, Sharpe,
    drawdown, fold consistency, slippage and parameter sensitivity.
    """
    if isinstance(min_total_trades, bool) or min_total_trades < 1:
        raise ValueError("min_total_trades must be positive")
    if not math.isfinite(float(min_profit_factor)) or min_profit_factor < 0:
        raise ValueError("min_profit_factor must be finite and nonnegative")

    folds = walk_forward_result.fold_metrics
    missing: list[str] = []
    reasons: list[str] = []

    if folds.empty or "trade_count" not in folds.columns:
        total_trades = None
        missing.append("walk-forward trade_count")
    else:
        trade_counts = pd.to_numeric(folds["trade_count"], errors="coerce")
        if trade_counts.empty or not trade_counts.notna().all():
            total_trades = None
            missing.append("valid walk-forward trade counts")
        else:
            total_trades = int(trade_counts.sum())
            if total_trades < min_total_trades:
                missing.append(
                    f"minimum out-of-sample trades ({total_trades} < {min_total_trades})"
                )

    row = dict(tournament_row)
    profit_factor = row.get("profit_factor")
    if profit_factor is None or pd.isna(profit_factor) or not math.isfinite(float(profit_factor)):
        missing.append("profit factor")
    elif float(profit_factor) < min_profit_factor:
        reasons.append(
            f"profit factor below minimum: {float(profit_factor):.3f} < {min_profit_factor:.3f}"
        )

    result = evaluate_strategy_quality(
        row,
        walk_forward_metrics=folds,
        slippage_report=slippage_report,
        parameter_report=parameter_report,
        min_positive_window_fraction=min_positive_fold_fraction,
        min_sharpe_ratio=min_sharpe_ratio,
        max_drawdown=max_drawdown,
    )
    result["reasons"].extend(reasons)
    result["missing_evidence"].extend(missing)
    result["total_out_of_sample_trades"] = total_trades
    result["positive_fold_fraction"] = walk_forward_result.positive_fold_fraction
    result["live_trading_authorized"] = False

    if result["missing_evidence"]:
        result["status"] = "research_only"
    elif result["reasons"]:
        result["status"] = "failed_validation"
    else:
        result["status"] = "eligible_for_paper_trading"
    result["checks_passed"] = result["status"] == "eligible_for_paper_trading"
    return result
