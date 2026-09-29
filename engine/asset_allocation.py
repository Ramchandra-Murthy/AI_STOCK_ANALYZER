"""Chapter 9 asset allocation and Dynamic Exposure Allocation (DEA).

Implements the failure-mode-driven allocation framework described in Chapter 9:
strategy failure geometry, portfolio elasticity, the risk appetite oscillator,
temporary boosts, exposure clipping, and recursive exposure allocation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def upper_band_limit(
    st_dd: float,
    lt_dd: float,
    corr_adj: float,
    lt_dd_tolerance: float,
    st_dd_tolerance: float,
    lqdty_haircut: float,
) -> float:
    """Calculate a strategy's hard upper allocation band."""
    _validate_positive("st_dd", st_dd)
    _validate_positive("lt_dd", lt_dd)
    _validate_fraction("corr_adj", corr_adj)
    _validate_fraction("lqdty_haircut", lqdty_haircut)
    _validate_positive("st_dd_tolerance", st_dd_tolerance)
    _validate_positive("lt_dd_tolerance", lt_dd_tolerance)

    min_dd = min(st_dd_tolerance / st_dd, lt_dd_tolerance / lt_dd)
    upper_band = round(
        min(min_dd * (1 - corr_adj), 1) * (1 - lqdty_haircut),
        2,
    )
    return upper_band


def risk_appetite(
    equity_curve: pd.Series | np.ndarray | list[float],
    max_drawdown_tolerance: float,
    min_risk: float,
    max_risk: float,
    smoothing_span: int = 20,
    curve_shape: str = "linear",
    drawdown_window: int = 0,
) -> pd.Series:
    """Scale target exposure between min and max from the equity drawdown state."""
    if max_drawdown_tolerance >= 0:
        raise ValueError("max_drawdown_tolerance must be negative")
    if min_risk < 0 or max_risk <= 0 or min_risk > max_risk:
        raise ValueError("risk bounds must satisfy 0 <= min_risk <= max_risk")
    if smoothing_span < 1:
        raise ValueError("smoothing_span must be at least 1")
    if drawdown_window < 0:
        raise ValueError("drawdown_window must be non-negative")
    if curve_shape not in {"linear", "aggressive", "conservative"}:
        raise ValueError("curve_shape must be linear, aggressive, or conservative")

    equity = pd.Series(equity_curve, dtype=float)
    if equity.empty:
        return pd.Series(dtype=float, index=equity.index, name="risk_appetite")

    if drawdown_window > 0:
        running_max = equity.rolling(drawdown_window, min_periods=1).max()
    else:
        running_max = equity.expanding().max()

    drawdown = equity / running_max - 1
    normalized = 1 - np.minimum(drawdown / max_drawdown_tolerance, 1)
    smoothed = normalized.ewm(span=smoothing_span).mean()

    power_map = {
        "aggressive": min_risk / max_risk if max_risk else 1.0,
        "conservative": max_risk / min_risk if min_risk else 1.0,
        "linear": 1.0,
    }
    transformed = smoothed ** power_map[curve_shape]
    result = min_risk + (max_risk - min_risk) * transformed
    return result.clip(lower=min_risk, upper=max_risk).rename("risk_appetite")


def temporary_boost(
    series1: pd.Series,
    series2: pd.Series,
    boost_val: float,
    duration: int,
) -> np.ndarray:
    """Boost series2 when series1 falls while series2 does not."""
    if duration < 1:
        raise ValueError("duration must be at least 1")
    if boost_val < 0:
        raise ValueError("boost_val must be non-negative")

    cond1 = series1.pct_change(duration) < 0
    cond2 = series2.pct_change(duration) >= 0
    return np.where(cond1 & cond2, boost_val, 1.0)


def calculate_raw_weight(
    upper_band: float,
    boost: float,
    gross_exposure: float,
) -> float:
    """Calculate an un-clipped strategy weight."""
    if upper_band < 0 or boost < 0 or gross_exposure < 0:
        raise ValueError("upper_band, boost, and gross_exposure must be non-negative")
    return upper_band * boost * gross_exposure


