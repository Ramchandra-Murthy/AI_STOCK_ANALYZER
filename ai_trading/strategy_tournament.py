"""Compare strategy return streams on a consistent basis.

This module ranks supplied out-of-sample return series. It does not generate
signals or claim that historical performance predicts future results.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

from ai_trading.risk_metrics import risk_performance_summary


def compare_strategies(
    strategy_returns: Mapping[str, pd.Series],
    *,
    periods_per_year: float = 252.0,
    risk_free_rate: float = 0.0,
    min_observations: int = 30,
) -> pd.DataFrame:
    """Return comparable performance metrics, ranked by Sharpe ratio.

    Each input must contain simple periodic returns (for example, daily
    net returns after transaction costs). Missing observations are excluded
    independently per strategy. Strategies below min_observations remain
    visible but are marked ineligible and are not assigned a rank.

    Use out-of-sample returns for decision-making; this function does not
    split data or prevent users from supplying in-sample returns.
    """
    if not math.isfinite(float(periods_per_year)) or periods_per_year <= 0:
        raise ValueError("periods_per_year must be finite and positive")
    if not math.isfinite(float(risk_free_rate)) or risk_free_rate <= -1.0:
        raise ValueError("risk_free_rate must be finite and greater than -1")
    if isinstance(min_observations, bool) or min_observations < 1:
        raise ValueError("min_observations must be a positive integer")
    if not strategy_returns:
        return pd.DataFrame(
            columns=[
                "strategy",
                "observations",
                "total_return",
                "annualized_volatility",
                "sharpe_ratio",
                "max_drawdown",
                "cvar_95",
                "win_rate",
                "profit_factor",
                "eligible",
                "rank",
            ]
        )

    rows: list[dict[str, object]] = []
    for name, returns in strategy_returns.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("strategy names must be non-empty strings")
        if not isinstance(returns, pd.Series):
            raise TypeError(f"returns for {name!r} must be a pandas Series")

        numeric = pd.to_numeric(returns, errors="coerce")
        invalid = returns.notna() & numeric.isna()
        if invalid.any():
            raise ValueError(f"returns for {name!r} must be numeric")
        clean = numeric.dropna().astype(float)
        values = clean.to_numpy(dtype=float)
        if not np.isfinite(values).all() or (values < -1.0).any():
            raise ValueError(f"returns for {name!r} must be finite and at least -100%")

        summary = risk_performance_summary(
            clean,
            risk_free_rate=risk_free_rate,
            periods_per_year=periods_per_year,
        )
        total_return = float((1.0 + clean).prod() - 1.0) if len(clean) else 0.0
        gains = float(clean[clean > 0].sum())
        losses = float(-clean[clean < 0].sum())
        profit_factor = (
            gains / losses if losses > 0 else (float("inf") if gains > 0 else None)
        )
        rows.append(
            {
                "strategy": name,
                "observations": len(clean),
                "total_return": total_return,
                "annualized_volatility": summary["annualized_volatility"],
                "sharpe_ratio": summary["sharpe_ratio"],
                "max_drawdown": summary["max_drawdown"],
                "cvar_95": summary["conditional_value_at_risk"],
                "win_rate": float((clean > 0).mean()) if len(clean) else 0.0,
                "profit_factor": profit_factor,
                "eligible": len(clean) >= min_observations,
                "rank": None,
            }
        )

    result = pd.DataFrame(rows)
    eligible = result["eligible"] & result["sharpe_ratio"].notna()
    result.loc[eligible, "rank"] = (
        result.loc[eligible, "sharpe_ratio"]
        .rank(method="min", ascending=False)
        .astype(int)
    )
    return result.sort_values(
        ["eligible", "rank", "strategy"],
        ascending=[False, True, True],
        na_position="last",
    ).reset_index(drop=True)
