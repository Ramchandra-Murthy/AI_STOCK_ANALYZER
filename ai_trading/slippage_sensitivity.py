"""Book-aligned slippage sensitivity diagnostics for research backtests."""

from __future__ import annotations

import numpy as np
import pandas as pd


def slippage_sensitivity(
    returns: pd.Series,
    *,
    turnover: pd.Series | None = None,
    slippage_bps: tuple[float, ...] = (0.0, 5.0, 10.0, 20.0),
) -> pd.DataFrame:
    """Estimate strategy returns under alternative execution-slippage assumptions."""
    if not slippage_bps:
        raise ValueError("slippage_bps must contain at least one value")
    rates = [float(value) for value in slippage_bps]
    if not all(np.isfinite(value) for value in rates):
        raise ValueError("slippage_bps values must be finite")
    if any(value < 0.0 for value in rates):
        raise ValueError("slippage_bps values must be non-negative")

    clean_returns = pd.to_numeric(returns, errors="coerce")
    if not np.isfinite(clean_returns.to_numpy(dtype=float)).all():
        raise ValueError("returns must contain only finite numeric values")
    if turnover is None:
        clean_turnover = clean_returns.ne(0.0).astype(float)
    else:
        clean_turnover = pd.to_numeric(turnover, errors="coerce").reindex(clean_returns.index)
        if not np.isfinite(clean_turnover.to_numpy(dtype=float)).all():
            raise ValueError("turnover must contain only finite numeric values aligned to returns")
        if (clean_turnover < 0.0).any():
            raise ValueError("turnover values must be non-negative")

    gross_return = float((1.0 + clean_returns).prod() - 1.0)
    total_turnover = float(clean_turnover.sum())
    rows: list[dict[str, float]] = []
    for bps in slippage_bps:
        rate = float(bps) / 10_000.0
        net_returns = clean_returns - clean_turnover * rate
        net_return = float((1.0 + net_returns).prod() - 1.0)
        rows.append(
            {
                "slippage_bps": float(bps),
                "gross_return": gross_return,
                "net_return": net_return,
                "slippage_drag": gross_return - net_return,
                "total_turnover": total_turnover,
            }
        )
    return pd.DataFrame(rows)


def slippage_sensitivity_summary(
    returns: pd.Series,
    *,
    turnover: pd.Series | None = None,
    slippage_bps: tuple[float, ...] = (0.0, 5.0, 10.0, 20.0),
) -> dict[str, float | None]:
    """Return gross and worst-case net outcomes across slippage assumptions."""
    report = slippage_sensitivity(
        returns,
        turnover=turnover,
        slippage_bps=slippage_bps,
    )
    if report.empty:
        return {
            "gross_return": None,
            "worst_net_return": None,
            "worst_slippage_bps": None,
        }
    worst_index = report["net_return"].idxmin()
    return {
        "gross_return": float(report["gross_return"].iloc[0]),
        "worst_net_return": float(report.loc[worst_index, "net_return"]),
        "worst_slippage_bps": float(report.loc[worst_index, "slippage_bps"]),
    }
