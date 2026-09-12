from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: float
    average_cost: float
    current_price: float
    sector: str
    industry: str
    expected_return: float  # e.g. 0.15 for 15%
    expected_risk: float  # volatility e.g. 0.20
    intrinsic_value: float
    committee_signal: str  # "BUY", "HOLD", "SELL"

    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        return (self.current_price - self.average_cost) * self.quantity


@dataclass(frozen=True)
class Portfolio:
    portfolio_id: str
    owner: str
    base_currency: str = "INR"
    benchmark: str = "NIFTY50"
    cash: float = 0.0
    positions: list[Position] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def total_positions_value(self) -> float:
        return sum(p.market_value for p in self.positions)

    @property
    def total_portfolio_value(self) -> float:
        return self.cash + self.total_positions_value


@dataclass(frozen=True)
class PortfolioDecision:
    portfolio_id: str
    recommended_actions: list[dict[str, Any]]
    target_weights: dict[str, float]
    expected_return: float
    expected_risk: float
    portfolio_score: float
    confidence: float
    major_risks: list[str]
    rebalance_summary: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
