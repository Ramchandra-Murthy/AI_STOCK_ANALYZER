from __future__ import annotations

from backend.research.evidence.graph.evidence_graph import EvidenceGraph
from backend.research.evidence.services.evidence_service import EvidenceService
from backend.research.services.research_case_service import ResearchCaseService


def test_evidence_graph_node_addition() -> None:
    case = ResearchCaseService.create_case(symbol="TCS.NS", objective="Test graph construction")
    ev = EvidenceService.create_evidence(
        case, category="FUNDAMENTAL", statement="High margins", polarity="POSITIVE"
    )

    graph = EvidenceGraph(case_id=case.case_id, symbol=case.symbol)
    graph.add_evidence(ev)
    assert len(graph.nodes) == 1
    assert ev.evidence_id in graph.nodes


def test_evidence_graph_clustering_and_scoring() -> None:
    case = ResearchCaseService.create_case(symbol="INFY.NS", objective="Test graph scoring")
    ev1 = EvidenceService.create_evidence(
        case,
        category="FUNDAMENTAL",
        statement="Strong growth",
        polarity="POSITIVE",
        confidence=0.95,
    )
    ev2 = EvidenceService.create_evidence(
        case,
        category="VALUATION",
        statement="Attractive entry",
        polarity="POSITIVE",
        confidence=0.90,
    )
    ev3 = EvidenceService.create_evidence(
        case, category="RISK", statement="High currency risk", polarity="NEGATIVE", confidence=0.80
    )

    graph = EvidenceGraph(case_id=case.case_id, symbol=case.symbol)
    graph.add_evidence(ev1)
    graph.add_evidence(ev2)
    graph.add_evidence(ev3)
    graph.build_graph()

    # Inspect available categories in graph nodes for robustness
    all_categories = [node.evidence.category for node in graph.nodes.values()]
    target_cat = all_categories[0] if all_categories else "FUNDAMENTAL"

    cluster = graph.get_cluster(target_cat)
    assert len(cluster) >= 1

    scores = graph.compute_thesis_support_score()
    assert scores["support_score"] > 0
    assert scores["contradiction_score"] > 0
    assert "net_score" in scores
