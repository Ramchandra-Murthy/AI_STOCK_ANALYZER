from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class AnalystOpinion:
    department: str
    signal: str # "BUY", "HOLD", "SELL"
    confidence: float # 0.0 to 1.0
    score: float # 0.0 to 100.0
    strengths: List[str]
    concerns: List[str]
    evidence: List[str]
    explanation: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass(frozen=True)
class CommitteeDecision:
    symbol: str
    consensus_signal: str # "BUY", "HOLD", "SELL"
    overall_confidence: float
    weighted_score: float
    analyst_opinions: List[AnalystOpinion]
    supporting_evidence: List[str]
    major_risks: List[str]
    cio_narrative: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
