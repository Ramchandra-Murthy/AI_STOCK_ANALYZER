from __future__ import annotations

from typing import Any

from services.market_data.pipeline_integration import (
    FullyIntegratedMarketPipeline,
)


class EROSProductionWorkflowOrchestrator:
    """
    EROS 3.0 production workflow orchestrator.

    Connects the validated market-data pipeline to the unified
    research/scoring/decision result and exposes a stable
    production API response.
    """

    def __init__(
        self,
        policy_profile: str = "Institutional",
    ) -> None:
        self.market_pipeline = FullyIntegratedMarketPipeline(policy_profile=policy_profile)

    def execute_workflow(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        """
        Execute the complete production workflow for one symbol.
        """

        packet, decision, result, trace = self.market_pipeline.evaluate_stock_securely(symbol)

        if not decision.allowed_in_scoring or result is None:
            return {
                "symbol": symbol,
                "status": "REJECTED_BY_INTEGRITY_GATE",
                "directive": decision.directive,
                "warning_message": decision.warning_message,
                "trace": {
                    "raw_state": trace.raw_data_state,
                    "validation_status": trace.validation_status,
                    "confidence_penalty": (trace.confidence_penalty),
                },
            }

        investment_decision = result.decision

        return {
            "symbol": symbol,
            "status": "SUCCESS",
            "market_data": {
                "current_price": packet.current_price,
                "volume": packet.volume,
                "source": packet.details.get("source"),
                "state": decision.directive,
            },
            "confidence_metrics": {
                "base_confidence": trace.base_confidence,
                "confidence_penalty": (trace.confidence_penalty),
                "adjusted_confidence": (result.adjusted_confidence),
            },
            "investment_decision": {
                "final_action": result.final_action,
                "composite_score": (investment_decision.composite_score),
                "target_allocation": (investment_decision.target_weight),
                "portfolio_weight": (investment_decision.portfolio_weight),
                "incremental_weight": (investment_decision.incremental_weight),
                "confidence": (investment_decision.confidence),
                "rating": investment_decision.rating,
                "expected_return": (investment_decision.expected_return),
                "downside_risk": (investment_decision.downside_risk),
                "net_expected_return": (investment_decision.net_expected_return),
                "rationale": (investment_decision.rationale),
                "evidence": (investment_decision.evidence),
            },
            "audit_trace": {
                "timestamp": trace.timestamp,
                "engine_version": trace.details.get(
                    "engine_version",
                    "EROS-3.0-BLOCK-23J",
                ),
            },
        }
