from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ValuationMethod(str, Enum):
    DCF = "DCF"
    NAV = "NAV"
    SOTP = "SOTP"


class ValuationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PENDING = "PENDING"


@dataclass
class ValuationResult:
    method: ValuationMethod
    enterprise_value: float = 0.0
    equity_value: float = 0.0
    implied_share_price: float = 0.0
    status: ValuationStatus = ValuationStatus.SUCCESS
    details: dict[str, Any] = field(default_factory=dict)