def clip_weight(
    weight: float,
    upper_band: float,
    min_exposure: float,
    max_exposure: float,
) -> float:
    """Clip a strategy weight to its failure-tolerance exposure range."""
    if upper_band < 0:
        raise ValueError("upper_band must be non-negative")
    if min_exposure < 0 or max_exposure < min_exposure:
        raise ValueError("exposure bounds are invalid")
    return float(
        np.clip(weight, upper_band * min_exposure, upper_band * max_exposure)
    )


def calculate_portfolio_return(
    w_mr: float,
    w_tf: float,
    mr_return: float,
    tf_return: float,
) -> float:
    """Combine mean-reversion and trend-following strategy returns."""
    return w_mr * mr_return + w_tf * tf_return


def exposure_allocation(
    mr_returns: pd.Series,
    tf_returns: pd.Series,
    initial_capital: float,
    upper_band_mr: float,
    upper_band_tf: float,
    min_exposure: float,
    max_exposure: float,
    k: int,
    risk_params: dict[str, float],
    curve_shape: str = "linear",
    mr_boost_val: float = 2.0,
    tf_boost_val: float = 1.1,
) -> pd.DataFrame:
    """Recursively allocate exposure across mean reversion and trend following."""
    mr = pd.Series(mr_returns, dtype=float)
    tf = pd.Series(tf_returns, dtype=float)
    if len(mr) != len(tf):
        raise ValueError("mr_returns and tf_returns must have the same length")
    if len(mr) == 0:
        return pd.DataFrame(
            columns=[
                "equity",
                "w_MR",
                "w_TF",
                "portfolio_returns",
                "gross_exposure",
                "mr_boost",
                "tf_boost",
            ],
            index=mr.index,
        )
    if not mr.index.equals(tf.index):
        raise ValueError("mr_returns and tf_returns must share the same index")
    if initial_capital <= 0:
        raise ValueError("initial_capital must be positive")
    if k < 1:
        raise ValueError("k must be at least 1")
    if upper_band_mr < 0 or upper_band_tf < 0:
        raise ValueError("upper bands must be non-negative")
    if min_exposure < 0 or max_exposure < min_exposure:
        raise ValueError("exposure bounds are invalid")

    required = {
        "max_drawdown_tolerance",
        "min_risk",
        "max_risk",
    }
    missing = required.difference(risk_params)
    if missing:
        raise ValueError(f"risk_params missing keys: {sorted(missing)}")

    n = len(mr)
    equity = np.full(n, np.nan, dtype=float)
    equity[0] = initial_capital
    w_mr_series = np.full(n, np.nan, dtype=float)
    w_tf_series = np.full(n, np.nan, dtype=float)
    portfolio_returns = np.full(n, np.nan, dtype=float)
    gross_exp = np.full(n, np.nan, dtype=float)

    mr_boost_series = temporary_boost(tf, mr, mr_boost_val, k)
    tf_boost_series = temporary_boost(mr, tf, tf_boost_val, k)

    for t in range(1, n):
        gross_exposure = risk_appetite(
            equity[:t],
            curve_shape=curve_shape,
            **risk_params,
        ).iloc[-1]
        gross_exp[t] = gross_exposure

        w_mr = calculate_raw_weight(
            upper_band_mr,
            mr_boost_series[t],
            gross_exposure,
        )
        w_tf = calculate_raw_weight(
            upper_band_tf,
            tf_boost_series[t],
            gross_exposure,
        )
        w_mr = clip_weight(w_mr, upper_band_mr, min_exposure, max_exposure)
        w_tf = clip_weight(w_tf, upper_band_tf, min_exposure, max_exposure)

        w_mr_series[t] = w_mr
        w_tf_series[t] = w_tf
        portfolio_returns[t] = calculate_portfolio_return(
            w_mr,
            w_tf,
            mr.iloc[t],
            tf.iloc[t],
        )
        equity[t] = equity[t - 1] * (1 + portfolio_returns[t])

    return pd.DataFrame(
        {
            "equity": equity,
            "w_MR": w_mr_series,
            "w_TF": w_tf_series,
            "portfolio_returns": portfolio_returns,
            "gross_exposure": gross_exp,
            "mr_boost": mr_boost_series,
            "tf_boost": tf_boost_series,
        },
        index=mr.index,
    )


def _validate_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def _validate_fraction(name: str, value: float) -> None:
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1")
