from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class EvidenceObject:
    metric_name: str
    value: float | str
    direction: str
    importance: str
    confidence: float
    source: str
    period: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(frozen=True, slots=True)
class Hypothesis:
    title: str
    statement: str
    supporting_evidence: list[str]
    confidence: float


@dataclass(frozen=True, slots=True)
class Contradiction:
    title: str
    description: str
    conflicting_signals: list[str]
    severity: str


@dataclass(frozen=True, slots=True)
class ReasoningResult:
    symbol: str
    department: str
    summary: str
    evidence_list: list[EvidenceObject]
    hypotheses: list[Hypothesis]
    contradictions: list[Contradiction]
    confidence: float
    recommendation: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
