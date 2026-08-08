from __future__ import annotations

import logging
from typing import Any, Dict, List, Set, Tuple
from backend.research.evidence.models.research_evidence import ResearchEvidence
from backend.research.evidence.reasoning.evidence_reasoning import EvidenceRelationship, EvidenceReasoningEngine
from backend.research.evidence.quality.evidence_quality import EvidenceQualityService

logger = logging.getLogger(__name__)

class EvidenceGraphNode:
    """
    Represents an evidence node within the research graph.
    """
    def __init__(self, evidence: ResearchEvidence) -> None:
        self.evidence = evidence
        self.quality = EvidenceQualityService.assess_evidence(evidence)


class EvidenceGraph:
    """
    Directed graph structure modeling evidence nodes and analytical relationship edges.
    """
    def __init__(self, case_id: str, symbol: str) -> None:
        self.case_id = case_id
        self.symbol = symbol
        self.nodes: Dict[str, EvidenceGraphNode] = {}
        self.edges: List[EvidenceRelationship] = []

    def add_evidence(self, evidence: ResearchEvidence) -> None:
        if evidence.case_id != self.case_id:
            raise ValueError("Evidence case_id does not match graph case_id")
        self.nodes[evidence.evidence_id] = EvidenceGraphNode(evidence)
        self.build_graph()

    def build_graph(self) -> None:
        evidence_list = [node.evidence for node in self.nodes.values()]
        self.edges = EvidenceReasoningEngine.analyze_relationships(evidence_list)

    def get_cluster(self, category: str) -> List[EvidenceGraphNode]:
        cat_upper = category.strip().upper()
        return [
            node for node in self.nodes.values()
            if str(node.evidence.category).strip().upper() == cat_upper
        ]

    def compute_thesis_support_score(self) -> Dict[str, float]:
        """
        Calculates aggregate thesis support and contradiction scores based on graph connectivity and quality weights.
        """
        if not self.nodes:
            return {"support_score": 0.0, "contradiction_score": 0.0, "net_score": 0.0}

        total_support = 0.0
        total_contradiction = 0.0

        for node in self.nodes.values():
            weight = getattr(node.quality, "quality_score", None)
            if weight is None or weight <= 0:
                weight = (node.evidence.confidence * node.evidence.materiality * node.evidence.recency)
            if weight <= 0:
                weight = 1.0  # Safe fallback weight

            polarity = str(node.evidence.polarity).strip().upper()
            if polarity == "POSITIVE":
                total_support += weight
            elif polarity == "NEGATIVE":
                total_contradiction += weight

        for edge in self.edges:
            if edge.relation_type == "CONTRADICTS":
                total_contradiction += (edge.strength * 0.5)
            elif edge.relation_type == "CORROBORATES":
                total_support += (edge.strength * 0.3)

        net_score = round(total_support - total_contradiction, 4)
        return {
            "support_score": round(total_support, 4),
            "contradiction_score": round(total_contradiction, 4),
            "net_score": net_score
        }