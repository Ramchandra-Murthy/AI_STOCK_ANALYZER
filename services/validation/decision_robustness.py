from __future__ import annotations

from typing import Any

from services.scoring.block18_orchestrator import UnifiedResearchToDecisionOrchestrator
from services.scoring.models import AIScoreResult


class DecisionRobustnessEngine:
    """
    EROS 3.0 Block 22B Decision Robustness Engine.
    Evaluates engine stability under conflicting multi-pillar signals (e.g., high valuation vs strong growth).
    """

    @staticmethod
    def evaluate_conflicting_signals(symbol: str, scenario: str) -> dict[str, Any]:
        orchestrator = UnifiedResearchToDecisionOrchestrator(policy_profile="Institutional")

        if scenario == "high_valuation_strong_growth":
            ai_score = AIScoreResult(
                symbol=symbol,
                growth_score=92.0,
                quality_score=85.0,
                profitability_score=88.0,
                capital_allocation_score=80.0,
                valuation_score=35.0,  # High valuation / low score
                momentum_score=75.0,
                risk_score=82.0,
                composite_score=76.7,
                breakdown_details={"rating": "BUY"},
            )
        elif scenario == "poor_fundamentals_strong_momentum":
            ai_score = AIScoreResult(
                symbol=symbol,
                growth_score=40.0,
                quality_score=45.0,
                profitability_score=42.0,
                capital_allocation_score=38.0,
                valuation_score=50.0,
                momentum_score=95.0,  # High momentum
                risk_score=40.0,
                composite_score=53.1,
                breakdown_details={"rating": "HOLD"},
            )
        else:
            ai_score = AIScoreResult(
                symbol=symbol,
                growth_score=70.0,
                quality_score=70.0,
                profitability_score=70.0,
                capital_allocation_score=70.0,
                valuation_score=70.0,
                momentum_score=70.0,
                risk_score=70.0,
                composite_score=70.0,
                breakdown_details={"rating": "HOLD"},
            )

        result = orchestrator.evaluate(ai_score, holdings=None, portfolio_weight=0.03)
        return {
            "scenario": scenario,
            "symbol": symbol,
            "final_action": result.final_action,
            "adjusted_confidence": result.adjusted_confidence,
            "rationale_count": len(result.summary_rationale),
        }
