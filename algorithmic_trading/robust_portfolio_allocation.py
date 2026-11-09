"""Robust, turnover-aware portfolio allocation for research workflows.

Uses diagonal covariance shrinkage and a long-only capped-simplex optimizer.
The method is a transparent research baseline, not a return forecast or
guarantee of optimal live execution.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _finite_parameter(value: float, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be finite and numeric")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be finite and numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite and numeric")
    return result


def _validate_returns(returns: pd.DataFrame) -> pd.DataFrame:
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
    if (values < -1.0).any():
        raise ValueError("simple returns cannot be below -100%")
    if len(numeric) < 2:
        raise ValueError("at least two observations are required")
    return numeric


def shrinkage_covariance(
    returns: pd.DataFrame,
    *,
    shrinkage: float = 0.25,
    ridge: float = 1e-8,
) -> pd.DataFrame:
    """Shrink sample covariance toward its diagonal and add ridge regularization.

    The diagonal target reduces noisy off-diagonal correlation estimates.
    The ridge term makes the matrix numerically better conditioned, including
    when assets are collinear or have zero sample variance.
    """
    shrinkage = _finite_parameter(shrinkage, "shrinkage")
    ridge = _finite_parameter(ridge, "ridge")
    if not 0.0 <= shrinkage <= 1.0:
        raise ValueError("shrinkage must be between 0 and 1")
    if ridge <= 0.0:
        raise ValueError("ridge must be greater than zero")

    numeric = _validate_returns(returns)
    sample = numeric.cov().to_numpy(dtype=float)
    if not np.isfinite(sample).all():
        raise ValueError("sample covariance must be finite")
    diagonal = np.diag(np.diag(sample))
    covariance = (1.0 - shrinkage) * sample + shrinkage * diagonal
    covariance += np.eye(covariance.shape[0]) * ridge
    covariance = (covariance + covariance.T) / 2.0
    if not np.isfinite(covariance).all():
        raise ValueError("regularized covariance must be finite")
    return pd.DataFrame(covariance, index=numeric.columns, columns=numeric.columns)


def _project_capped_simplex(values: np.ndarray, cap: float) -> np.ndarray:
    """Euclidean projection onto {w: sum(w)=1, 0<=w<=cap}."""
    count = len(values)
    if cap * count < 1.0 - 1e-12:
        raise ValueError("max_weight is too small to fully allocate across assets")
    lower = float(np.min(values - cap))
    upper = float(np.max(values))
    for _ in range(100):
        midpoint = (lower + upper) / 2.0
        projected = np.clip(values - midpoint, 0.0, cap)
        if float(projected.sum()) > 1.0:
            lower = midpoint
        else:
            upper = midpoint
    result = np.clip(values - (lower + upper) / 2.0, 0.0, cap)
    residual = 1.0 - float(result.sum())
    if abs(residual) > 1e-10:
        eligible = np.flatnonzero(
            (result < cap - 1e-12) if residual > 0 else (result > 1e-12)
        )
        for index in eligible:
            adjustment = min(cap - result[index], residual) if residual > 0 else max(
                -result[index], residual
            )
            result[index] += adjustment
            residual -= adjustment
            if abs(residual) <= 1e-12:
                break
    if abs(float(result.sum()) - 1.0) > 1e-8:
        raise RuntimeError("capped-simplex projection did not converge")
    return result


def cost_aware_minimum_variance_weights(
    returns: pd.DataFrame,
    *,
    previous_weights: pd.Series | None = None,
    shrinkage: float = 0.25,
    ridge: float = 1e-8,
    max_weight: float = 0.35,
    turnover_penalty: float = 0.0,
    max_iter: int = 10_000,
    tolerance: float = 1e-10,
) -> pd.Series:
    """Optimize long-only minimum variance with a quadratic turnover penalty.

    The objective is w'Σw + λ||w-w_previous||² subject to sum(w)=1 and
    0<=w_i<=max_weight. With no previous weights, the turnover term is absent.
    A projected-gradient solver avoids adding an optional optimization
    dependency and fails explicitly if it does not converge.
    """
    numeric = _validate_returns(returns)
    cap = _finite_parameter(max_weight, "max_weight")
    penalty = _finite_parameter(turnover_penalty, "turnover_penalty")
    tol = _finite_parameter(tolerance, "tolerance")
    if not 0.0 < cap <= 1.0:
        raise ValueError("max_weight must be in (0, 1]")
    if cap * numeric.shape[1] < 1.0 - 1e-12:
        raise ValueError("max_weight is too small to fully allocate across assets")
    if penalty < 0.0:
        raise ValueError("turnover_penalty must be non-negative")
    if tol <= 0.0:
        raise ValueError("tolerance must be greater than zero")
    if isinstance(max_iter, bool) or not isinstance(max_iter, int) or max_iter < 1:
        raise ValueError("max_iter must be a positive integer")

    covariance = shrinkage_covariance(
        numeric,
        shrinkage=shrinkage,
        ridge=ridge,
    ).to_numpy(dtype=float)
    previous: np.ndarray | None = None
    if previous_weights is not None:
        if not isinstance(previous_weights, pd.Series):
            raise ValueError("previous_weights must be a pandas Series")
        if not previous_weights.index.is_unique:
            raise ValueError("previous weight symbols must be unique")
        unknown = previous_weights.index.difference(numeric.columns)
        if len(unknown):
            raise ValueError(f"previous_weights contains unknown assets: {list(unknown)}")
        previous_series = pd.to_numeric(previous_weights.reindex(numeric.columns), errors="coerce")
        previous = previous_series.to_numpy(dtype=float)
        if not np.isfinite(previous).all() or (previous < 0.0).any():
            raise ValueError("previous weights must be finite and non-negative")
        if not math.isclose(float(previous.sum()), 1.0, rel_tol=0.0, abs_tol=1e-8):
            raise ValueError("previous weights must sum to 1")

    hessian = covariance + (penalty * np.eye(len(covariance)) if previous is not None else 0.0)
    largest_eigenvalue = float(np.linalg.eigvalsh(hessian).max())
    if not math.isfinite(largest_eigenvalue) or largest_eigenvalue <= 0.0:
        raise ValueError("allocation objective must have positive finite curvature")
    step_size = 1.0 / (2.0 * largest_eigenvalue)
    weights = (
        _project_capped_simplex(previous.copy(), cap)
        if previous is not None
        else np.full(numeric.shape[1], 1.0 / numeric.shape[1])
    )

    converged = False
    for _ in range(max_iter):
        gradient = 2.0 * (covariance @ weights)
        if previous is not None:
            gradient += 2.0 * penalty * (weights - previous)
        updated = _project_capped_simplex(weights - step_size * gradient, cap)
        if float(np.max(np.abs(updated - weights))) <= tol:
            weights = updated
            converged = True
            break
        weights = updated
    if not converged:
        raise RuntimeError("portfolio allocation optimizer did not converge")

    return pd.Series(weights, index=numeric.columns, name="target_weight")


def estimate_rebalance_cost(
    target_weights: pd.Series,
    current_weights: pd.Series,
    *,
    cost_bps: float,
) -> dict[str, float]:
    """Estimate linear trading cost as a fraction of NAV and in basis points.

    Turnover is the sum of absolute weight changes. Cost bps applies to each
    unit of traded notional, so buys and sells are both included.
    """
    cost_bps = _finite_parameter(cost_bps, "cost_bps")
    if cost_bps < 0.0:
        raise ValueError("cost_bps must be non-negative")
    if not target_weights.index.is_unique or not current_weights.index.is_unique:
        raise ValueError("weight symbols must be unique")
    symbols = target_weights.index.union(current_weights.index)
    target = pd.to_numeric(target_weights.reindex(symbols).fillna(0.0), errors="coerce")
    current = pd.to_numeric(current_weights.reindex(symbols).fillna(0.0), errors="coerce")
    values = np.concatenate([target.to_numpy(dtype=float), current.to_numpy(dtype=float)])
    if not np.isfinite(values).all() or (values < 0.0).any():
        raise ValueError("weights must be finite and non-negative")
    turnover = float((target - current).abs().sum())
    return {
        "gross_turnover": turnover,
        "estimated_cost_fraction": turnover * cost_bps / 10_000.0,
        "estimated_cost_bps_of_nav": turnover * cost_bps,
    }
