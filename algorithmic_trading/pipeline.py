"""End-to-end NSE/BSE algorithmic research pipeline."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from algorithmic_trading.edge_engine import EdgeMetrics, calculate_edge
from algorithmic_trading.position_sizing import PositionSize, fixed_risk_size
from algorithmic_trading.regime_engine import classify_regime, regime_score
from algorithmic_trading.relative_strength import relative_return
from algorithmic_trading.signal_engine import SignalDecision, compose_signal


@dataclass(frozen=True)
class AlgorithmicAnalysis:
    """Complete research output for one symbol."""

    symbol: str
    regime: str
    regime_score: int
    relative_return_pct: float | None
    edge: EdgeMetrics | None
    signal: SignalDecision
    position_size: PositionSize


def analyze_symbol(
    symbol: str,
    frame: pd.DataFrame,
    benchmark: pd.Series | None,
    capital: float,
    risk_fraction: float = 0.01,
    stop_price: float | None = None,
    historical_trade_returns: pd.Series | None = None,
    min_expectancy: float = 0.0,
    relative_periods: int = 20,
) -> AlgorithmicAnalysis:
    """Run the existing algorithmic components as one transparent pipeline.

    Market data is supplied by the caller so this layer remains independent
    of any broker or data vendor.
    """
    if not symbol.strip():
        raise ValueError("symbol must not be empty")
    if frame.empty or "Close" not in frame:
        raise ValueError("frame must contain Close data")

    current_price = float(pd.to_numeric(frame["Close"], errors="coerce").iloc[-1])
    if current_price <= 0:
        raise ValueError("latest close must be greater than zero")

    score = regime_score(frame)
    regime = classify_regime(frame)

    rs_return = None
    if benchmark is not None:
        rs_return = relative_return(
            pd.to_numeric(frame["Close"], errors="coerce"),
            pd.to_numeric(benchmark, errors="coerce"),
            periods=relative_periods,
        )

    edge = None
    if historical_trade_returns is not None:
        edge = calculate_edge(historical_trade_returns)

    signal = compose_signal(
        regime=regime,
        regime_score=score,
        relative_return_pct=rs_return,
        edge=edge,
        min_expectancy=min_expectancy,
    )

    effective_stop = stop_price
    if effective_stop is None:
        effective_stop = current_price

    position_size = fixed_risk_size(
        capital=capital,
        risk_fraction=risk_fraction,
        entry_price=current_price,
        stop_price=effective_stop,
    )

    return AlgorithmicAnalysis(
        symbol=symbol,
        regime=regime,
        regime_score=score,
        relative_return_pct=rs_return,
        edge=edge,
        signal=signal,
        position_size=position_size,
    )
