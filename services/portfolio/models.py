from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class PositionResult:
    """Individual position metrics within a portfolio."""

    symbol: str
    shares: float
    current_price: float
    market_value: float
    weight: float
    unrealized_pnl: float


@dataclass(frozen=True, slots=True)
class PortfolioAnalyticsResult:
    """Portfolio analytics derived from caller-supplied holdings."""

    total_portfolio_value: float
    positions: list[PositionResult] = field(default_factory=list)
    sector_allocation: dict[str, float] = field(default_factory=dict)
    portfolio_beta: float | None = None
    sharpe_ratio: float | None = None
    value_at_risk_95: float | None = None
    monte_carlo_median_end_value: float | None = None
    assumptions: dict[str, Any] = field(default_factory=dict)
