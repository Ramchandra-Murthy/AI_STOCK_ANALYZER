from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from services.scoring.models import AIScoreResult
from services.scoring.investment_decision import InvestmentDecisionOrchestrator, InvestmentDecisionResult
from services.research.block17_engine import Block17ResearchOrchestrator, ResearchIntelligenceResult
from services.reasoning.block17_reasoning import Block17ReasoningOrchestrator, EvidenceReasoningResult
from services.scoring.block17_confidence import Block17ConfidenceOrchestrator, ResearchConfidenceResult
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
    EROS 3.0 Block 18 Unified Orchestrator.
    Bridges quantitative scoring, research intelligence, evidence reasoning, 
    confidence adjustment, and institutional portfolio decision execution.
    """
    def __init__(self, policy_profile: str = "Institutional", max_position_limit: float = 0.12, aum_baseline: float = 100000000.0) -> None:
        self.decision_orchestrator = InvestmentDecisionOrchestrator(
            policy_profile=policy_profile,
            max_position_limit=max_position_limit,
            aum_baseline=aum_baseline
        )
        self.research_orchestrator = Block17ResearchOrchestrator()
        self.reasoning_orchestrator = Block17ReasoningOrchestrator()
        self.confidence_orchestrator = Block17ConfidenceOrchestrator()

    def evaluate(
        self,
        ai_score: AIScoreResult,
        holdings: Optional[Dict[str, Dict[str, float]]] = None,
        portfolio_weight: Optional[float] = None,
        ratios: Optional[FinancialRatios] = None,
    ) -> UnifiedInvestmentResult:
        symbol = ai_score.symbol

        # 1. Run Block 17 Research Intelligence & Economic Moat
        research_res = self.research_orchestrator.evaluate(
            symbol=symbol,
            ratios=ratios,
            composite_score=ai_score.composite_score
        )

        # 2. Run Block 17 Evidence & Business Reasoning
        reasoning_res = self.reasoning_orchestrator.evaluate(ai_score=ai_score)

        # 3. Run Block 17 Confidence Orchestration
        confidence_res = self.confidence_orchestrator.evaluate(
            symbol=symbol,
            evidence_confidence=0.90,
            reasoning_confidence=reasoning_res.reasoning_confidence,
            moat_score=research_res.moat_score,
            contradiction_count=reasoning_res.contradiction_count
        )

        # 4. Run Block 16 Investment Decision & Portfolio Orchestrator
        decision_res = self.decision_orchestrator.evaluate(
            ai_score=ai_score,
            holdings=holdings,
            portfolio_weight=portfolio_weight
        )

        # 5. Integrate Research Confidence into Final Decision Action & Confidence
        final_action = decision_res.action
        adjusted_confidence = round(decision_res.confidence * confidence_res.overall_confidence, 2)

        summary_rationale = list(decision_res.rationale)
        summary_rationale.append(f"Research Moat Classification: {research_res.moat_classification} (Score: {research_res.moat_score:.1f})")
        summary_rationale.append(f"Research Confidence Rating: {confidence_res.confidence_rating} ({confidence_res.overall_confidence*100:.1f}%)")
        if reasoning_res.high_severity_contradictions > 0:
            summary_rationale.append(f"Warning: {reasoning_res.high_severity_contradictions} high-severity evidence contradiction(s) detected.")

        details = {
            "engine_version": "EROS-3.0-BLOCK-18",
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
            },
            "execution_summary": {
                "target_weight": decision_res.target_weight,
                "incremental_weight": decision_res.incremental_weight,
                "execution_cost": decision_res.execution_cost,
                "net_expected_return": decision_res.net_expected_return,
            }
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
