"""Tests for the multi-stock ML scanner."""

import numpy as np
import pandas as pd

from ai_trading.ml_scanner import scan_frames


def _frame(seed: int, rows: int = 220) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0008, 0.015, rows)
    close = 100.0 * np.exp(np.cumsum(returns))
    return pd.DataFrame(
        {
            "Close": close,
            "Volume": rng.integers(900_000, 1_100_000, rows),
        }
    )


def test_scan_frames_returns_ranked_ml_results() -> None:
    result = scan_frames(
        {"RELIANCE": _frame(1), "TCS": _frame(2)},
        exchange="NSE",
        horizon=5,
        threshold=0.0,
    )
    assert len(result) == 2
    assert {
        "symbol",
        "probability_up_pct",
        "confidence_pct",
        "accuracy_pct",
        "roc_auc",
        "signal",
        "regime",
        "regime_score",
        "regime_strength_pct",
    }.issubset(result.columns)
    assert result["confidence_pct"].between(0, 100).all()
    assert result["probability_up_pct"].between(0, 100).all()
    assert result["regime_strength_pct"].between(0, 100).all()
