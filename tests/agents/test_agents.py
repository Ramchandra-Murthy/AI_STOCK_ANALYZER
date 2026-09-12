from __future__ import annotations

from services.agents.base_agent import AgentOpinion, QualityAgent, RiskAgent, ValuationAgent
from services.agents.coordinator import MultiAgentCoordinator


def test_agent_opinion_immutability_and_defaults() -> None:
    opinion = AgentOpinion(
        agent_name="TestAgent",
        recommendation="BUY",
        confidence=0.85,
        evidence=["Strong growth"],
        risks=["High debt"],
    )
    assert opinion.agent_name == "TestAgent"
    assert opinion.recommendation == "BUY"
    assert opinion.confidence == 0.85
    assert opinion.timestamp is not None
    assert isinstance(opinion.metadata, dict)


def test_specialist_agents_execution() -> None:
    val_agent = ValuationAgent()
    op = val_agent.evaluate("RELIANCE.NS")
    assert op.agent_name == "ValuationAgent"
    assert op.recommendation == "BUY"
    assert len(op.evidence) > 0

    qual_agent = QualityAgent()
    op_q = qual_agent.evaluate("RELIANCE.NS")
    assert op_q.agent_name == "QualityAgent"
    assert op_q.confidence > 0.90


def test_multi_agent_coordinator_default_registry() -> None:
    coordinator = MultiAgentCoordinator()
    result = coordinator.evaluate_symbol("RELIANCE.NS")

    assert result["symbol"] == "RELIANCE.NS"
    assert result["consensus_recommendation"] == "BUY"
    assert 0.0 <= result["overall_confidence"] <= 1.0
    assert result["participating_agents"] == 4
    assert len(result["opinions"]) == 4
    assert len(result["synthesized_evidence"]) > 0
    assert len(result["synthesized_risks"]) > 0


def test_multi_agent_coordinator_empty_registry() -> None:
    coordinator = MultiAgentCoordinator(agents=[])
    result = coordinator.evaluate_symbol("EMPTY.NS")
    assert result["participating_agents"] == 0
    assert result["consensus_recommendation"] == "HOLD"
    assert result["overall_confidence"] == 0.0


def test_multi_agent_coordinator_conflicting_recommendations() -> None:
    class BearAgent(RiskAgent):
        def evaluate(self, symbol: str) -> AgentOpinion:
            return AgentOpinion(
                agent_name="BearAgent",
                recommendation="SELL",
                confidence=0.95,
                evidence=["Severe downturn"],
                risks=["Insolvency risk"],
            )

    coordinator = MultiAgentCoordinator(agents=[BearAgent()])
    result = coordinator.evaluate_symbol("BEAR.NS")
    assert result["consensus_recommendation"] == "SELL"
    assert result["overall_confidence"] == 1.0
