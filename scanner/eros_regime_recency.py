"""Descriptive recency analytics for the current EROS regime."""

from __future__ import annotations

import pandas as pd

from scanner.eros_regime_duration import analyze_eros_regime_duration


def analyze_eros_regime_recency(
    history: pd.DataFrame | None,
) -> pd.DataFrame:
    """Describe how recently the current EROS regime began."""
    runs = analyze_eros_regime_duration(history)
    if runs.empty:
        return pd.DataFrame()

    current = runs.iloc[-1]
    previous_regime = runs.iloc[-2]["Regime"] if len(runs) > 1 else "NO PRIOR REGIME"

    return pd.DataFrame(
        [
            {
                "Current Regime": current["Regime"],
                "Latest Timestamp": current["End"],
                "Current Run Start": current["Start"],
                "Current Run Snapshots": int(current["Snapshots"]),
                "Current Run Duration Minutes": float(current["Duration Minutes"]),
                "Previous Regime": previous_regime,
                "Historical Transitions": len(runs) - 1,
            }
        ]
    )
