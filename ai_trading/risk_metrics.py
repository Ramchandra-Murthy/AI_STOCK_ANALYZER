"""Book-aligned risk and performance metrics for EROS."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _validate_finite_parameter(value: float, name: str) -> float:
    """Return a finite numeric parameter, rejecting booleans and invalid types."""
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be finite and numeric")
    try:
        numeric_value = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be finite and numeric") from exc
    if not math.isfinite(numeric_value):
        raise ValueError(f"{name} must be finite and numeric")
    return numeric_value


def _clean_returns(returns: pd.Series) -> pd.Series:
    """Coerce returns to numeric, ignore missing values, and validate simple returns."""
    numeric = pd.to_numeric(returns, errors="coerce")
    invalid = returns.notna() & numeric.isna()
    if invalid.any():
        raise ValueError("returns must contain only numeric values or missing values")
    clean = numeric.dropna()
    values = clean.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("returns must contain only finite numeric values")
    if (values < -1.0).any():
        raise ValueError("returns cannot be below -100%")
    return clean


def annualized_volatility(
    returns: pd.Series,
    *,
    periods_per_year: float = 252.0,
) -> float:
    """Return annualized return volatility."""
    periods_per_year = _validate_finite_parameter(periods_per_year, "periods_per_year")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be finite and positive")
    clean = _clean_returns(returns)
    if len(clean) < 2:
        return 0.0
    result = float(clean.std(ddof=1) * math.sqrt(periods_per_year))
    if not math.isfinite(result):
        raise ValueError("annualized volatility overflowed")
    return result


def sharpe_ratio(
    returns: pd.Series,
    *,
    risk_free_rate: float = 0.0,
    periods_per_year: float = 252.0,
) -> float:
    """Return annualized Sharpe ratio using a constant annual risk-free rate."""
    periods_per_year = _validate_finite_parameter(periods_per_year, "periods_per_year")
    risk_free_rate = _validate_finite_parameter(risk_free_rate, "risk_free_rate")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be finite and positive")
    if risk_free_rate <= -1.0:
        raise ValueError("risk_free_rate must be finite and greater than -1")
    clean = _clean_returns(returns)
    if len(clean) < 2:
        return 0.0
    try:
        period_exponent = 1.0 / periods_per_year
        period_rf = (1.0 + risk_free_rate) ** period_exponent - 1.0
    except OverflowError as exc:
        raise ValueError("Sharpe ratio risk-free rate calculation overflowed") from exc
    if not math.isfinite(period_exponent) or not math.isfinite(period_rf):
        raise ValueError("Sharpe ratio risk-free rate calculation produced a non-finite result")
    excess = clean - period_rf
    if not np.isfinite(excess.to_numpy(dtype=float)).all():
        raise ValueError("Sharpe ratio excess returns overflowed")
    volatility = excess.std(ddof=1)
    if not math.isfinite(float(volatility)):
        raise ValueError("Sharpe ratio volatility overflowed")
    if math.isclose(volatility, 0.0, abs_tol=1e-12):
        return 0.0
    result = float(excess.mean() / volatility * math.sqrt(periods_per_year))
    if not math.isfinite(result):
        raise ValueError("Sharpe ratio overflowed")
    return result


def omega_ratio(
    returns: pd.Series,
    *,
    threshold: float = 0.0,
) -> float | None:
    """Return the Omega ratio at a return threshold."""
    threshold = _validate_finite_parameter(threshold, "threshold")
    clean = _clean_returns(returns)
    if clean.empty:
        return None
    excess = clean - threshold
    if not np.isfinite(excess.to_numpy(dtype=float)).all():
        raise ValueError("omega ratio excess returns overflowed")
    gains = float(excess[excess > 0.0].sum())
    losses = float(-excess[excess < 0.0].sum())
    if not math.isfinite(gains) or not math.isfinite(losses):
        raise ValueError("omega ratio gain/loss totals overflowed")
    if math.isclose(losses, 0.0, abs_tol=1e-12):
        return float("inf") if gains > 0.0 else None
    result = gains / losses
    if not math.isfinite(result):
        raise ValueError("omega ratio calculation produced a non-finite result")
    return result


def conditional_value_at_risk(
    returns: pd.Series,
    *,
    confidence: float = 0.95,
) -> float | None:
    """Return historical CVaR as a positive loss magnitude."""
    confidence = _validate_finite_parameter(confidence, "confidence")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be finite and between 0 and 1")
    clean = _clean_returns(returns)
    if clean.empty:
        return None
    var = float(clean.quantile(1.0 - confidence))
    if not math.isfinite(var):
        raise ValueError("CVaR quantile calculation produced a non-finite result")
    tail = clean[clean <= var]
    if tail.empty:
        return max(0.0, -var)
    tail_mean = float(tail.mean())
    if not math.isfinite(tail_mean):
        raise ValueError("CVaR tail mean calculation produced a non-finite result")
    result = max(0.0, -tail_mean)
    if not math.isfinite(result):
        raise ValueError("CVaR calculation produced a non-finite result")
    return result


def max_drawdown(returns: pd.Series) -> float:
    """Return maximum drawdown as a positive loss fraction."""
    clean = _clean_returns(returns)
    if clean.empty:
        return 0.0
    equity = np.concatenate(([1.0], (1.0 + clean).cumprod().to_numpy(dtype=float)))
    if not np.isfinite(equity).all():
        raise ValueError("equity curve overflowed while calculating max drawdown")
    peak = np.maximum.accumulate(equity)
    drawdown = 1.0 - equity / peak
    return float(drawdown.max())


def risk_performance_summary(
    returns: pd.Series,
    *,
    risk_free_rate: float = 0.0,
    periods_per_year: float = 252.0,
    cvar_confidence: float = 0.95,
) -> dict[str, float | None]:
    """Return a composite risk/performance view for a return series."""
    return {
        "annualized_volatility": annualized_volatility(returns, periods_per_year=periods_per_year),
        "sharpe_ratio": sharpe_ratio(
            returns,
            risk_free_rate=risk_free_rate,
            periods_per_year=periods_per_year,
        ),
        "omega_ratio": omega_ratio(returns),
        "conditional_value_at_risk": conditional_value_at_risk(returns, confidence=cvar_confidence),
        "max_drawdown": max_drawdown(returns),
    }
