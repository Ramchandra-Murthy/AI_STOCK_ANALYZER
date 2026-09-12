from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from backend.research.evidence.models.research_evidence import ResearchEvidence


@dataclass
class EvidenceQualityAssessment:
    """
    Evaluates the institutional quality, authority, reliability,
    and corroboration of a ResearchEvidence item.
    """

    evidence_id: str
    source_reliability: float = 1.0  # 0.0 to 1.0
    source_authority: float = 1.0  # 0.0 to 1.0
    independence: float = 1.0  # 0.0 to 1.0
    corroboration: float = 1.0  # 0.0 to 1.0
    temporal_quality: float = 1.0  # 0.0 to 1.0
    completeness: float = 1.0  # 0.0 to 1.0
    quality_score: float = 1.0  # Computed composite score
    quality_grade: str = "A+"  # A+, A, B, C
    metadata: dict[str, Any] = field(default_factory=dict)
    assessed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def __post_init__(self) -> None:
        for name, val in [
            ("source_reliability", self.source_reliability),
            ("source_authority", self.source_authority),
            ("independence", self.independence),
            ("corroboration", self.corroboration),
            ("temporal_quality", self.temporal_quality),
            ("completeness", self.completeness),
        ]:
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0")


class EvidenceQualityService:
    """
    Computes rigorous quality grades and scores for institutional evidence.
    """

    @staticmethod
    def assess_evidence(evidence: ResearchEvidence) -> EvidenceQualityAssessment:
        # Determine base reliability & authority by source type
        source_type_weights = {
            "PRIMARY": (1.0, 1.0),
            "AUDITED": (1.0, 1.0),
            "SECONDARY": (0.8, 0.7),
            "REGULATORY": (0.95, 0.95),
            "INTERNAL": (0.9, 0.8),
            "ANALYST": (0.7, 0.6),
            "MEDIA": (0.5, 0.4),
            "ANONYMOUS": (0.3, 0.2),
        }

        rel_weight, auth_weight = source_type_weights.get(evidence.source_type.upper(), (0.6, 0.5))

        # Factor in evidence confidence and recency
        independence = 0.9 if evidence.source_type in {"PRIMARY", "REGULATORY", "AUDITED"} else 0.7
        corroboration = evidence.confidence
        temporal_quality = evidence.recency
        completeness = 0.85 if evidence.value is not None else 0.65

        # Composite quality score calculation
        composite_score = round(
            (rel_weight * 0.25)
            + (auth_weight * 0.20)
            + (independence * 0.15)
            + (corroboration * 0.20)
            + (temporal_quality * 0.10)
            + (completeness * 0.10),
            4,
        )

        # Assign Institutional Grade
        if composite_score >= 0.90:
            grade = "A+"
        elif composite_score >= 0.80:
            grade = "A"
        elif composite_score >= 0.65:
            grade = "B"
        else:
            grade = "C"

        return EvidenceQualityAssessment(
            evidence_id=evidence.evidence_id,
            source_reliability=rel_weight,
            source_authority=auth_weight,
            independence=independence,
            corroboration=corroboration,
            temporal_quality=temporal_quality,
            completeness=completeness,
            quality_score=composite_score,
            quality_grade=grade,
            metadata={"source": evidence.source, "source_type": evidence.source_type},
        )
