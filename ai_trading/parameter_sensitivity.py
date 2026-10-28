"""Book-aligned parameter sensitivity diagnostics for backtest returns."""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

from ai_trading.risk_metrics import max_drawdown, sharpe_ratio


def _clean_parameter_returns(returns: pd.Series, parameter: str) -> pd.Series:
    """Validate one configuration's simple returns without hiding malformed values."""
    numeric = pd.to_numeric(returns, errors="coerce")
    invalid = returns.notna() & numeric.isna()
    if invalid.any():
        raise ValueError(
            f"returns for {parameter!r} must contain only numeric values or missing values"
        )
    clean = numeric.dropna()
    values = clean.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError(f"returns for {parameter!r} must contain only finite numeric values")
    if (values < -1.0).any():
        raise ValueError(f"returns for {parameter!r} cannot be below -100%")
    return clean.reset_index(drop=True)


def parameter_sensitivity_report(
    returns_by_parameter: Mapping[str, pd.Series],
    *,
    periods_per_year: float = 252.0,
) -> pd.DataFrame:
    """Compare return and risk metrics across parameter configurations."""
    if isinstance(periods_per_year, (bool, np.bool_)):
        raise ValueError("periods_per_year must be finite and positive")
    try:
        periods_per_year = float(periods_per_year)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("periods_per_year must be finite and positive") from exc
    if not math.isfinite(periods_per_year) or periods_per_year <= 0:
        raise ValueError("periods_per_year must be finite and positive")
    if not returns_by_parameter:
        raise ValueError("returns_by_parameter must not be empty")

    rows: list[dict[str, float | str]] = []
    for parameter, returns in returns_by_parameter.items():
        clean = _clean_parameter_returns(returns, str(parameter))
        if clean.empty:
            raise ValueError(f"returns for {parameter!r} must contain valid observations")

        total_return = float((1.0 + clean).prod() - 1.0)
        if not math.isfinite(total_return):
            raise ValueError(f"total return for {parameter!r} overflowed")
        rows.append(
            {
                "parameter": str(parameter),
                "observations": float(len(clean)),
                "total_return": total_return,
                "sharpe_ratio": sharpe_ratio(clean, periods_per_year=periods_per_year),
                "max_drawdown": max_drawdown(clean),
            }
        )

    result = pd.DataFrame(rows)
    result["return_rank"] = result["total_return"].rank(ascending=False, method="min")
    result["sharpe_rank"] = result["sharpe_ratio"].rank(ascending=False, method="min")
    return result.sort_values("return_rank").reset_index(drop=True)


def parameter_sensitivity_summary(
    report: pd.DataFrame,
) -> dict[str, float | str | None]:
    """Summarize the performance spread across parameter configurations."""
    required = {"parameter", "total_return", "sharpe_ratio", "max_drawdown"}
    missing = sorted(required.difference(report.columns))
    if missing:
        raise KeyError(f"missing required columns: {missing}")
    if report.empty:
        return {
            "configurations": 0.0,
            "best_parameter": None,
            "worst_parameter": None,
            "return_spread": None,
            "sharpe_spread": None,
            "drawdown_spread": None,
        }

    metric_columns = ["total_return", "sharpe_ratio", "max_drawdown"]
    for column in metric_columns:
        values = pd.to_numeric(report[column], errors="coerce")
        if not np.isfinite(values.to_numpy(dtype=float)).all():
            raise ValueError(f"{column} must contain only finite numeric values")

    best = report.loc[report["total_return"].idxmax()]
    worst = report.loc[report["total_return"].idxmin()]

    return {
        "configurations": float(len(report)),
        "best_parameter": str(best["parameter"]),
        "worst_parameter": str(worst["parameter"]),
        "return_spread": float(report["total_return"].max() - report["total_return"].min()),
        "sharpe_spread": float(report["sharpe_ratio"].max() - report["sharpe_ratio"].min()),
        "drawdown_spread": float(report["max_drawdown"].max() - report["max_drawdown"].min()),
    }
