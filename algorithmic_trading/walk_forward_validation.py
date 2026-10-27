"""Sequential out-of-sample evaluation for precomputed point-in-time signals."""

from __future__ import annotations

import pandas as pd

from algorithmic_trading.backtester import run_backtest
from algorithmic_trading.trading_costs import IndiaEquityCostModel


def align_return_series(
    strategy_returns: pd.Series, benchmark_returns: pd.Series
) -> tuple[pd.Series, pd.Series]:
    """Return numeric strategy and benchmark returns on shared, valid timestamps only."""
    if not strategy_returns.index.is_unique:
        raise ValueError("strategy_returns contains duplicate timestamps")
    if not benchmark_returns.index.is_unique:
        raise ValueError("benchmark_returns contains duplicate timestamps")

    aligned = pd.concat(
        [
            pd.to_numeric(strategy_returns, errors="coerce").rename("strategy"),
            pd.to_numeric(benchmark_returns, errors="coerce").rename("benchmark"),
        ],
        axis=1,
        join="inner",
    )
    aligned = aligned.replace([float("inf"), float("-inf")], float("nan")).dropna().sort_index()
    return aligned["strategy"], aligned["benchmark"]


def _max_drawdown(returns: pd.Series) -> float:
    if returns.empty:
        return float("nan")
    wealth = (1.0 + returns).cumprod()
    return float((wealth / wealth.cummax() - 1.0).min())


def _downside_deviation(returns: pd.Series) -> float:
    if returns.empty:
        return float("nan")
    downside = returns.clip(upper=0.0).to_numpy(dtype=float)
    return float(pd.Series(downside).pow(2).mean() ** 0.5 * (252.0**0.5))


def benchmark_relative_metrics(
    strategy_returns: pd.Series, benchmark_returns: pd.Series
) -> dict[str, float | int]:
    """Calculate annualized risk and compounded excess return on shared dates.

    Undefined ratios and metrics with no observations are represented as NaN.
    Returns are daily simple returns; annualization assumes 252 sessions.
    """
    strategy, benchmark = align_return_series(strategy_returns, benchmark_returns)
    active = strategy - benchmark
    active_std = float(active.std(ddof=1)) if len(active) > 1 else float("nan")
    tracking_error = active_std * (252.0**0.5) if pd.notna(active_std) else float("nan")
    information_ratio = (
        float(active.mean() / active_std * (252.0**0.5))
        if pd.notna(active_std) and active_std > 0
        else float("nan")
    )
    strategy_wealth = (1.0 + strategy).cumprod()
    benchmark_wealth = (1.0 + benchmark).cumprod()
    cumulative_excess = (
        float(strategy_wealth.iloc[-1] - benchmark_wealth.iloc[-1])
        if not strategy.empty
        else float("nan")
    )
    return {
        "observations": len(strategy),
        "tracking_error": tracking_error,
        "information_ratio": information_ratio,
        "strategy_downside_deviation": _downside_deviation(strategy),
        "benchmark_downside_deviation": _downside_deviation(benchmark),
        "strategy_max_drawdown": _max_drawdown(strategy),
        "benchmark_max_drawdown": _max_drawdown(benchmark),
        "cumulative_excess_return": cumulative_excess,
    }


def walk_forward_evaluate(
    prices: pd.Series,
    signals: pd.Series,
    *,
    initial_capital: float = 100_000.0,
    cost_bps: float = 10.0,
    cost_model: IndiaEquityCostModel | None = None,
    min_train_size: int = 252,
    n_splits: int = 5,
) -> pd.DataFrame:
    """Evaluate signals on sequential test windows after a warm-up history.

    Signals must already be generated point-in-time (no future data used to
    create a signal). Each fold is evaluated independently; the initial test
    bar starts flat because the backtester shifts signals by one bar. This
    function does not fit or tune model parameters.
    """
    if min_train_size < 2:
        raise ValueError("min_train_size must be at least 2")
    if n_splits < 1:
        raise ValueError("n_splits must be at least 1")
    if not prices.index.is_unique:
        raise ValueError("prices contains duplicate timestamps")
    if not signals.index.is_unique:
        raise ValueError("signals contains duplicate timestamps")

    if not prices.index.is_monotonic_increasing:
        prices = prices.sort_index()
    if not signals.index.is_monotonic_increasing:
        signals = signals.sort_index()

    aligned = pd.concat(
        [
            pd.to_numeric(prices, errors="coerce").rename("price"),
            pd.to_numeric(signals, errors="coerce").rename("signal"),
        ],
        axis=1,
    ).dropna()
    aligned = aligned[aligned["price"] > 0]

    if len(aligned) <= min_train_size:
        raise ValueError("not enough observations after min_train_size")

    available = len(aligned) - min_train_size
    if available < n_splits * 2:
        raise ValueError("each test fold must contain at least two observations")

    fold_size = available // n_splits
    rows: list[dict[str, float | int | str]] = []
    for fold in range(n_splits):
        start = min_train_size + fold * fold_size
        stop = len(aligned) if fold == n_splits - 1 else start + fold_size
        test = aligned.iloc[start:stop]
        _, metrics = run_backtest(
            prices=test["price"],
            signals=test["signal"],
            initial_capital=initial_capital,
            cost_bps=cost_bps,
            cost_model=cost_model,
        )
        rows.append(
            {
                "fold": fold + 1,
                "test_start": str(test.index[0]),
                "test_end": str(test.index[-1]),
                "observations": len(test),
                "total_return": metrics.total_return,
                "cagr": metrics.cagr if metrics.cagr is not None else float("nan"),
                "max_drawdown": metrics.max_drawdown,
                "buy_hold_return": metrics.buy_hold_return,
                "trade_count": metrics.trade_count,
                "win_rate": metrics.win_rate,
                "profit_factor": (
                    metrics.profit_factor if metrics.profit_factor is not None else float("nan")
                ),
                "annualized_volatility": metrics.volatility,
                "sharpe_ratio": (
                    metrics.sharpe_ratio if metrics.sharpe_ratio is not None else float("nan")
                ),
                "sortino_ratio": (
                    metrics.sortino_ratio if metrics.sortino_ratio is not None else float("nan")
                ),
                "calmar_ratio": (
                    metrics.calmar_ratio if metrics.calmar_ratio is not None else float("nan")
                ),
            }
        )
    return pd.DataFrame(rows)
