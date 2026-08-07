from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class EvidenceObject:
    metric_name: str
    value: float | str
    direction: str # "IMPROVING", "STABLE", "DETERIORATING", "ACCELERATING"
    importance: str # "HIGH", "MEDIUM", "LOW"
    confidence: float
    source: str
    period: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass(frozen=True)
class Hypothesis:
    title: str
    statement: str
    supporting_evidence: List[str]
    confidence: float

@dataclass(frozen=True)
class Contradiction:
    title: str
    description: str
    conflicting_signals: List[str]
    severity: str # "HIGH", "MEDIUM", "LOW"

@dataclass(frozen=True)
class ReasoningResult:
    symbol: str
    department: str
    summary: str
    evidence_list: List[EvidenceObject]
    hypotheses: List[Hypothesis]
    contradictions: List[Contradiction]
    confidence: float
    recommendation: str # "BUY", "HOLD", "SELL"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
