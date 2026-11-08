"""Expanding-window walk-forward stability checks for market-impact calibration."""

from __future__ import annotations

import pandas as pd

from algorithmic_trading.impact_validation import validate_market_impact_out_of_sample


def validate_market_impact_walk_forward(
    observations: pd.DataFrame,
    *,
    min_train_size: int = 20,
    n_splits: int = 5,
) -> pd.DataFrame:
    """Evaluate calibration across sequential, non-overlapping holdouts.

    The calibration window expands after every fold. Each fold is fitted only
    on observations strictly earlier than its holdout window. Every observation
    after the initial training window is scored exactly once.

    The input must have a unique, increasing DatetimeIndex and the same three
    columns required by the out-of-sample validation helper. At least two
    observations are required in each holdout fold.
    """
    if not isinstance(observations, pd.DataFrame):
        raise TypeError("observations must be a pandas DataFrame")
    if min_train_size < 3:
        raise ValueError("min_train_size must be at least 3")
    if n_splits < 1:
        raise ValueError("n_splits must be at least 1")
    if not isinstance(observations.index, pd.DatetimeIndex):
        raise ValueError("observations must use a DatetimeIndex")
    if not observations.index.is_unique:
        raise ValueError("observations contains duplicate timestamps")
    if not observations.index.is_monotonic_increasing:
        raise ValueError("observations timestamps must be chronological")

    remaining = len(observations) - min_train_size
    if remaining < n_splits * 2:
        raise ValueError("not enough observations for the requested training size and holdout folds")

    base_size, extra = divmod(remaining, n_splits)
    fold_sizes = [base_size + (1 if fold < extra else 0) for fold in range(n_splits)]
    rows: list[dict[str, float | int | str | None]] = []
    holdout_start = min_train_size

    for fold_number, fold_size in enumerate(fold_sizes, start=1):
        holdout_end = holdout_start + fold_size
        calibration_data = observations.iloc[:holdout_start]
        holdout_data = observations.iloc[holdout_start:holdout_end]
        result = validate_market_impact_out_of_sample(calibration_data, holdout_data)
        rows.append(
            {
                "fold": fold_number,
                "calibration_start": str(calibration_data.index[0]),
                "calibration_end": str(calibration_data.index[-1]),
                "holdout_start": str(holdout_data.index[0]),
                "holdout_end": str(holdout_data.index[-1]),
                "calibration_observations": len(calibration_data),
                "holdout_observations": result.observations,
                "half_spread_bps": result.calibration.half_spread_bps,
                "impact_coefficient": result.calibration.impact_coefficient,
                "rmse_bps": result.rmse_bps,
                "mae_bps": result.mae_bps,
                "bias_bps": result.bias_bps,
                "r_squared": result.r_squared,
            }
        )
        holdout_start = holdout_end

    return pd.DataFrame(rows)
