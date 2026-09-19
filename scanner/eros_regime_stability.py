"""EROS regime stability analytics helpers."""

from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = {
    "Timestamp",
    "Regime",
    "Rising Breadth %",
    "Falling Breadth %",
    "Average Trend Confidence %",
}


def analyze_eros_regime_stability(history: pd.DataFrame | None) -> pd.DataFrame:
    """Measure how stable the latest aggregate EROS regime has been."""
    if history is None or history.empty:
        return pd.DataFrame()
    if not REQUIRED_COLUMNS.issubset(history.columns):
        return pd.DataFrame()

    frame = history.copy()
    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], errors="coerce")
    for column in (
        "Rising Breadth %",
        "Falling Breadth %",
        "Average Trend Confidence %",
    ):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = frame.dropna(
        subset=[
            "Timestamp",
            "Rising Breadth %",
            "Falling Breadth %",
            "Average Trend Confidence %",
        ]
    ).sort_values("Timestamp")
    if frame.empty:
        return pd.DataFrame()

    latest_regime = str(frame.iloc[-1]["Regime"])
    current = frame[frame["Regime"].astype(str) == latest_regime]
    streak = 0
    for regime in reversed(frame["Regime"].astype(str).tolist()):
        if regime != latest_regime:
            break
        streak += 1

    breadth_range = round(
        float(
            current["Rising Breadth %"].max() - current["Rising Breadth %"].min()
        ),
        2,
    )
    confidence_range = round(
        float(
            current["Average Trend Confidence %"].max()
            - current["Average Trend Confidence %"].min()
        ),
        2,
    )

    if streak >= 5 and breadth_range <= 10 and confidence_range <= 10:
        stability = "HIGH"
    elif streak >= 3 and breadth_range <= 20 and confidence_range <= 20:
        stability = "MODERATE"
    elif streak >= 2:
        stability = "LOW"
    else:
        stability = "INITIAL"

    return pd.DataFrame(
        [
            {
                "Current Regime": latest_regime,
                "Regime Streak": streak,
                "Stability": stability,
                "Regime Snapshots": len(current),
                "Rising Breadth Range": breadth_range,
                "Confidence Range": confidence_range,
                "Latest Rising Breadth %": float(frame.iloc[-1]["Rising Breadth %"]),
                "Latest Falling Breadth %": float(frame.iloc[-1]["Falling Breadth %"]),
                "Latest Average Confidence %": float(
                    frame.iloc[-1]["Average Trend Confidence %"]
                ),
                "Total Snapshots": len(frame),
            }
        ]
    )
