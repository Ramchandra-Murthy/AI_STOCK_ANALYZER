from __future__ import annotations

import pytest
from services.reasoning_graph.models import ReasoningEvidence
from services.reasoning_graph.propagation_engine import ReasoningPropagationEngine
from services.reasoning_graph.graph_reasoner import InstitutionalReasoningGraph

def test_reasoning_evidence_immutability() -> None:
    evidence = ReasoningEvidence(
        source_node="COMM-CRUDE",
        target_node="RELIANCE.NS",
        relationship="impacts_cost",
        impact="NEGATIVE",
        confidence=0.90,
        explanation="Crude price hike increases refining input costs."
    )
    assert evidence.source_node == "COMM-CRUDE"
    assert evidence.impact == "NEGATIVE"
    assert evidence.confidence == 0.90
    assert evidence.timestamp is not None
    assert isinstance(evidence.metadata, dict)

def test_reasoning_propagation_engine() -> None:
    chain = ReasoningPropagationEngine.propagate_shock("COMM-CRUDE", "NEGATIVE")
    assert len(chain) == 2
    assert chain[0].target_node == "SECTOR-ENERGY"
    assert chain[1].target_node == "RELIANCE.NS"

def test_institutional_reasoning_graph_explanation() -> None:
    explanation = InstitutionalReasoningGraph.explain_recommendation_change("RELIANCE.NS", "BUY", "HOLD")
    assert explanation["symbol"] == "RELIANCE.NS"
    assert explanation["previous_recommendation"] == "BUY"
    assert explanation["current_recommendation"] == "HOLD"
    assert len(explanation["primary_drivers"]) == 4
    assert len(explanation["causal_chain"]) == 2
    assert explanation["overall_confidence"] == 0.82
