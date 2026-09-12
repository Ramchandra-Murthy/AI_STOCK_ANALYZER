from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class SegmentValuation:
    """Valuation details for an individual business segment of a conglomerate."""

    segment_name: str
    revenue: float
    ebitda: float
    multiple: float
    enterprise_value: float


@dataclass(frozen=True, slots=True)
class SOTPResult:
    """Sum-of-the-Parts (SOTP) valuation result for conglomerates (e.g., Reliance)."""

    symbol: str
    segments: list[SegmentValuation] = field(default_factory=list)
    sum_of_segments_ev: float = 0.0
    net_debt: float = 0.0
    holding_company_discount_pct: float = 0.15
    conglomerate_equity_value: float = 0.0
    fair_value_per_share: float = 0.0
    assumptions: dict[str, Any] = field(default_factory=dict)
