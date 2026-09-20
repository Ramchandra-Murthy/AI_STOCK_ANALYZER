"""Descriptive timing analytics for EROS regime transitions."""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = {"Timestamp", "Regime"}


def analyze_eros_regime_transition_intervals(
    history: pd.DataFrame | None,
) -> pd.DataFrame:
    """Describe elapsed time between consecutive EROS regime transitions."""
    if history is None or history.empty:
        return pd.DataFrame()
    if not REQUIRED_COLUMNS.issubset(history.columns):
        return pd.DataFrame()

    frame = history.loc[:, ["Timestamp", "Regime"]].copy()
    frame["Timestamp"] = pd.to_datetime(frame["Timestamp"], errors="coerce")
    frame = frame.dropna(subset=["Timestamp"]).sort_values("Timestamp")
    frame = frame.drop_duplicates(subset=["Timestamp"], keep="last")
    if len(frame) < 2:
        return pd.DataFrame()

    frame["Regime"] = frame["Regime"].astype(str).str.strip()
    frame = frame[frame["Regime"].ne("")]
    if len(frame) < 2:
        return pd.DataFrame()

    previous_regime = frame["Regime"].shift(1)
    changed = frame["Regime"].ne(previous_regime)
    transitions = frame.loc[changed, ["Timestamp", "Regime"]].copy()
    if transitions.empty:
        return pd.DataFrame()

    transitions["Previous Regime"] = previous_regime.loc[changed].to_numpy()
    transitions["Previous Transition Timestamp"] = transitions["Timestamp"].shift(1)
    transitions["Minutes Since Previous Transition"] = (
        (transitions["Timestamp"] - transitions["Previous Transition Timestamp"])
        .dt.total_seconds()
        .div(60)
        .round(2)
    )

    transitions = transitions.rename(columns={"Regime": "Current Regime"})
    transitions["Transition"] = (
        transitions["Previous Regime"] + " → " + transitions["Current Regime"]
    )
    transitions["Transition Count"] = range(1, len(transitions) + 1)

    return transitions[
        [
            "Timestamp",
            "Previous Regime",
            "Current Regime",
            "Transition",
            "Previous Transition Timestamp",
            "Minutes Since Previous Transition",
            "Transition Count",
        ]
    ].reset_index(drop=True)
