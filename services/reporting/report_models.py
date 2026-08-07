from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class InstitutionalResearchReport:
    symbol: str
    recommendation: str # "BUY", "HOLD", "SELL"
    executive_summary: str
    valuation_section: str
    quality_section: str
    risk_section: str
    forecast_section: str
    portfolio_section: str
    appendix: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
