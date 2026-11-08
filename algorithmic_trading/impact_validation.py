"""Chronological holdout validation for calibrated market-impact parameters."""

from __future__ import annotations

import numpy as np
import pandas as pd


_REQUIRED_COLUMNS = (
    "observed_shortfall_bps",
    "participation_rate",
    "volatility",
)


class MarketImpactHoldoutValidation:
    """Calibration fit plus strictly later holdout diagnostics."""

    def __init__(
        self,
        calibration: object,
        observations: int,
        rmse_bps: float,
        mae_bps: float,
        bias_bps: float,
        r_squared: float | None,
        predictions: pd.DataFrame,
    ) -> None:
        self.calibration = calibration
        self.observations = observations
        self.rmse_bps = rmse_bps
        self.mae_bps = mae_bps
        self.bias_bps = bias_bps
        self.r_squared = r_squared
        self.predictions = predictions


def _prepare_observations(data: pd.DataFrame, label: str) -> pd.DataFrame:
    if not isinstance(data, pd.DataFrame):
        raise TypeError(f"{label} must be a pandas DataFrame")
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError(f"{label} must use a DatetimeIndex")
    if not data.index.is_unique:
        raise ValueError(f"{label} contains duplicate timestamps")
    if not data.index.is_monotonic_increasing:
        raise ValueError(f"{label} timestamps must be chronological")
    missing = sorted(set(_REQUIRED_COLUMNS).difference(data.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {', '.join(missing)}")
    prepared = data.loc[:, list(_REQUIRED_COLUMNS)].apply(pd.to_numeric, errors="coerce")
    values = prepared.to_numpy(dtype=float)
    if len(prepared) == 0 or not np.isfinite(values).all():
        raise ValueError(f"{label} must contain non-empty finite numeric observations")
    if (prepared["observed_shortfall_bps"] < 0).any():
        raise ValueError(f"{label} shortfall must be non-negative")
    if (
        (prepared["participation_rate"] <= 0)
        | (prepared["participation_rate"] > 1)
    ).any():
        raise ValueError(f"{label} participation_rate must be in (0, 1]")
    if (prepared["volatility"] < 0).any():
        raise ValueError(f"{label} volatility must be non-negative")
    return prepared


def validate_market_impact_out_of_sample(
    calibration_data: pd.DataFrame,
    holdout_data: pd.DataFrame,
) -> MarketImpactHoldoutValidation:
    """Fit only on an earlier period and score untouched, strictly later observations.

    Both frames require a chronological DatetimeIndex and columns named
    observed_shortfall_bps, participation_rate, and volatility. The final
    calibration timestamp must precede the first holdout timestamp. No
    parameter is refitted using holdout observations.
    """
    calibration = _prepare_observations(calibration_data, "calibration_data")
    holdout = _prepare_observations(holdout_data, "holdout_data")
    if len(calibration) < 3:
        raise ValueError("calibration_data requires at least three observations")
    if holdout.index.tz != calibration.index.tz:
        raise ValueError("calibration and holdout timestamps must use the same timezone")
    if calibration.index[-1] >= holdout.index[0]:
        raise ValueError("holdout_data must start strictly after calibration_data ends")

    from algorithmic_trading.impact_calibration import calibrate_market_impact

    fitted = calibrate_market_impact(
        calibration["observed_shortfall_bps"],
        calibration["participation_rate"],
        calibration["volatility"],
    )
    feature = (
        holdout["volatility"].to_numpy(dtype=float)
        * np.sqrt(holdout["participation_rate"].to_numpy(dtype=float))
        * 10_000.0
    )
    predicted = fitted.half_spread_bps + fitted.impact_coefficient * feature
    actual = holdout["observed_shortfall_bps"].to_numpy(dtype=float)
    residual = actual - predicted
    rmse = float(np.sqrt(np.mean(np.square(residual))))
    mae = float(np.mean(np.abs(residual)))
    bias = float(np.mean(residual))
    total_variance = float(np.square(actual - actual.mean()).sum())
    r_squared = (
        float(1.0 - np.square(residual).sum() / total_variance)
        if total_variance > 0
        else None
    )
    predictions = pd.DataFrame(
        {
            "observed_shortfall_bps": actual,
            "predicted_shortfall_bps": predicted,
            "residual_bps": residual,
            "participation_rate": holdout["participation_rate"].to_numpy(dtype=float),
            "volatility": holdout["volatility"].to_numpy(dtype=float),
        },
        index=holdout.index,
    )
    return MarketImpactHoldoutValidation(
        calibration=fitted,
        observations=len(holdout),
        rmse_bps=rmse,
        mae_bps=mae,
        bias_bps=bias,
        r_squared=r_squared,
        predictions=predictions,
    )
