"""End-to-end NSE/BSE algorithmic research pipeline."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from algorithmic_trading.edge_engine import EdgeMetrics, calculate_edge
from algorithmic_trading.position_sizing import PositionSize, fixed_risk_size
from algorithmic_trading.regime_engine import classify_regime, regime_score
from algorithmic_trading.relative_strength import relative_return
from algorithmic_trading.risk_engine import PositionPlan, calculate_position_plan
from algorithmic_trading.signal_engine import SignalDecision, compose_signal
from algorithmic_trading.trading_profile import TradingProfile


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
    risk_plan: PositionPlan | None = None


def _average_true_range(frame: pd.DataFrame) -> float | None:
    """Return the latest 14-bar simple-average true range, when available."""
    required = {"High", "Low", "Close"}
    if not required.issubset(frame.columns):
        return None
    high = pd.to_numeric(frame["High"], errors="coerce")
    low = pd.to_numeric(frame["Low"], errors="coerce")
    close = pd.to_numeric(frame["Close"], errors="coerce")
    true_range = pd.concat(
        [
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = true_range.rolling(window=14, min_periods=14).mean().iloc[-1]
    if pd.isna(atr) or float(atr) <= 0:
        return None
    return float(atr)


def _profile_stop_price(
    profile: TradingProfile,
    *,
    entry_price: float,
    side: str,
    frame: pd.DataFrame,
    supplied_stop: float | None,
) -> float:
    """Resolve a profile's stop policy into a concrete stop price."""
    if supplied_stop is not None:
        return float(supplied_stop)

    if profile.stop_mode == "technical":
        raise ValueError("stop_price is required when stop_mode is 'technical'")

    if profile.stop_mode == "fixed":
        distance = float(profile.stop_value)
    elif profile.stop_mode == "percentage":
        distance = entry_price * float(profile.stop_value) / 100.0
    else:
        atr = _average_true_range(frame)
        if atr is None:
            raise ValueError("ATR stop mode requires 14 valid bars with High, Low and Close")
        distance = atr * float(profile.stop_value)

    return entry_price - distance if side == "LONG" else entry_price + distance


def analyze_symbol(
    symbol: str,
    frame: pd.DataFrame,
    benchmark: pd.Series | None,
    capital: float | None = None,
    risk_fraction: float = 0.01,
    stop_price: float | None = None,
    historical_trade_returns: pd.Series | None = None,
    min_expectancy: float = 0.0,
    relative_periods: int = 20,
    *,
    profile: TradingProfile | None = None,
    available_cash: float | None = None,
    current_exposure: float = 0.0,
    daily_loss_so_far: float = 0.0,
) -> AlgorithmicAnalysis:
    """Run the research pipeline and optionally apply profile-based risk controls.

    Existing callers retain the legacy fixed-risk sizing path. Supplying a
    TradingProfile activates the reusable risk engine, including cash reserve,
    position/exposure caps, estimated round-trip costs and daily loss limits.
    This function is analytics-only and never places broker orders.
    """
    if not symbol.strip():
        raise ValueError("symbol must not be empty")
    if frame.empty or "Close" not in frame:
        raise ValueError("frame must contain Close data")

    current_price = float(pd.to_numeric(frame["Close"], errors="coerce").iloc[-1])
    if not pd.notna(current_price) or current_price <= 0:
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

    direction = signal.direction
    risk_plan = None
    if profile is not None:
        if direction not in {"LONG", "SHORT"}:
            position_size = PositionSize(0, 0.0, 0.0, "profile_risk")
        else:
            resolved_stop = _profile_stop_price(
                profile,
                entry_price=current_price,
                side=direction,
                frame=frame,
                supplied_stop=stop_price,
            )
            risk_plan = calculate_position_plan(
                profile,
                entry_price=current_price,
                stop_price=resolved_stop,
                side=direction,
                available_cash=available_cash,
                current_exposure=current_exposure,
                daily_loss_so_far=daily_loss_so_far,
            )
            position_size = PositionSize(
                quantity=risk_plan.quantity,
                risk_budget=risk_plan.risk_budget,
                risk_per_share=risk_plan.risk_per_unit,
                method="profile_risk",
            )
    else:
        if capital is None:
            raise ValueError("capital is required when no trading profile is supplied")
        effective_stop = stop_price
        if effective_stop is None and direction in {"LONG", "SHORT"}:
            atr = _average_true_range(frame)
            if atr is not None:
                stop_distance = atr * 1.5
                effective_stop = (
                    current_price - stop_distance
                    if direction == "LONG"
                    else current_price + stop_distance
                )

        position_size = fixed_risk_size(
            capital=capital,
            risk_fraction=risk_fraction,
            entry_price=current_price,
            stop_price=effective_stop if effective_stop is not None else current_price,
        )

    return AlgorithmicAnalysis(
        symbol=symbol,
        regime=regime,
        regime_score=score,
        relative_return_pct=rs_return,
        edge=edge,
        signal=signal,
        position_size=position_size,
        risk_plan=risk_plan,
    )
