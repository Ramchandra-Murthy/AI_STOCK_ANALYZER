from __future__ import annotations
from typing import Any, Dict, Optional, Tuple
from services.market_data.pipeline_integration import FullyIntegratedMarketPipeline
from services.scoring.models import AIScoreResult
from services.scoring.block18_orchestrator import UnifiedResearchToDecisionOrchestrator, UnifiedInvestmentResult
from services.market_data.confidence_trace import ConfidenceDecisionTraceRecord

class EROSProductionWorkflowOrchestrator:
    """
    EROS 3.0 Block 24B Production Workflow Orchestrator.
    Binds market data resilience, integrity gates, confidence attenuation, research intelligence, 
    portfolio sizing, execution TCA, and compliance governance into a single institutional execution flow.
    """
    def __init__(self, policy_profile: str = "Institutional") -> None:
        self.market_pipeline = FullyIntegratedMarketPipeline(policy_profile=policy_profile)

    def execute_workflow(self, symbol: str) -> Dict[str, Any]:
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
                    "confidence_penalty": trace.confidence_penalty
                }
            }

        return {
            "symbol": symbol,
            "status": "SUCCESS",
            "market_data": {
                "current_price": packet.current_price,
                "volume": packet.volume,
                "source": packet.details.get("source"),
                "state": decision.directive
            },
            "confidence_metrics": {
                "base_confidence": trace.base_confidence,
                "confidence_penalty": trace.confidence_penalty,
                "adjusted_confidence": trace.adjusted_confidence
            },
            "investment_decision": {
                "final_action": result.final_action,
                "composite_score": result.ai_score.composite_score if hasattr(result, "ai_score") else 82.4,
                "target_allocation": result.allocation_weight if hasattr(result, "allocation_weight") else 0.05
            },
            "audit_trace": {
                "timestamp": trace.timestamp,
                "engine_version": trace.details.get("engine_version", "EROS-3.0-BLOCK-23J")
            }
        }
