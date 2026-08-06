from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


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
    """Comprehensive portfolio analytics result including risk, return, and allocation."""
    total_portfolio_value: float
    positions: List[PositionResult] = field(default_factory=list)
    sector_allocation: Dict[str, float] = field(default_factory=dict)
    portfolio_beta: float = 1.0
    sharpe_ratio: float = 0.0
    value_at_risk_95: float = 0.0
    monte_carlo_median_end_value: float = 0.0
    assumptions: Dict[str, Any] = field(default_factory=dict)
