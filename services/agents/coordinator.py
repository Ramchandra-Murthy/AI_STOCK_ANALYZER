from __future__ import annotations

import logging
from typing import Any

from services.agents.base_agent import (
    BaseSpecialistAgent,
    MarketAgent,
    QualityAgent,
    RiskAgent,
    ValuationAgent,
)

logger = logging.getLogger(__name__)


class MultiAgentCoordinator:
    """Orchestrates specialist AI agents via registry, computes confidence-weighted consensus, and synthesizes institutional reviews."""

    def __init__(self, agents: list[BaseSpecialistAgent] | None = None) -> None:
        self.agents: list[BaseSpecialistAgent] = (
            [ValuationAgent(), QualityAgent(), MarketAgent(), RiskAgent()]
            if agents is None
            else agents
        )

    def evaluate_symbol(self, symbol: str) -> dict[str, Any]:
        logger.info(
            "Coordinating multi-agent research network review for %s with %d agents",
            symbol,
            len(self.agents),
        )

        opinions = [agent.evaluate(symbol) for agent in self.agents]

        if not opinions:
            return {
                "symbol": symbol,
                "consensus_recommendation": "HOLD",
                "overall_confidence": 0.0,
                "participating_agents": 0,
                "opinions": [],
                "synthesized_evidence": [],
                "synthesized_risks": [],
            }

        buy_score = sum(o.confidence for o in opinions if o.recommendation == "BUY")
        hold_score = sum(o.confidence for o in opinions if o.recommendation == "HOLD")
        sell_score = sum(o.confidence for o in opinions if o.recommendation == "SELL")

        scores = {"BUY": buy_score, "HOLD": hold_score, "SELL": sell_score}

        consensus = max(scores, key=scores.get)
        total_score = sum(scores.values())
        overall_confidence = (
            round(max(scores.values()) / total_score, 4) if total_score > 0 else 0.0
        )

        all_evidence = [ev for o in opinions for ev in o.evidence]
        all_risks = [r for o in opinions for r in o.risks]

        return {
            "symbol": symbol,
            "consensus_recommendation": consensus,
            "overall_confidence": overall_confidence,
            "participating_agents": len(opinions),
            "opinions": opinions,
            "synthesized_evidence": all_evidence,
            "synthesized_risks": all_risks,
        }
