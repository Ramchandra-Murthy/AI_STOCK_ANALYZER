"""Monthly return diagnostics for research backtests."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _compound_returns(values: pd.Series) -> float:
    """Compound simple returns while guarding invalid and overflowing inputs."""
    array = values.to_numpy(dtype=float)
    if (array < -1.0).any():
        raise ValueError("daily returns cannot be below -100%")
    if (array == -1.0).any():
        return -1.0

    log_growth = float(np.log1p(array).sum())
    if not np.isfinite(log_growth) or log_growth > np.log(np.finfo(float).max):
        raise ValueError("compounded monthly return is not finite")
    return float(np.expm1(log_growth))


def monthly_return_diagnostics(returns: pd.Series) -> pd.DataFrame:
    """Aggregate daily returns into compounded calendar-month returns."""
    clean = pd.to_numeric(returns, errors="coerce").dropna()
    if not np.isfinite(clean.to_numpy(dtype=float)).all():
        raise ValueError("returns must contain only finite numeric values")
    columns = ["year", "month", "return"]
    if clean.empty:
        return pd.DataFrame(columns=columns)

    index = pd.to_datetime(clean.index, errors="coerce")
    if index.isna().any():
        raise ValueError("returns index must contain valid timestamps")

    frame = clean.copy()
    frame.index = index
    grouped = frame.groupby([frame.index.year, frame.index.month])
    result = grouped.apply(_compound_returns)
    result.index.names = ["year", "month"]
    return result.rename("return").reset_index()
