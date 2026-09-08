from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True, slots=True)
class DCFValuation:
    """Discounted Cash Flow (DCF) valuation model output."""
    implied_value: float
    wacc: float
    terminal_growth_rate: float
    pv_cash_flows: float
    pv_terminal_value: float


@dataclass(frozen=True, slots=True)
class RelativeValuation:
    """Peer comparison and relative valuation (P/E, EV/EBITDA)."""
    pe_implied_value: float
    ev_ebitda_implied_value: float
    sector_pe_benchmark: float


@dataclass(frozen=True, slots=True)
class ValuationResult:
    """Comprehensive institutional valuation summary."""
    symbol: str
    dcf: DCFValuation
    relative: RelativeValuation
    nav_value: float
    blended_fair_value: float
    current_market_price: float
    margin_of_safety_pct: float
    recommendation: str
