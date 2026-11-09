"""Combinatorially symmetric cross-validation for strategy-selection bias.

This is a supplementary research diagnostic, not a substitute for a final
chronological holdout or live/paper-trading validation.
"""

from __future__ import annotations

import itertools
import math
from numbers import Integral

import numpy as np
import pandas as pd

from ai_trading.risk_metrics import sharpe_ratio


def probability_of_backtest_overfitting(
    strategy_returns: pd.DataFrame,
    *,
    n_blocks: int = 8,
    periods_per_year: float = 252.0,
    risk_free_rate: float = 0.0,
) -> tuple[dict[str, float | int], pd.DataFrame]:
    """Estimate PBO with combinatorially symmetric cross-validation (CSCV).

    Rows must be chronological observations and columns must be candidate
    strategies. The history is divided into contiguous blocks. For each
    combination of half the blocks, the best in-sample Sharpe strategy is
    selected and ranked against all candidates on the complementary blocks.

    The selected strategy's out-of-sample rank is converted to
    omega = rank / (number_of_strategies + 1), where rank 1 is worst.
    PBO is the fraction of splits whose logit(omega) is non-positive,
    indicating that the in-sample winner ranked at or below the OOS median.

    This diagnostic does not correct poor data, overlapping labels, regime
    changes, or repeated research decisions made after inspecting its output.
    Keep a final untouched chronological holdout.
    """
    if not isinstance(strategy_returns, pd.DataFrame):
        raise ValueError("strategy_returns must be a pandas DataFrame")
    if strategy_returns.empty or strategy_returns.shape[1] < 2:
        raise ValueError("at least two strategies and one observation are required")
    if not strategy_returns.columns.is_unique:
        raise ValueError("strategy columns must be unique")
    if not strategy_returns.index.is_unique or not strategy_returns.index.is_monotonic_increasing:
        raise ValueError("observations must have a unique, chronological index")
    if isinstance(n_blocks, bool) or not isinstance(n_blocks, Integral):
        raise ValueError("n_blocks must be an even integer of at least 4")
    if n_blocks < 4 or n_blocks % 2:
        raise ValueError("n_blocks must be an even integer of at least 4")
    if len(strategy_returns) < n_blocks * 2:
        raise ValueError("at least two observations per block are required")

    try:
        annualization = float(periods_per_year)
        annual_risk_free = float(risk_free_rate)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("annualization and risk-free rate must be finite numbers") from exc
    if isinstance(periods_per_year, (bool, np.bool_)) or not math.isfinite(annualization):
        raise ValueError("periods_per_year must be finite and positive")
    if annualization <= 0:
        raise ValueError("periods_per_year must be finite and positive")
    if isinstance(risk_free_rate, (bool, np.bool_)) or not math.isfinite(annual_risk_free):
        raise ValueError("risk_free_rate must be finite and greater than -1")
    if annual_risk_free <= -1:
        raise ValueError("risk_free_rate must be finite and greater than -1")

    numeric = strategy_returns.apply(pd.to_numeric, errors="coerce")
    values = numeric.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("strategy returns must be complete and finite")
    if (values < -1.0).any():
        raise ValueError("simple returns cannot be below -100%")

    blocks = np.array_split(np.arange(len(numeric)), n_blocks)
    strategy_names = [str(column) for column in numeric.columns]
    if any(not name.strip() for name in strategy_names):
        raise ValueError("strategy names must be non-empty")

    split_rows: list[dict[str, float | int | str]] = []
    block_ids = range(n_blocks)
    for split_number, in_sample_blocks in enumerate(
        itertools.combinations(block_ids, n_blocks // 2), start=1
    ):
        in_sample_set = set(in_sample_blocks)
        out_sample_blocks = tuple(block for block in block_ids if block not in in_sample_set)
        in_sample_positions = np.concatenate([blocks[index] for index in in_sample_blocks])
        out_sample_positions = np.concatenate([blocks[index] for index in out_sample_blocks])

        in_sample_scores = [
            sharpe_ratio(
                numeric.iloc[in_sample_positions, column],
                risk_free_rate=annual_risk_free,
                periods_per_year=annualization,
            )
            for column in range(numeric.shape[1])
        ]
        out_sample_scores = [
            sharpe_ratio(
                numeric.iloc[out_sample_positions, column],
                risk_free_rate=annual_risk_free,
                periods_per_year=annualization,
            )
            for column in range(numeric.shape[1])
        ]

        selected_index = int(np.argmax(in_sample_scores))
        oos_ranks = pd.Series(out_sample_scores).rank(method="average", ascending=True)
        selected_rank = float(oos_ranks.iloc[selected_index])
        omega = selected_rank / (numeric.shape[1] + 1.0)
        logit_omega = math.log(omega / (1.0 - omega))

        split_rows.append(
            {
                "split": split_number,
                "selected_strategy": strategy_names[selected_index],
                "in_sample_sharpe": float(in_sample_scores[selected_index]),
                "out_of_sample_sharpe": float(out_sample_scores[selected_index]),
                "out_of_sample_rank": selected_rank,
                "omega": omega,
                "logit_omega": logit_omega,
            }
        )

    splits = pd.DataFrame(split_rows)
    pbo = float((splits["logit_omega"] <= 0.0).mean())
    summary: dict[str, float | int] = {
        "probability_of_backtest_overfitting": pbo,
        "split_count": int(len(splits)),
        "strategy_count": int(numeric.shape[1]),
        "observation_count": int(len(numeric)),
        "median_selected_oos_sharpe": float(splits["out_of_sample_sharpe"].median()),
    }
    return summary, splits
