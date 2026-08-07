from __future__ import annotations

import pytest
from services.memory.models import ResearchMemory
from services.memory.memory_engine import KnowledgeMemoryEngine

def test_research_memory_immutability() -> None:
    mem = ResearchMemory(
        symbol="RELIANCE.NS",
        research_date="2025-08-07",
        summary="Strong retail tailwinds",
        committee_decision="BUY",
        valuation_snapshot={"dcf_value": 3200.0},
        forecast_snapshot={"eps": 110.0},
        thesis="Digital compounding"
    )
    assert mem.symbol == "RELIANCE.NS"
    assert mem.committee_decision == "BUY"
    assert mem.timestamp is not None
    assert isinstance(mem.metadata, dict)

def test_knowledge_memory_engine() -> None:
    mem1 = ResearchMemory(
        symbol="RELIANCE.NS",
        research_date="2025-08-07",
        summary="Initial thesis",
        committee_decision="BUY",
        valuation_snapshot={"dcf_value": 3000.0},
        forecast_snapshot={"eps": 100.0},
        thesis="Compounder"
    )
    mem2 = ResearchMemory(
        symbol="RELIANCE.NS",
        research_date="2026-08-07",
        summary="Updated thesis",
        committee_decision="BUY",
        valuation_snapshot={"dcf_value": 3500.0},
        forecast_snapshot={"eps": 125.0},
        thesis="Compounder accelerated"
    )

    KnowledgeMemoryEngine.store_memory(mem1)
    KnowledgeMemoryEngine.store_memory(mem2)

    results = KnowledgeMemoryEngine.query_memory("RELIANCE.NS")
    assert len(results) >= 2

    drift = KnowledgeMemoryEngine.analyze_drift("RELIANCE.NS")
    assert drift["symbol"] == "RELIANCE.NS"
    assert "message" in drift
