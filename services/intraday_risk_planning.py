"""Helpers for descriptive intraday risk and trade-planning metrics."""

from __future__ import annotations

import pandas as pd

DEFAULT_INTRADAY_CAPITAL = 10_000.0
MAX_INTRADAY_CAPITAL = 10_000.0
DEFAULT_INTRADAY_RISK_BUDGET = 500.0
MAX_INTRADAY_LOSS_PER_TRADE = 500.0


def risk_plan_frame(
    results: pd.DataFrame,
    risk_budget: float = DEFAULT_INTRADAY_RISK_BUDGET,
    capital_limit: float = DEFAULT_INTRADAY_CAPITAL,
) -> pd.DataFrame:
    """Add position-size and capital-use calculations to existing trade references."""
    if results is None or results.empty:
        return pd.DataFrame(columns=_columns(results))

    frame = results.copy()
    for column in ("Price", "Entry reference", "Stop reference", "Risk per share"):
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if "Risk per share" not in frame.columns:
        if {"Entry reference", "Stop reference"}.issubset(frame.columns):
            frame["Risk per share"] = (frame["Entry reference"] - frame["Stop reference"]).abs()
        else:
            frame["Risk per share"] = pd.NA

    bounded_risk_budget = min(MAX_INTRADAY_LOSS_PER_TRADE, max(0.0, float(risk_budget)))
    bounded_capital_limit = min(MAX_INTRADAY_CAPITAL, max(0.0, float(capital_limit)))
    frame["Risk budget"] = bounded_risk_budget
    frame["Capital limit"] = bounded_capital_limit
    frame["Risk-based quantity"] = (
        (bounded_risk_budget / frame["Risk per share"].replace(0, pd.NA)).fillna(0).floordiv(1)
    )
    entry = frame.get("Entry reference", frame.get("Price"))
    frame["Capital-based quantity"] = (
        (bounded_capital_limit / pd.to_numeric(entry, errors="coerce")).fillna(0).floordiv(1)
    )
    frame["Suggested quantity"] = frame[["Risk-based quantity", "Capital-based quantity"]].min(
        axis=1
    )
    frame["Planned capital"] = (
        pd.to_numeric(entry, errors="coerce") * frame["Suggested quantity"]
    ).round(2)
    frame["Planned risk"] = (frame["Risk per share"] * frame["Suggested quantity"]).round(2)

    return frame.reset_index(drop=True)


def _columns(results: pd.DataFrame | None) -> list[str]:
    """Return stable columns for an empty risk-plan frame."""
    base = list(results.columns) if results is not None else []
    return base + [
        column
        for column in (
            "Risk budget",
            "Capital limit",
            "Risk-based quantity",
            "Capital-based quantity",
            "Suggested quantity",
            "Planned capital",
            "Planned risk",
        )
        if column not in base
    ]
