from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ValuationResultDTO:
    record_id: str
    symbol: str
    intrinsic_value: float
    current_price: float
    margin_of_safety: float
    recommendation: str
    valuation_model: str
    created_at: datetime
