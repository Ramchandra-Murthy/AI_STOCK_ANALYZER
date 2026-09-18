"""EROS fusion history analytics helpers."""

from __future__ import annotations

import pandas as pd


def summarize_eros_fusion_history(
    history: pd.DataFrame | None,
) -> pd.DataFrame:
    """Summarize repeated EROS fusion observations by symbol and exchange."""
    if history is None or history.empty:
        return pd.DataFrame()

    required = {"Timestamp", "Symbol", "Exchange", "Fusion Score"}
    if not required.issubset(history.columns):
        return pd.DataFrame()

    frame = history.copy()
    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], errors="coerce")
    frame["Fusion Score"] = pd.to_numeric(frame["Fusion Score"], errors="coerce")
    frame = frame.dropna(subset=["Timestamp", "Fusion Score"])
    if frame.empty:
        return pd.DataFrame()

    summary = (
        frame.groupby(["Symbol", "Exchange"], as_index=False)
        .agg(
            Observations=("Symbol", "size"),
            Average_Fusion=("Fusion Score", "mean"),
            Peak_Fusion=("Fusion Score", "max"),
            Latest_Fusion=("Fusion Score", "last"),
            First_Seen=("Timestamp", "min"),
            Last_Seen=("Timestamp", "max"),
        )
        .sort_values(
            ["Latest_Fusion", "Observations", "Average_Fusion"],
            ascending=[False, False, False],
        )
        .reset_index(drop=True)
    )
    summary["Persistence"] = pd.cut(
        summary["Observations"],
        bins=[0, 1, 2, 4, float("inf")],
        labels=["ONE", "REPEATED", "PERSISTENT", "HIGH PERSISTENCE"],
    )
    return summary
