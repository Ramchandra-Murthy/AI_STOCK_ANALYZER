"""Descriptive trade-journal performance analytics."""

from __future__ import annotations

import pandas as pd


def trade_performance_frame(history: list[dict] | None) -> pd.DataFrame:
    """Return journal rows with realized R multiple where available."""
    frame = pd.DataFrame(history or [])
    if frame.empty:
        return frame
    result = frame.copy()
    risk = pd.to_numeric(result.get("Risk"), errors="coerce")
    pnl = pd.to_numeric(result.get("PnL"), errors="coerce")
    result["R Multiple"] = (pnl / risk).where(risk > 0)
    return result


def performance_summary(history: list[dict] | None) -> pd.DataFrame:
    """Return descriptive closed-trade statistics."""
    frame = trade_performance_frame(history)
    if frame.empty:
        return pd.DataFrame(
            [{"Trades": 0, "Closed": 0, "Wins": 0, "Losses": 0, "Win rate %": 0.0, "Net PnL": 0.0}]
        )
    pnl = pd.to_numeric(frame["PnL"], errors="coerce")
    closed = frame[pnl.notna()].copy()
    if closed.empty:
        return pd.DataFrame(
            [{"Trades": len(frame), "Closed": 0, "Wins": 0, "Losses": 0, "Win rate %": 0.0, "Net PnL": 0.0}]
        )
    wins = int((closed["PnL"] > 0).sum())
    losses = int((closed["PnL"] < 0).sum())
    return pd.DataFrame(
        [{
            "Trades": len(frame),
            "Closed": len(closed),
            "Wins": wins,
            "Losses": losses,
            "Win rate %": round(wins / len(closed) * 100, 2),
            "Net PnL": round(float(closed["PnL"].sum()), 2),
            "Average R": round(float(closed["R Multiple"].mean()), 2),
        }]
    )


def setup_performance(history: list[dict] | None) -> pd.DataFrame:
    """Group realized journal results by setup."""
    frame = trade_performance_frame(history)
    if frame.empty or "Setup" not in frame.columns:
        return pd.DataFrame(
            columns=["Setup", "Trades", "Closed", "Win rate %", "Net PnL", "Average R"]
        )
    frame["PnL"] = pd.to_numeric(frame["PnL"], errors="coerce")
    rows = []
    for setup, group in frame.groupby("Setup", dropna=False):
        closed = group[group["PnL"].notna()]
        wins = int((closed["PnL"] > 0).sum())
        rows.append({
            "Setup": str(setup),
            "Trades": len(group),
            "Closed": len(closed),
            "Win rate %": round(wins / len(closed) * 100, 2) if len(closed) else 0.0,
            "Net PnL": round(float(closed["PnL"].sum()), 2) if len(closed) else 0.0,
            "Average R": round(float(closed["R Multiple"].mean()), 2) if len(closed) else 0.0,
        })
    return pd.DataFrame(rows)


def side_performance(history: list[dict] | None) -> pd.DataFrame:
    """Group realized journal results by LONG/SHORT side."""
    frame = trade_performance_frame(history)
    if frame.empty or "Side" not in frame.columns:
        return pd.DataFrame(
            columns=["Side", "Trades", "Closed", "Win rate %", "Net PnL", "Average R"]
        )
    frame["PnL"] = pd.to_numeric(frame["PnL"], errors="coerce")
    rows = []
    for side, group in frame.groupby("Side", dropna=False):
        closed = group[group["PnL"].notna()]
        wins = int((closed["PnL"] > 0).sum())
        rows.append({
            "Side": str(side),
            "Trades": len(group),
            "Closed": len(closed),
            "Win rate %": round(wins / len(closed) * 100, 2) if len(closed) else 0.0,
            "Net PnL": round(float(closed["PnL"].sum()), 2) if len(closed) else 0.0,
            "Average R": round(float(closed["R Multiple"].mean()), 2) if len(closed) else 0.0,
        })
    return pd.DataFrame(rows)
