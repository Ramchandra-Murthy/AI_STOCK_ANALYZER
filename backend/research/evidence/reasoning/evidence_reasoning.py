from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple
from backend.research.evidence.models.research_evidence import ResearchEvidence
from backend.research.evidence.quality.evidence_quality import EvidenceQualityService

logger = logging.getLogger(__name__)

class EvidenceRelationship:
    """
    Represents an analytical relationship between two evidence items:
    SUPPORTS, CONTRADICTS, CORROBORATES, or SUPERSEDES.
    """
    def __init__(
        self,
        source_evidence_id: str,
        target_evidence_id: str,
        relation_type: str,
        strength: float,
        rationale: str
    ) -> None:
        self.source_evidence_id = source_evidence_id
        self.target_evidence_id = target_evidence_id
        self.relation_type = relation_type.upper()
        self.strength = strength
        self.rationale = rationale

        allowed = {"SUPPORTS", "CONTRADICTS", "CORROBORATES", "SUPERSEDES"}
        if self.relation_type not in allowed:
            raise ValueError(f"Invalid relation type: {self.relation_type}")


class EvidenceReasoningEngine:
    """
    Analyzes a collection of ResearchEvidence items within a ResearchCase
    to surface corroborations, contradictions, and net analytical posture.
    """

    @staticmethod
    def analyze_relationships(evidence_items: List[ResearchEvidence]) -> List[EvidenceRelationship]:
        relationships: List[EvidenceRelationship] = []
        
        for i, item_a in enumerate(evidence_items):
            for j, item_b in enumerate(evidence_items):
                if i >= j:
                    continue  # Avoid self-comparison and duplicate pairs

                # Check for Contradiction (Same category or related metrics with opposite polarity)
                if item_a.category == item_b.category and item_a.polarity != "NEUTRAL" and item_b.polarity != "NEUTRAL":
                    if item_a.polarity != item_b.polarity:
                        # Contradiction detected
                        qa_a = EvidenceQualityService.assess_evidence(item_a)
                        qa_b = EvidenceQualityService.assess_evidence(item_b)
                        strength = round((qa_a.quality_score + qa_b.quality_score) / 2.0, 4)
                        
                        rel = EvidenceRelationship(
                            source_evidence_id=item_a.evidence_id,
                            target_evidence_id=item_b.evidence_id,
                            relation_type="CONTRADICTS",
                            strength=strength,
                            rationale=f"Conflicting polarities detected in category {item_a.category}: '{item_a.statement}' vs '{item_b.statement}'"
                        )
                        relationships.append(rel)

                # Check for Corroboration (Same category, same polarity, different sources)
                elif item_a.category == item_b.category and item_a.polarity == item_b.polarity and item_a.polarity != "NEUTRAL":
                    if item_a.source != item_b.source:
                        qa_a = EvidenceQualityService.assess_evidence(item_a)
                        qa_b = EvidenceQualityService.assess_evidence(item_b)
                        strength = round((qa_a.quality_score + qa_b.quality_score) / 2.0, 4)

                        rel = EvidenceRelationship(
                            source_evidence_id=item_a.evidence_id,
                            target_evidence_id=item_b.evidence_id,
                            relation_type="CORROBORATES",
                            strength=strength,
                            rationale=f"Independent sources ({item_a.source} and {item_b.source}) corroborate finding in {item_a.category}"
                        )
                        relationships.append(rel)

                # Check for Supersession (Same category, one is much older/lower recency than the other)
                elif item_a.category == item_b.category and abs(item_a.recency - item_b.recency) > 0.3:
                    older = item_a if item_a.recency < item_b.recency else item_b
                    newer = item_b if item_a.recency < item_b.recency else item_a
                    
                    rel = EvidenceRelationship(
                        source_evidence_id=newer.evidence_id,
                        target_evidence_id=older.evidence_id,
                        relation_type="SUPERSEDES",
                        strength=round(newer.recency, 4),
                        rationale=f"Recent observation in {newer.category} supersedes legacy finding."
                    )
                    relationships.append(rel)

        return relationships

    @staticmethod
    def evaluate_net_stance(evidence_items: List[ResearchEvidence], relationships: List[EvidenceRelationship]) -> Dict[str, Any]:
        """
        Synthesizes net analytical stance, accounting for contradictions and quality weights.
        """
        if not evidence_items:
            return {"posture": "NEUTRAL", "confidence_score": 0.0, "contradiction_count": 0}

        contradictions = [r for r in relationships if r.relation_type == "CONTRADICTS"]
        corroborations = [r for r in relationships if r.relation_type == "CORROBORATES"]

        pos_score = sum(1.0 for item in evidence_items if item.polarity == "POSITIVE")
        neg_score = sum(1.0 for item in evidence_items if item.polarity == "NEGATIVE")

        # Penalize for unaddressed contradictions
        net_balance = pos_score - neg_score
        if len(contradictions) > 0:
            net_balance *= (1.0 - (0.1 * len(contradictions)))

        if net_balance > 0.5:
            posture = "CONSTRUCTIVE"
        elif net_balance < -0.5:
            posture = "CAUTIOUS"
        else:
            posture = "BALANCED"

        return {
            "posture": posture,
            "net_balance": round(net_balance, 2),
            "contradiction_count": len(contradictions),
            "corroboration_count": len(corroborations),
            "total_evidence": len(evidence_items)
        }