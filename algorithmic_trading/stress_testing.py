"""Deterministic portfolio scenario stress tests for research workflows.

Scenarios are explicit one-period asset returns supplied by the caller. They
are not forecasts, VaR estimates, or substitutes for chronological backtests.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd


def run_portfolio_stress_scenarios(
    weights: pd.Series,
    scenarios: Mapping[str, Mapping[str, float]],
    *,
    portfolio_value: float = 1.0,
) -> pd.DataFrame:
    """Apply caller-defined asset-return shocks to a long-only portfolio.

    Missing asset shocks are treated as zero. Unknown symbols, duplicate
    holdings, invalid weights, and returns below -100% are rejected.
    """
    if not isinstance(weights, pd.Series) or weights.empty:
        raise ValueError("weights must be a non-empty pandas Series")
    if not weights.index.is_unique:
        raise ValueError("weight symbols must be unique")
    if not isinstance(scenarios, Mapping) or not scenarios:
        raise ValueError("scenarios must be a non-empty mapping")
    if isinstance(portfolio_value, (bool, np.bool_)):
        raise ValueError("portfolio_value must be finite and greater than zero")
    try:
        nav = float(portfolio_value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("portfolio_value must be finite and greater than zero") from exc
    if not math.isfinite(nav) or nav <= 0:
        raise ValueError("portfolio_value must be finite and greater than zero")

    numeric_weights = pd.to_numeric(weights, errors="coerce")
    weight_values = numeric_weights.to_numpy(dtype=float)
    if not np.isfinite(weight_values).all() or (weight_values < 0).any():
        raise ValueError("weights must be finite and non-negative")
    if not math.isclose(float(numeric_weights.sum()), 1.0, rel_tol=0.0, abs_tol=1e-8):
        raise ValueError("weights must sum to 1")

    rows: list[dict[str, float | str]] = []
    for name, asset_shocks in scenarios.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("scenario names must be non-empty strings")
        if not isinstance(asset_shocks, Mapping):
            raise ValueError(f"scenario '{name}' must map symbols to returns")
        unknown = set(asset_shocks).difference(numeric_weights.index)
        if unknown:
            raise ValueError(f"scenario '{name}' contains unknown assets: {sorted(unknown)}")
        shocks = pd.Series(0.0, index=numeric_weights.index, dtype=float)
        for symbol, value in asset_shocks.items():
            if isinstance(value, (bool, np.bool_)):
                raise ValueError(f"scenario '{name}' returns must be finite and >= -100%")
            try:
                shock = float(value)
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError(
                    f"scenario '{name}' returns must be finite and >= -100%"
                ) from exc
            if not math.isfinite(shock) or shock < -1.0:
                raise ValueError(f"scenario '{name}' returns must be finite and >= -100%")
            shocks.loc[symbol] = shock

        contributions = numeric_weights * shocks
        portfolio_return = float(contributions.sum())
        worst_symbol = str(contributions.idxmin())
        rows.append(
            {
                "scenario": name,
                "portfolio_return": portfolio_return,
                "pnl": nav * portfolio_return,
                "portfolio_value_after": nav * (1.0 + portfolio_return),
                "worst_contributor": worst_symbol,
                "worst_contribution": float(contributions.loc[worst_symbol]),
            }
        )

    return pd.DataFrame(rows).set_index("scenario")
