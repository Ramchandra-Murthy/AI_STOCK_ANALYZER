"""Cross-sectional walk-forward validation for multiple symbols."""

from __future__ import annotations

import pandas as pd

from algorithmic_trading.signal_backtest import generate_pipeline_signals
from algorithmic_trading.trading_costs import IndiaEquityCostModel
from algorithmic_trading.walk_forward_validation import walk_forward_evaluate


def evaluate_symbol_universe(
    frames: dict[str, pd.DataFrame],
    benchmark: pd.Series,
    *,
    initial_capital: float = 100_000.0,
    cost_bps: float = 10.0,
    cost_model: IndiaEquityCostModel | None = None,
    min_train_size: int = 252,
    n_splits: int = 5,
    minimum_observations: int = 300,
) -> pd.DataFrame:
    """Evaluate each symbol independently and preserve failures as explicit rows.

    Frames must contain High, Low, and Close columns. The function does not
    select winners or combine assets into a portfolio; each symbol receives
    its own independent walk-forward evaluation.
    """
    if not frames:
        raise ValueError("frames must contain at least one symbol")
    if not isinstance(benchmark, pd.Series) or benchmark.empty:
        raise ValueError("benchmark must be a non-empty price series")
    if initial_capital <= 0:
        raise ValueError("initial_capital must be positive")
    if cost_bps < 0:
        raise ValueError("cost_bps must be non-negative")
    if min_train_size < 2:
        raise ValueError("min_train_size must be at least 2")
    if n_splits < 1:
        raise ValueError("n_splits must be at least 1")
    if minimum_observations < 2:
        raise ValueError("minimum_observations must be at least 2")

    rows: list[dict[str, float | int | str]] = []
    for symbol, frame in sorted(frames.items()):
        try:
            if not isinstance(frame, pd.DataFrame):
                raise ValueError("invalid price frame: expected a pandas DataFrame")
            if frame.empty:
                raise ValueError("empty price frame")
            signals = generate_pipeline_signals(frame, benchmark)
            prices = pd.to_numeric(frame["Close"], errors="coerce").reindex(signals.index)
            valid = pd.concat([prices.rename("price"), signals.rename("signal")], axis=1).dropna()
            valid = valid[valid["price"] > 0]
            if len(valid) < minimum_observations:
                raise ValueError(
                    f"insufficient observations: {len(valid)} < {minimum_observations}"
                )
            folds = walk_forward_evaluate(
                valid["price"],
                valid["signal"],
                initial_capital=initial_capital,
                cost_bps=cost_bps,
                cost_model=cost_model,
                min_train_size=min_train_size,
                n_splits=n_splits,
            )
            for record in folds.to_dict(orient="records"):
                rows.append({"symbol": symbol, "status": "ok", **record})
        except (KeyError, TypeError, ValueError) as exc:
            rows.append(
                {
                    "symbol": symbol,
                    "status": "skipped",
                    "reason": str(exc),
                }
            )
    return pd.DataFrame(rows)
