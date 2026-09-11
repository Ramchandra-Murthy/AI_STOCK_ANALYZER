from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.ratios.models import FinancialRatios
from services.reasoning.block17_reasoning import (
    Block17ReasoningOrchestrator,
    EvidenceReasoningResult,
)
from services.research.block17_engine import (
    Block17ResearchOrchestrator,
    ResearchIntelligenceResult,
)
from services.scoring.block17_confidence import (
    Block17ConfidenceOrchestrator,
    ResearchConfidenceResult,
)
from services.scoring.investment_decision import (
    InvestmentDecisionOrchestrator,
    InvestmentDecisionResult,
)
from services.scoring.models import AIScoreResult


@dataclass(frozen=True, slots=True)
class UnifiedInvestmentResult:
    symbol: str
    decision: InvestmentDecisionResult
    research: ResearchIntelligenceResult
    reasoning: EvidenceReasoningResult
    confidence: ResearchConfidenceResult
    final_action: str
    adjusted_confidence: float
    summary_rationale: list[str]
    details: dict[str, Any]


class UnifiedResearchToDecisionOrchestrator:
    """Integrate validated scoring, research, reasoning, confidence and execution."""

    def __init__(
        self,
        policy_profile: str = "Institutional",
        max_position_limit: float = 0.12,
        aum_baseline: float = 100_000_000.0,
    ) -> None:
        self.decision_orchestrator = InvestmentDecisionOrchestrator(
            policy_profile=policy_profile,
            max_position_limit=max_position_limit,
            aum_baseline=aum_baseline,
        )
        self.research_orchestrator = Block17ResearchOrchestrator()
        self.reasoning_orchestrator = Block17ReasoningOrchestrator()
        self.confidence_orchestrator = Block17ConfidenceOrchestrator()

    def evaluate(
        self,
        ai_score: AIScoreResult,
        holdings: dict[str, dict[str, float]] | None = None,
        portfolio_weight: float | None = None,
        ratios: FinancialRatios | None = None,
    ) -> UnifiedInvestmentResult:
        symbol = ai_score.symbol.strip().upper()
        if not symbol:
            raise ValueError("ai_score.symbol must be non-empty")

        research_res = self.research_orchestrator.evaluate(
            symbol=symbol,
            ratios=ratios,
            composite_score=ai_score.composite_score,
        )
        reasoning_res = self.reasoning_orchestrator.evaluate(ai_score=ai_score)
        confidence_res = self.confidence_orchestrator.evaluate(
            symbol=symbol,
            evidence_confidence=research_res.confidence_score,
            reasoning_confidence=reasoning_res.reasoning_confidence,
            moat_score=research_res.moat_score,
            contradiction_count=reasoning_res.contradiction_count,
        )

        breakdown = ai_score.breakdown_details or {}
        live_price = breakdown.get("current_price")
        if not isinstance(live_price, (int, float)) or live_price <= 0:
            raise ValueError("ai_score.breakdown_details.current_price must be positive")

        decision_res = self.decision_orchestrator.evaluate(
            ai_score=ai_score,
            holdings=holdings,
            portfolio_weight=portfolio_weight,
            assumed_price=float(live_price),
        )

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
                f"Warning: {reasoning_res.high_severity_contradictions} high-severity "
                "evidence contradiction(s) detected."
            )
            if adjusted_confidence < 0.60:
                final_action = "HOLD"

        return UnifiedInvestmentResult(
            symbol=symbol,
            decision=decision_res,
            research=research_res,
            reasoning=reasoning_res,
            confidence=confidence_res,
            final_action=final_action,
            adjusted_confidence=adjusted_confidence,
            summary_rationale=summary_rationale,
            details={
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
                },
            },
        )
