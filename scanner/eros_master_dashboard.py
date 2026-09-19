"""EROS master dashboard aggregation helpers."""

from __future__ import annotations

import pandas as pd

from scanner.eros_regime_momentum import analyze_eros_regime_momentum
from scanner.eros_regime_signal_sync import analyze_eros_regime_signal_sync
from scanner.eros_regime_stability import analyze_eros_regime_stability
from scanner.eros_signal_alignment import analyze_eros_signal_alignment
from scanner.eros_signal_lifecycle import analyze_eros_signal_lifecycle
from scanner.eros_trend_confidence import analyze_eros_trend_confidence


def build_eros_master_dashboard(
    history: pd.DataFrame | None,
    current_fusion: pd.DataFrame | None = None,
    regime_history: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate existing EROS analytics into a compact summary and signal board."""
    if history is None or history.empty:
        return pd.DataFrame(), pd.DataFrame()

    lifecycle = analyze_eros_signal_lifecycle(history, current_fusion)
    confidence = analyze_eros_trend_confidence(history, current_fusion)
    alignment = analyze_eros_signal_alignment(history, current_fusion)
    regime_sync = analyze_eros_regime_signal_sync(history, regime_history, current_fusion)

    signal = (
        history.sort_values("Timestamp").groupby(["Symbol", "Exchange"], as_index=False).tail(1)
    )

    if current_fusion is not None and not current_fusion.empty:
        keys = ["Symbol", "Exchange"]
        if set(keys).issubset(current_fusion.columns):
            signal = current_fusion.copy()

    signal = signal.copy()
    signal_columns = [
        column
        for column in ["Symbol", "Exchange", "Sector", "Fusion Score"]
        if column in signal.columns
    ]
    signal = signal[signal_columns]

    for frame in (lifecycle, confidence, alignment, regime_sync):
        if not frame.empty and {"Symbol", "Exchange"}.issubset(frame.columns):
            columns = [
                column
                for column in frame.columns
                if column
                in {
                    "Symbol",
                    "Exchange",
                    "Lifecycle",
                    "Trend Consensus",
                    "Trend Confidence %",
                    "Confidence",
                    "Trend Quality",
                    "Alignment %",
                    "Alignment",
                    "Persistence",
                    "Current Regime",
                    "Regime Direction",
                    "Signal Direction",
                    "Regime-Signal Sync",
                }
            ]
            signal = signal.merge(
                frame[columns],
                on=["Symbol", "Exchange"],
                how="left",
            )

    summary_values: dict[str, object] = {
        "Signals": len(signal),
        "Average Fusion Score": (
            round(float(pd.to_numeric(signal["Fusion Score"], errors="coerce").mean()), 2)
            if "Fusion Score" in signal.columns
            else None
        ),
    }

    if "Lifecycle" in signal.columns:
        summary_values["New Signals"] = int((signal["Lifecycle"] == "NEW").sum())
        summary_values["Persistent Signals"] = int((signal["Lifecycle"] == "PERSISTENT").sum())
        summary_values["Accelerating Signals"] = int((signal["Lifecycle"] == "ACCELERATING").sum())
        summary_values["Weakening Signals"] = int((signal["Lifecycle"] == "WEAKENING").sum())
        summary_values["Expired Signals"] = int((signal["Lifecycle"] == "EXPIRED").sum())

    if "Alignment %" in signal.columns:
        alignment_values = pd.to_numeric(signal["Alignment %"], errors="coerce")
        summary_values["Average Signal Alignment %"] = round(float(alignment_values.mean()), 2)

    if "Regime-Signal Sync" in signal.columns:
        sync = signal["Regime-Signal Sync"]
        summary_values["Regime-Signal Aligned Signals"] = int((sync == "ALIGNED").sum())
        summary_values["Regime-Signal Mismatch Signals"] = int((sync == "MISMATCH").sum())

    if "Trend Confidence %" in signal.columns:
        confidence_values = pd.to_numeric(signal["Trend Confidence %"], errors="coerce")
        summary_values["Average Trend Confidence %"] = round(float(confidence_values.mean()), 2)

    if regime_history is not None and not regime_history.empty:
        momentum = analyze_eros_regime_momentum(regime_history)
        stability = analyze_eros_regime_stability(regime_history)
        if not momentum.empty:
            row = momentum.iloc[0]
            summary_values["Current Regime"] = row["Current Regime"]
            summary_values["Regime Momentum"] = row["Regime Momentum"]
        if not stability.empty:
            row = stability.iloc[0]
            summary_values["Regime Stability"] = row["Stability"]
            summary_values["Regime Streak"] = row["Regime Streak"]

    summary = pd.DataFrame([summary_values])
    return summary, signal.sort_values(
        ["Fusion Score", "Symbol"],
        ascending=[False, True],
        na_position="last",
    ).reset_index(drop=True)
