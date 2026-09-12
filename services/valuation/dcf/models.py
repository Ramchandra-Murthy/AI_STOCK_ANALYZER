from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class DCFResult:
    """Production-grade Discounted Cash Flow valuation result."""

    symbol: str
    enterprise_value: float
    equity_value: float
    fair_value_per_share: float
    wacc: float
    terminal_value: float
    pv_cash_flows: list[float] = field(default_factory=list)
    pv_terminal_value: float = 0.0
    assumptions: dict[str, Any] = field(default_factory=dict)
