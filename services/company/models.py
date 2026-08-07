from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class CompanyIdentity:
    symbol: str
    name: str
    sector: str
    industry: str
    country: str = "India"
    currency: str = "INR"
    exchange: str = "NSE"
    listing_date: str = "1995-01-01"
    business_description: str = ""
    market_cap: float = 0.0
    shares_outstanding: float = 0.0
    employees: int = 0
    website: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass(frozen=True)
class PeriodSnapshot:
    period: str # e.g. "FY2024", "Q1-2025"
    statement_type: str # "income", "balance", "cashflow"
    metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass(frozen=True)
class CompanyRecord:
    identity: CompanyIdentity
    history: List[PeriodSnapshot] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
