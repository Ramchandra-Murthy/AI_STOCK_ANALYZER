"""Reusable, validated trading-profile configuration.

Profiles contain user preferences and limits; they do not encode a specific
account size, risk amount, exchange, or holding period.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TradingStyle = Literal["intraday", "swing", "positional", "long_term"]
RiskMode = Literal["percent", "fixed"]
StopMode = Literal["fixed", "percentage", "atr", "technical"]
Exchange = Literal["NSE", "BSE", "BOTH"]


@dataclass(frozen=True)
class TradingProfile:
    """A portable set of trading preferences and portfolio risk limits."""

    name: str = "default"
    style: TradingStyle = "intraday"
    exchange: Exchange = "BOTH"
    timeframe: str = "5m"
    capital: float = 100_000.0
    risk_mode: RiskMode = "percent"
    risk_value: float = 1.0
    max_daily_loss_pct: float = 3.0
    max_positions: int = 5
    max_position_pct: float = 20.0
    max_exposure_pct: float = 80.0
    cash_reserve_pct: float = 10.0
    stop_mode: StopMode = "atr"
    stop_value: float = 1.5
    allow_short: bool = False
    estimated_round_trip_cost_pct: float = 0.25

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("profile name must not be empty")
        if self.capital <= 0:
            raise ValueError("capital must be positive")
        if self.risk_value <= 0:
            raise ValueError("risk_value must be positive")
        if self.risk_mode == "percent" and self.risk_value > 100:
            raise ValueError("percentage risk_value cannot exceed 100")
        if not 0 < self.max_daily_loss_pct <= 100:
            raise ValueError("max_daily_loss_pct must be in (0, 100]")
        if self.max_positions < 1:
            raise ValueError("max_positions must be at least 1")
        if not 0 < self.max_position_pct <= 100:
            raise ValueError("max_position_pct must be in (0, 100]")
        if not 0 < self.max_exposure_pct <= 100:
            raise ValueError("max_exposure_pct must be in (0, 100]")
        if self.max_position_pct > self.max_exposure_pct:
            raise ValueError("max_position_pct cannot exceed max_exposure_pct")
        if not 0 <= self.cash_reserve_pct < 100:
            raise ValueError("cash_reserve_pct must be in [0, 100)")
        if self.stop_value <= 0:
            raise ValueError("stop_value must be positive")
        if self.estimated_round_trip_cost_pct < 0:
            raise ValueError("estimated_round_trip_cost_pct cannot be negative")
        if not self.timeframe.strip():
            raise ValueError("timeframe must not be empty")

    @property
    def risk_budget(self) -> float:
        """Return the per-trade risk budget in account currency."""
        if self.risk_mode == "fixed":
            return self.risk_value
        return self.capital * self.risk_value / 100.0

    @property
    def daily_loss_limit(self) -> float:
        """Return the configured daily loss limit in account currency."""
        return self.capital * self.max_daily_loss_pct / 100.0
