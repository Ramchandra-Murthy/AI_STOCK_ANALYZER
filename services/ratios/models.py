from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class RatioCategoryResult:
    category_name: str
    symbol: str
    period: str
    metrics: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FinancialRatios:
    period: str
    symbol: str = "UNKNOWN"
    roe: float = 0.0
    roa: float = 0.0
    roic: float = 0.0
    gross_margin: float = 0.0
    operating_margin: float = 0.0
    net_margin: float = 0.0
    current_ratio: float = 0.0
    quick_ratio: float = 0.0
    debt_to_equity: float = 0.0
    interest_coverage: float = 0.0
    asset_turnover: float = 0.0
    profitability: dict[str, float] = field(default_factory=dict)
    liquidity: dict[str, float] = field(default_factory=dict)
    solvency: dict[str, float] = field(default_factory=dict)
    efficiency: dict[str, float] = field(default_factory=dict)
    growth: dict[str, float] = field(default_factory=dict)
    cash_flow: dict[str, float] = field(default_factory=dict)
    quality_scores: dict[str, float] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
