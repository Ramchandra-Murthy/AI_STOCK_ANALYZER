"""Descriptive recency analytics for the current EROS regime."""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = {"Timestamp", "Regime"}


def analyze_eros_regime_recency(
    history: pd.DataFrame | None,
) -> pd.DataFrame:
    """Describe how recently the current EROS regime began."""
    if history is None or history.empty:
        return pd.DataFrame()
    if not REQUIRED_COLUMNS.issubset(history.columns):
        return pd.DataFrame()

    frame = history.loc[:, ["Timestamp", "Regime"]].copy()
    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], errors="coerce")
    frame = frame.dropna(subset=["Timestamp"]).sort_values("Timestamp")
    frame = frame.drop_duplicates(subset=["Timestamp"], keep="last")
    if frame.empty:
        return pd.DataFrame()

    frame["Regime"] = frame["Regime"].astype(str)
    frame = frame[frame["Regime"].str.strip().ne("")]
    if frame.empty:
        return pd.DataFrame()

    current_regime = frame.iloc[-1]["Regime"]
    run_start_index = len(frame) - 1
    while run_start_index > 0 and frame.iloc[run_start_index - 1]["Regime"] == current_regime:
        run_start_index -= 1

    current_run = frame.iloc[run_start_index:]
    run_start = current_run.iloc[0]["Timestamp"]
    latest_timestamp = frame.iloc[-1]["Timestamp"]
    previous_regime = (
        frame.iloc[run_start_index - 1]["Regime"] if run_start_index > 0 else "NO PRIOR REGIME"
    )
    transition_count = int((frame["Regime"] != frame["Regime"].shift()).sum() - 1)

    return pd.DataFrame(
        [
            {
                "Current Regime": current_regime,
                "Latest Timestamp": latest_timestamp,
                "Current Run Start": run_start,
                "Current Run Snapshots": len(current_run),
                "Current Run Duration Minutes": round(
                    (latest_timestamp - run_start).total_seconds() / 60, 2
                ),
                "Previous Regime": previous_regime,
                "Historical Transitions": max(transition_count, 0),
            }
        ]
    )
