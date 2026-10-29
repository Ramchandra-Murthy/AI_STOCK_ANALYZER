"""Select research strategies compatible with a supplied market regime.

Combines tournament metrics, explicit strategy-regime metadata, and quality-gate
decisions. It does not classify the market, generate signals, or submit orders.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd

SUPPORTED_REGIMES = {"BULLISH", "BEARISH", "RANGE / MIXED"}
PAPER_ELIGIBLE_STATUS = "eligible_for_paper_trading"


def select_regime_compatible_strategies(
    tournament: pd.DataFrame,
    *,
    regime: str,
    strategy_regimes: Mapping[str, Sequence[str]],
    quality_results: Mapping[str, Mapping[str, object]],
    top_n: int = 5,
) -> pd.DataFrame:
    """Rank validated tournament strategies explicitly mapped to the regime.

    Strategy-regime metadata is caller-supplied; behavior is never guessed from
    a strategy name. Only strategies passing the quality gate are returned.
    Results are paper-trading candidates, not live-trading authorization.
    """
    if regime not in SUPPORTED_REGIMES:
        raise ValueError(f"unsupported regime: {regime}")
    if isinstance(top_n, bool) or not isinstance(top_n, int) or top_n < 1:
        raise ValueError("top_n must be a positive integer")
    required = {"strategy", "eligible", "sharpe_ratio", "max_drawdown"}
    if not required.issubset(tournament.columns):
        missing = sorted(required.difference(tournament.columns))
        raise ValueError(f"tournament is missing required columns: {missing}")

    rows: list[dict[str, object]] = []
    for _, row in tournament.iterrows():
        name = row["strategy"]
        if not isinstance(name, str) or not name:
            continue
        if regime not in strategy_regimes.get(name, ()):
            continue
        quality = quality_results.get(name, {})
        if quality.get("status") != PAPER_ELIGIBLE_STATUS or not bool(row["eligible"]):
            continue
        metrics = pd.to_numeric(
            pd.Series([row["sharpe_ratio"], row["max_drawdown"]]),
            errors="coerce",
        )
        if metrics.isna().any():
            continue
        sharpe, drawdown = (float(value) for value in metrics)
        rows.append(
            {
                "strategy": name,
                "regime": regime,
                "sharpe_ratio": sharpe,
                "max_drawdown": drawdown,
                "quality_status": PAPER_ELIGIBLE_STATUS,
                "selection_scope": "paper_trading_only",
                "live_trading_authorized": False,
            }
        )

    columns = [
        "strategy",
        "regime",
        "sharpe_ratio",
        "max_drawdown",
        "quality_status",
        "selection_scope",
        "live_trading_authorized",
    ]
    result = pd.DataFrame(rows, columns=columns)
    if result.empty:
        return result
    return (
        result.sort_values(
            ["sharpe_ratio", "max_drawdown", "strategy"],
            ascending=[False, True, True],
        )
        .head(top_n)
        .reset_index(drop=True)
    )
