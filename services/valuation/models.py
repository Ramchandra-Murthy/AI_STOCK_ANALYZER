from __future__ import annotations

"""
==========================================================
VALUATION DATA MODELS & CONTRACTS
Module  : models
Version : V1.0
==========================================================

Defines core data structures, enums, and calculation contracts
used across engines, dispatchers, and aggregators.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ValuationMethod(Enum):
    DCF = "DCF"
    NAV = "NAV"
    COMPARABLE = "COMPARABLE"
    MARKET = "MARKET"
    BOOK = "BOOK"


class ValuationStatus(Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    FAILED = "FAILED"


@dataclass(slots=True)
class ValuationResult:
    """
    Standardized result contract returned by all valuation engines.
    """

    entity_name: str
    valuation_method: ValuationMethod
    valuation_status: ValuationStatus
    enterprise_value: float
    equity_value: float
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    raw_result: Any = None


@dataclass(slots=True)
class SOTPResult:
    """
    Aggregate valuation result output by SOTPEngine.
    """

    enterprise_value: float
    equity_value: float
    implied_share_price: float
    net_debt: float
    holdco_discount_pct: float
    holdco_discount_amount: float
    component_results: List[ValuationResult] = field(default_factory=list)
