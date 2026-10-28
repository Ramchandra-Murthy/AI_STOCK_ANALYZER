"""Leakage-aware experimental MLP benchmark for daily return series.

This is a research-only baseline. It is not a trading recommendation and does not
submit broker orders. Feature rows use information available through session t to
predict the return at session t+1.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler


def evaluate_mlp_return_strategy(
    returns: pd.Series,
    *,
    cost_bps: float = 10.0,
    train_fraction: float = 0.6,
    validation_fraction: float = 0.2,
    random_state: int = 42,
) -> dict[str, float | int | str]:
    """Fit a small MLP on past daily returns and evaluate on a final holdout.

    Five lagged daily returns are used as features. The model is fitted only on the
    chronological training partition; validation data is reported separately and
    is not used for fitting or hyperparameter selection. The final test partition
    is untouched until predictions are generated.

    Strategy exposure is long when predicted next-session return is positive and
    cash otherwise. Transaction costs are charged on position changes, including
    the initial entry. The buy-and-hold reference uses the same test target dates.
    """
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be between 0 and 1")
    if not 0.0 < validation_fraction < 1.0:
        raise ValueError("validation_fraction must be between 0 and 1")
    if train_fraction + validation_fraction >= 1.0:
        raise ValueError("train_fraction + validation_fraction must be less than 1")
    if not np.isfinite(cost_bps) or cost_bps < 0:
        raise ValueError("cost_bps must be a finite non-negative number")
    if not returns.index.is_unique:
        raise ValueError("returns contains duplicate timestamps")

    clean = pd.to_numeric(returns, errors="coerce").replace([np.inf, -np.inf], np.nan)
    clean = clean.sort_index().dropna()
    if len(clean) < 40:
        raise ValueError("at least 40 valid daily returns are required")

    features = pd.DataFrame(
        {f"return_lag_{lag}": clean.shift(lag) for lag in range(5)},
        index=clean.index,
    )
    target = clean.shift(-1).rename("next_return")
    dataset = pd.concat([features, target], axis=1).dropna()
    if len(dataset) < 35:
        raise ValueError("not enough observations after creating lagged features")

    feature_columns = list(features.columns)
    n_rows = len(dataset)
    train_end = int(n_rows * train_fraction)
    validation_end = int(n_rows * (train_fraction + validation_fraction))
    if train_end < 10 or validation_end <= train_end or n_rows - validation_end < 5:
        raise ValueError("chronological splits must leave enough train, validation, and test rows")

    x_train = dataset.iloc[:train_end][feature_columns]
    y_train = dataset.iloc[:train_end]["next_return"]
    x_validation = dataset.iloc[train_end:validation_end][feature_columns]
    y_validation = dataset.iloc[train_end:validation_end]["next_return"]
    x_test = dataset.iloc[validation_end:][feature_columns]
    y_test = dataset.iloc[validation_end:]["next_return"]

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_validation_scaled = scaler.transform(x_validation)
    x_test_scaled = scaler.transform(x_test)

    model = MLPRegressor(
        hidden_layer_sizes=(16, 8),
        activation="relu",
        solver="adam",
        alpha=0.001,
        max_iter=500,
        early_stopping=False,
        random_state=random_state,
    )
    model.fit(x_train_scaled, y_train.to_numpy())
    validation_predictions = model.predict(x_validation_scaled)
    test_predictions = model.predict(x_test_scaled)

    positions = (test_predictions > 0.0).astype(float)
    turnover = np.abs(np.diff(np.r_[0.0, positions]))
    strategy_returns = positions * y_test.to_numpy() - turnover * (cost_bps / 10_000.0)
    reference_returns = y_test.to_numpy()

    def cumulative_return(values: np.ndarray) -> float:
        return float(np.prod(1.0 + values) - 1.0)

    def sharpe(values: np.ndarray) -> float:
        std = float(np.std(values, ddof=1)) if len(values) > 1 else float("nan")
        if not np.isfinite(std) or std <= 0:
            return float("nan")
        return float(np.mean(values) / std * np.sqrt(252.0))

    def max_drawdown(values: np.ndarray) -> float:
        wealth = np.cumprod(1.0 + values)
        peaks = np.maximum.accumulate(np.r_[1.0, wealth])[1:]
        return float(np.min(wealth / peaks - 1.0)) if len(wealth) else float("nan")

    return {
        "train_observations": len(x_train),
        "validation_observations": len(x_validation),
        "test_observations": len(x_test),
        "train_end": str(x_train.index[-1]),
        "validation_start": str(x_validation.index[0]),
        "validation_end": str(x_validation.index[-1]),
        "test_start": str(x_test.index[0]),
        "test_end": str(x_test.index[-1]),
        "validation_mse": float(mean_squared_error(y_validation, validation_predictions)),
        "test_mse": float(mean_squared_error(y_test, test_predictions)),
        "strategy_cumulative_return": cumulative_return(strategy_returns),
        "buy_hold_cumulative_return": cumulative_return(reference_returns),
        "strategy_sharpe": sharpe(strategy_returns),
        "buy_hold_sharpe": sharpe(reference_returns),
        "strategy_max_drawdown": max_drawdown(strategy_returns),
        "buy_hold_max_drawdown": max_drawdown(reference_returns),
        "test_turnover": float(np.sum(turnover)),
        "cost_bps": float(cost_bps),
    }


def evaluate_mlp_seed_stability(
    returns: pd.Series,
    *,
    cost_bps: float = 10.0,
    random_states: tuple[int, ...] = (7, 21, 42, 84, 123),
) -> dict[str, object]:
    """Evaluate a fixed chronological holdout across seeds without selecting a winner.

    All runs use identical data splits and model settings. The summary describes
    sensitivity to initialization; it is not an estimate of independent market
    regimes and must not be used to select a seed for live trading.
    """
    if not random_states:
        raise ValueError("at least one random state is required")
    if len(set(random_states)) != len(random_states):
        raise ValueError("random_states must be unique")

    rows = []
    for seed in random_states:
        result = evaluate_mlp_return_strategy(
            returns,
            cost_bps=cost_bps,
            random_state=seed,
        )
        rows.append(
            {
                "random_state": seed,
                "test_start": result["test_start"],
                "test_end": result["test_end"],
                "strategy_cumulative_return": result["strategy_cumulative_return"],
                "buy_hold_cumulative_return": result["buy_hold_cumulative_return"],
                "strategy_sharpe": result["strategy_sharpe"],
                "strategy_max_drawdown": result["strategy_max_drawdown"],
                "test_mse": result["test_mse"],
            }
        )

    strategy_returns = np.asarray([row["strategy_cumulative_return"] for row in rows], dtype=float)
    benchmark_returns = np.asarray([row["buy_hold_cumulative_return"] for row in rows], dtype=float)
    return {
        "runs": rows,
        "seed_count": len(rows),
        "outperformance_count": int(np.sum(strategy_returns > benchmark_returns)),
        "median_strategy_return": float(np.median(strategy_returns)),
        "minimum_strategy_return": float(np.min(strategy_returns)),
        "maximum_strategy_return": float(np.max(strategy_returns)),
        "median_buy_hold_return": float(np.median(benchmark_returns)),
    }
