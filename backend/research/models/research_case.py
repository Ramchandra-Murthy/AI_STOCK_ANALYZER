from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

@dataclass
class ResearchCase:
    """
    Institutional research case representing a structured
    investigation of an investment opportunity.
    """
    case_id: str
    symbol: str
    research_type: str = "Long-Term Equity"
    objective: str = ""
    status: str = "OPEN"
    analyst: str = "EROS"
    evidence: List[str] = field(default_factory=list)
    investment_thesis: str = ""
    conclusion: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )