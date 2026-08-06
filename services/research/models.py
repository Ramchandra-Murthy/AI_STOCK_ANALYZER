from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True, slots=True)
class InvestmentThesis:
    """Core investment thesis summarizing structural tailwinds and competitive edge."""
    summary: str
    drivers: List[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class RiskSummary:
    """Key operational, financial, and regulatory risks."""
    primary_risk: str
    mitigants: List[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ResearchResult:
    """Structured research output synthesizing valuation and qualitative factors."""
    symbol: str
    thesis: InvestmentThesis
    risks: RiskSummary
    economic_moat: str
    ai_recommendation: str
    confidence_score: float
