from __future__ import annotations

import logging
from typing import Any, Dict, List
from backend.research.evidence.models.research_evidence import ResearchEvidence
from backend.research.models.research_case import ResearchCase

logger = logging.getLogger(__name__)

class EvidenceService:
    """
    Manages structured evidence attached to institutional
    research cases.
    """

    @staticmethod
    def create_evidence(
        case: ResearchCase,
        category: str,
        statement: str,
        *,
        value: Any = None,
        source: str = "EROS",
        source_type: str = "INTERNAL",
        confidence: float = 1.0,
        materiality: float = 0.5,
        recency: float = 1.0,
        polarity: str = "NEUTRAL",
        metadata: Dict[str, Any] | None = None,
    ) -> ResearchEvidence:
        if not category:
            raise ValueError("category is required")
        if not statement:
            raise ValueError("statement is required")
            
        evidence_id = f"{case.case_id}-E{len(case.evidence) + 1:04d}"
        
        # Ensure category is strictly uppercase
        normalized_category = str(category).strip().upper()
        
        evidence = ResearchEvidence(
            evidence_id=evidence_id,
            case_id=case.case_id,
            symbol=case.symbol,
            category=normalized_category,
            statement=statement,
            value=value,
            source=source,
            source_type=source_type,
            confidence=confidence,
            materiality=materiality,
            recency=recency,
            polarity=polarity.upper(),
            metadata=metadata or {},
        )
        return evidence

    @staticmethod
    def attach_evidence(
        case: ResearchCase,
        evidence: ResearchEvidence,
    ) -> ResearchCase:
        if evidence.case_id != case.case_id:
            raise ValueError(
                "evidence does not belong to this research case"
            )
        evidence_summary = evidence.statement
        if evidence_summary not in case.evidence:
            case.evidence.append(evidence_summary)
        case.updated_at = (
            __import__("datetime")
            .datetime.utcnow()
            .isoformat()
        )
        return case

    @staticmethod
    def calculate_evidence_strength(
        evidence: ResearchEvidence,
    ) -> float:
        strength = (
            evidence.confidence
            * evidence.materiality
            * evidence.recency
        )
        return round(strength, 4)

    @staticmethod
    def summarize(
        evidence_items: List[ResearchEvidence],
    ) -> Dict[str, Any]:
        if not evidence_items:
            return {
                "count": 0,
                "average_strength": 0.0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
            }
        strengths = [
            EvidenceService.calculate_evidence_strength(item)
            for item in evidence_items
        ]
        return {
            "count": len(evidence_items),
            "average_strength": round(
                sum(strengths) / len(strengths),
                4,
            ),
            "positive": sum(
                item.polarity == "POSITIVE"
                for item in evidence_items
            ),
            "negative": sum(
                item.polarity == "NEGATIVE"
                for item in evidence_items
            ),
            "neutral": sum(
                item.polarity == "NEUTRAL"
                for item in evidence_items
            ),
        }