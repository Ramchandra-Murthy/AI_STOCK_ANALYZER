"""Walk-forward evaluation for robust portfolio allocation research.

The evaluator compares equal-weight, sample-covariance minimum-variance, and
shrinkage/turnover-aware portfolios on identical chronological test returns.
It is research-only and never places orders.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from algorithmic_trading.robust_portfolio_allocation import (
    cost_aware_minimum_variance_weights,
)


def _validate_inputs(
    returns: pd.DataFrame,
    lookback: int,
    rebalance_every: int,
    cost_bps: float,
    max_weight: float,
) -> tuple[pd.DataFrame, int, int, float, float]:
    if not isinstance(returns, pd.DataFrame):
        raise ValueError("returns must be a pandas DataFrame")
    if returns.empty or returns.shape[1] == 0:
        raise ValueError("returns must contain observations and assets")
    if not returns.columns.is_unique:
        raise ValueError("asset columns must be unique")
    if not returns.index.is_unique or not returns.index.is_monotonic_increasing:
        raise ValueError("returns must have a unique, chronological index")
    numeric = returns.apply(pd.to_numeric, errors="coerce")
    values = numeric.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("returns must be complete and finite")
    if (values <= -1.0).any():
        raise ValueError("returns must be greater than -100%")
    if isinstance(lookback, bool) or not isinstance(lookback, int) or lookback < 2:
        raise ValueError("lookback must be an integer of at least 2")
    if (
        isinstance(rebalance_every, bool)
        or not isinstance(rebalance_every, int)
        or rebalance_every < 1
    ):
        raise ValueError("rebalance_every must be a positive integer")
    try:
        costs = float(cost_bps)
        cap = float(max_weight)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("cost_bps and max_weight must be finite numbers") from exc
    if isinstance(cost_bps, bool) or not math.isfinite(costs) or costs < 0:
        raise ValueError("cost_bps must be finite and non-negative")
    if isinstance(max_weight, bool) or not math.isfinite(cap) or not 0 < cap <= 1:
        raise ValueError("max_weight must be finite and in (0, 1]")
    if cap * numeric.shape[1] < 1.0 - 1e-12:
        raise ValueError("max_weight is too small for the number of assets")
    if costs >= 10_000.0:
        raise ValueError("cost_bps must be below 10000")
    if len(numeric) <= lookback:
        raise ValueError("returns must contain observations beyond the lookback")
    return numeric, lookback, rebalance_every, costs, cap


def _max_drawdown(returns: pd.Series) -> float:
    wealth = (1.0 + returns).cumprod()
    return float((wealth / wealth.cummax() - 1.0).min())


def _performance_metrics(returns: pd.Series) -> dict[str, float | int]:
    if returns.empty:
        return {
            "observations": 0,
            "total_return": float("nan"),
            "annualized_return": float("nan"),
            "annualized_volatility": float("nan"),
            "sharpe_ratio": float("nan"),
            "max_drawdown": float("nan"),
        }
    wealth = float((1.0 + returns).prod())
    volatility = float(returns.std(ddof=1) * math.sqrt(252.0)) if len(returns) > 1 else float("nan")
    annualized_return = wealth ** (252.0 / len(returns)) - 1.0 if wealth > 0 else -1.0
    sharpe = (
        float(returns.mean() / returns.std(ddof=1) * math.sqrt(252.0))
        if len(returns) > 1 and returns.std(ddof=1) > 0
        else float("nan")
    )
    return {
        "observations": len(returns),
        "total_return": wealth - 1.0,
        "annualized_return": annualized_return,
        "annualized_volatility": volatility,
        "sharpe_ratio": sharpe,
        "max_drawdown": _max_drawdown(returns),
    }


def walk_forward_portfolio_evaluate(
    returns: pd.DataFrame,
    *,
    lookback: int = 252,
    rebalance_every: int = 21,
    cost_bps: float = 10.0,
    max_weight: float = 0.35,
    shrinkage: float = 0.25,
    turnover_penalty: float = 0.0001,
) -> pd.DataFrame:
    """Compare portfolio strategies using rolling, strictly prior return windows.

    Each strategy is rebalanced at the same timestamps and incurs the same
    linear cost in basis points of traded notional. Holdings drift with
    realized returns between rebalances. The first rebalance starts from cash,
    so initial purchases incur the same modeled cost for every strategy.

    Returns one row per strategy with out-of-sample performance, total turnover,
    estimated transaction costs, and the first/last test timestamps.
    Daily simple returns and 252-session annualization are assumed.
    """
    numeric, lookback, rebalance_every, costs, cap = _validate_inputs(
        returns, lookback, rebalance_every, cost_bps, max_weight
    )
    names = (
        "equal_weight",
        "sample_minimum_variance",
        "shrinkage_turnover_aware",
    )
    asset_count = numeric.shape[1]
    states: dict[str, dict[str, object]] = {
        name: {
            "weights": np.zeros(asset_count, dtype=float),
            "returns": [],
            "turnover": 0.0,
            "cost_fraction": 0.0,
        }
        for name in names
    }
    for start in range(lookback, len(numeric), rebalance_every):
        stop = min(start + rebalance_every, len(numeric))
        training = numeric.iloc[start - lookback : start]
        targets: dict[str, np.ndarray] = {
            "equal_weight": np.full(asset_count, 1.0 / asset_count),
        }
        sample_weights = cost_aware_minimum_variance_weights(
            training,
            shrinkage=0.0,
            max_weight=cap,
            turnover_penalty=0.0,
        )
        targets["sample_minimum_variance"] = sample_weights.to_numpy(dtype=float)
        robust_state = states["shrinkage_turnover_aware"]
        old_robust = np.asarray(robust_state["weights"], dtype=float)
        robust_previous = (
            pd.Series(old_robust, index=numeric.columns)
            if np.isclose(old_robust.sum(), 1.0)
            else None
        )
        robust_weights = cost_aware_minimum_variance_weights(
            training,
            previous_weights=robust_previous,
            shrinkage=shrinkage,
            max_weight=cap,
            turnover_penalty=turnover_penalty,
        )
        targets["shrinkage_turnover_aware"] = robust_weights.to_numpy(dtype=float)

        for name in names:
            state = states[name]
            old_weights = np.asarray(state["weights"], dtype=float)
            target = targets[name]
            turnover = (
                float(np.abs(target).sum())
                if not np.isclose(old_weights.sum(), 1.0)
                else float(np.abs(target - old_weights).sum())
            )
            cost_fraction = turnover * costs / 10_000.0
            state["turnover"] = float(state["turnover"]) + turnover
            state["cost_fraction"] = float(state["cost_fraction"]) + cost_fraction
            state["weights"] = target.copy()

            for offset, row in enumerate(
                numeric.iloc[start:stop].itertuples(index=False, name=None)
            ):
                daily_returns = np.asarray(row, dtype=float)
                portfolio_return = float(np.dot(state["weights"], daily_returns))
                net_return = (
                    (1.0 - cost_fraction) * (1.0 + portfolio_return) - 1.0
                    if offset == 0
                    else portfolio_return
                )
                state["returns"].append(net_return)
                denominator = 1.0 + portfolio_return
                state["weights"] = state["weights"] * (1.0 + daily_returns) / denominator

    test_index = numeric.index[lookback:]
    output: list[dict[str, object]] = []
    for name in names:
        state = states[name]
        strategy_returns = pd.Series(state["returns"], index=test_index, dtype=float, name=name)
        row: dict[str, object] = {
            "strategy": name,
            **_performance_metrics(strategy_returns),
            "gross_turnover": float(state["turnover"]),
            "estimated_cost_fraction": float(state["cost_fraction"]),
            "test_start": str(test_index[0]),
            "test_end": str(test_index[-1]),
            "lookback": lookback,
            "rebalance_every": rebalance_every,
            "cost_bps": costs,
        }
        output.append(row)
    return pd.DataFrame(output)
