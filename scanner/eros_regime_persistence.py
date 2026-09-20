"""EROS aggregate regime persistence analytics helpers."""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = {"Timestamp", "Regime"}


def analyze_eros_regime_persistence(history: pd.DataFrame | None) -> pd.DataFrame:
    """Summarize how consistently each aggregate EROS regime persists."""
    if history is None or history.empty:
        return pd.DataFrame()
    if not REQUIRED_COLUMNS.issubset(history.columns):
        return pd.DataFrame()

    frame = history.loc[:, ["Timestamp", "Regime"]].copy()
    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], errors="coerce")
    frame["Regime"] = frame["Regime"].astype(str)
    frame = frame.dropna(subset=["Timestamp"]).sort_values("Timestamp")
    frame = frame.drop_duplicates(subset=["Timestamp"], keep="last")
    if frame.empty:
        return pd.DataFrame()

    run_id = frame["Regime"].ne(frame["Regime"].shift()).cumsum()
    runs = (
        frame.groupby(run_id, sort=True)
        .agg(
            Regime=("Regime", "first"),
            Start=("Timestamp", "min"),
            End=("Timestamp", "max"),
            Snapshots=("Timestamp", "size"),
        )
        .reset_index(drop=True)
    )
    runs["Duration Minutes"] = (
        (runs["End"] - runs["Start"]).dt.total_seconds().div(60).round(2)
    )
    runs["Is Current"] = runs.index == len(runs) - 1

    grouped = runs.groupby("Regime", sort=False)
    result = grouped.agg(
        Runs=("Regime", "size"),
        Total_Snapshots=("Snapshots", "sum"),
        Average_Run_Snapshots=("Snapshots", "mean"),
        Median_Run_Snapshots=("Snapshots", "median"),
        Maximum_Run_Snapshots=("Snapshots", "max"),
        Average_Duration_Minutes=("Duration Minutes", "mean"),
        Median_Duration_Minutes=("Duration Minutes", "median"),
        Maximum_Duration_Minutes=("Duration Minutes", "max"),
    ).reset_index()

    current = runs[runs["Is Current"]].iloc[0]
    result["Current Run Snapshots"] = result["Regime"].map(
        {current["Regime"]: int(current["Snapshots"])}
    ).fillna(0)
    result["Current Run Duration Minutes"] = result["Regime"].map(
        {current["Regime"]: float(current["Duration Minutes"])}
    ).fillna(0.0)
    result["Current Run"] = result["Regime"] == current["Regime"]

    opportunities = runs["Snapshots"].sub(1).clip(lower=0)
    continued = opportunities.sum()
    same_regime_links = frame["Regime"].eq(frame["Regime"].shift()).iloc[1:].sum()
    overall_continuation = (
        round(float(same_regime_links / continued * 100), 2) if continued else 0.0
    )
    result["Overall Continuation %"] = overall_continuation

    numeric_columns = [
        "Average_Run_Snapshots",
        "Median_Run_Snapshots",
        "Maximum_Run_Snapshots",
        "Average_Duration_Minutes",
        "Median_Duration_Minutes",
        "Maximum_Duration_Minutes",
        "Current Run Duration Minutes",
        "Overall Continuation %",
    ]
    result[numeric_columns] = result[numeric_columns].round(2)

    return result[
        [
            "Regime",
            "Runs",
            "Total_Snapshots",
            "Average_Run_Snapshots",
            "Median_Run_Snapshots",
            "Maximum_Run_Snapshots",
            "Average_Duration_Minutes",
            "Median_Duration_Minutes",
            "Maximum_Duration_Minutes",
            "Current Run",
            "Current Run Snapshots",
            "Current Run Duration Minutes",
            "Overall Continuation %",
        ]
    ]
