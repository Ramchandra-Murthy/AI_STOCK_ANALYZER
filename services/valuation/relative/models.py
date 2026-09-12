from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class RelativeValuationResult:
    """Multi-metric relative valuation comparison result against peers and industry."""

    symbol: str
    pe_ratio: float
    ev_ebitda: float
    ev_sales: float
    pb_ratio: float
    peg_ratio: float
    implied_value_pe: float
    implied_value_ev_ebitda: float
    blend_relative_value: float
    comparison_benchmarks: dict[str, Any] = field(default_factory=dict)
