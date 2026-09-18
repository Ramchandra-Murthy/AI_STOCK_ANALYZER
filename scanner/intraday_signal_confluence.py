"""Intraday signal confluence helpers."""

from __future__ import annotations

import pandas as pd


def compute_signal_confluence(board: pd.DataFrame | None) -> pd.DataFrame:
    """Combine intraday momentum, volume, breakout, and relative strength signals."""
    if board is None or board.empty:
        return pd.DataFrame()

    frame = board.copy()
    required = {"Symbol", "Exchange"}
    if not required.issubset(frame.columns):
        return pd.DataFrame()

    score = pd.Series(0.0, index=frame.index)
    score += (pd.to_numeric(frame.get("2-min change %"), errors="coerce").fillna(0) >= 0.75) * 15
    score += (pd.to_numeric(frame.get("3-min change %"), errors="coerce").fillna(0) >= 1.0) * 15
    score += (pd.to_numeric(frame.get("5-min change %"), errors="coerce").fillna(0) >= 1.5) * 10
    score += (pd.to_numeric(frame.get("10-min change %"), errors="coerce").fillna(0) >= 2.0) * 10
    score += (pd.to_numeric(frame.get("15-min change %"), errors="coerce").fillna(0) >= 2.5) * 10
    score += (pd.to_numeric(frame.get("Volume surge x"), errors="coerce").fillna(0) >= 1.5) * 15
    score += (frame.get("Breakout", pd.Series("", index=frame.index)).astype(str) == "YES") * 10
    score += (
        pd.to_numeric(frame.get("Relative Strength"), errors="coerce").fillna(0) > 0
    ) * 15

    result = frame.copy()
    result["Confluence Score"] = score.astype(float)
    result["Confluence"] = pd.cut(
        result["Confluence Score"],
        bins=[-1, 24, 49, 74, 100],
        labels=["LOW", "MODERATE", "HIGH", "VERY HIGH"],
    )
    result = result.sort_values(
        ["Confluence Score", "Relative Strength", "3-min change %"],
        ascending=[False, False, False],
        na_position="last",
    ).reset_index(drop=True)
    return result
