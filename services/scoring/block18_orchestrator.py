from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from services.scoring.models import AIScoreResult
from services.scoring.investment_decision import (
    InvestmentDecisionOrchestrator,
    InvestmentDecisionResult,
)
from services.research.block17_engine import (
    Block17ResearchOrchestrator,
    ResearchIntelligenceResult,
)
from services.reasoning.block17_reasoning import (
    Block17ReasoningOrchestrator,
    EvidenceReasoningResult,
)
from services.scoring.block17_confidence import (
    Block17ConfidenceOrchestrator,
    ResearchConfidenceResult,
)
from services.ratios.models import FinancialRatios


@dataclass(frozen=True, slots=True)
class UnifiedInvestmentResult:
    symbol: str
    decision: InvestmentDecisionResult
    research: ResearchIntelligenceResult
    reasoning: EvidenceReasoningResult
    confidence: ResearchConfidenceResult
    final_action: str
    adjusted_confidence: float
    summary_rationale: List[str]
    details: Dict[str, Any]


class UnifiedResearchToDecisionOrchestrator:
    """
    EROS 3.0 Block 18 unified evidence-to-decision orchestrator.

    The orchestrator does not create market evidence. The canonical market
    packet is represented in AIScoreResult.breakdown_details and is propagated
    unchanged into downstream research and execution decisions.
    """

    def __init__(
        self,
        policy_profile: str = "Institutional",
        max_position_limit: float = 0.12,
        aum_baseline: float = 100000000.0,
    ) -> None:
        self.decision_orchestrator = InvestmentDecisionOrchestrator(
            policy_profile=policy_profile,
            max_position_limit=max_position_limit,
            aum_baseline=aum_baseline,
        )
        self.research_orchestrator = Block17ResearchOrchestrator()
        self.reasoning_orchestrator = Block17ReasoningOrchestrator()
        self.confidence_orchestrator = Block17ConfidenceOrchestrator()

    @staticmethod
    def _evidence_from_score(ai_score: AIScoreResult) -> Dict[str, Any]:
        """Extract only explicitly observed evidence from the scoring packet."""
        details = dict(ai_score.breakdown_details or {})
        observed = list(details.get("observed_pillars") or [])
        return {
            "scoring_source": details.get("scoring_source"),
            "observed_pillars": observed,
            "fundamental_pillars_available": bool(
                details.get("fundamental_pillars_available", False)
            ),
            "market_data_state": details.get("market_data_state")
            or details.get("data_state"),
            "market_price_source": details.get("market_price_source"),
            "current_price": details.get("current_price"),
            "previous_close": details.get("previous_close"),
        }

    def evaluate(
        self,
        ai_score: AIScoreResult,
        holdings: Optional[Dict[str, Dict[str, float]]] = None,
        portfolio_weight: Optional[float] = None,
        ratios: Optional[FinancialRatios] = None,
    ) -> UnifiedInvestmentResult:
        symbol = ai_score.symbol
        evidence = self._evidence_from_score(ai_score)

        # 1. Research is explicitly downstream of the same evidence packet.
        research_res = self.research_orchestrator.evaluate(
            symbol=symbol,
            ratios=ratios,
            composite_score=ai_score.composite_score,
            evidence=evidence,
        )

        # 2. Evidence reasoning consumes the same AIScoreResult.
        reasoning_res = self.reasoning_orchestrator.evaluate(ai_score=ai_score)

        # 3. Confidence reflects the evidence actually observed by the pipeline.
        observed_count = len(evidence["observed_pillars"])
        fundamental_available = evidence["fundamental_pillars_available"]
        evidence_confidence = min(
            1.0,
            (observed_count + int(fundamental_available)) / 4.0,
        )
        confidence_res = self.confidence_orchestrator.evaluate(
            symbol=symbol,
            evidence_confidence=evidence_confidence,
            reasoning_confidence=reasoning_res.reasoning_confidence,
            moat_score=research_res.moat_score,
            contradiction_count=reasoning_res.contradiction_count,
        )

        # 4. Investment decision receives the canonical observed price only.
        # No synthetic/default execution price is permitted.
        decision_res = self.decision_orchestrator.evaluate(
            ai_score=ai_score,
            holdings=holdings,
            portfolio_weight=portfolio_weight,
        )

        # 5. Integrate research confidence into the final decision.
        final_action = decision_res.action
        adjusted_confidence = round(
            decision_res.confidence * confidence_res.overall_confidence,
            2,
        )

        summary_rationale = list(decision_res.rationale)
        summary_rationale.append(
            f"Research Moat Classification: {research_res.moat_classification} "
            f"(Score: {research_res.moat_score:.1f})"
        )
        summary_rationale.append(
            f"Research Confidence Rating: {confidence_res.confidence_rating} "
            f"({confidence_res.overall_confidence * 100:.1f}%)"
        )
        if reasoning_res.high_severity_contradictions > 0:
            summary_rationale.append(
                f"Warning: {reasoning_res.high_severity_contradictions} "
                "high-severity evidence contradiction(s) detected."
            )

        details = {
            "engine_version": "EROS-3.0-BLOCK-18-REPAIRED",
            "evidence_packet": evidence,
            "research_intelligence": {
                "research_score": research_res.research_score,
                "moat_classification": research_res.moat_classification,
                "thesis_summary": research_res.thesis_summary,
                "primary_risk": research_res.primary_risk,
            },
            "evidence_reasoning": {
                "hypothesis_count": reasoning_res.hypothesis_count,
                "contradiction_count": reasoning_res.contradiction_count,
                "hypotheses": reasoning_res.hypotheses_summaries,
                "contradictions": reasoning_res.contradictions_summaries,
            },
            "research_confidence": {
                "overall_confidence": confidence_res.overall_confidence,
                "rating": confidence_res.confidence_rating,
                "evidence_confidence": evidence_confidence,
            },
            "execution_summary": {
                "target_weight": decision_res.target_weight,
                "incremental_weight": decision_res.incremental_weight,
                "execution_cost": decision_res.execution_cost,
                "net_expected_return": decision_res.net_expected_return,
            },
        }

        return UnifiedInvestmentResult(
            symbol=symbol,
            decision=decision_res,
            research=research_res,
            reasoning=reasoning_res,
            confidence=confidence_res,
            final_action=final_action,
            adjusted_confidence=adjusted_confidence,
            summary_rationale=summary_rationale,
            details=details,
        )
