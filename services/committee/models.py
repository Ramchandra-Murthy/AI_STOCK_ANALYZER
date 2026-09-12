from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class AnalystOpinion:
    department: str
    signal: str  # "BUY", "HOLD", "SELL"
    confidence: float  # 0.0 to 1.0
    score: float  # 0.0 to 100.0
    strengths: list[str]
    concerns: list[str]
    evidence: list[str]
    explanation: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass(frozen=True)
class CommitteeDecision:
    symbol: str
    consensus_signal: str  # "BUY", "HOLD", "SELL"
    overall_confidence: float
    weighted_score: float
    analyst_opinions: list[AnalystOpinion]
    supporting_evidence: list[str]
    major_risks: list[str]
    cio_narrative: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
