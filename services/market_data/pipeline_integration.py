from __future__ import annotations

from typing import Any

from services.market_data.confidence_trace import (
    ConfidenceAuditLogger,
    ConfidenceDecisionTraceRecord,
)
from services.market_data.decision_gate import (
    MarketDataDecisionGate,
    MarketDataDecisionResult,
)
from services.market_data.integrity import MarketDataIntegrityGate
from services.market_data.provider_resilience import ResilientMarketDataProvider
from services.scoring.block18_orchestrator import (
    UnifiedInvestmentResult,
    UnifiedResearchToDecisionOrchestrator,
)
from services.scoring.models import AIScoreResult


class FullyIntegratedMarketPipeline:
    """EROS production market-data pipeline with fail-closed integrity gating."""

    def __init__(self, policy_profile: str = "Institutional") -> None:
        self.orchestrator = UnifiedResearchToDecisionOrchestrator(
            policy_profile=policy_profile
        )

    def evaluate_stock_securely(
        self, symbol: str
    ) -> tuple[Any, MarketDataDecisionResult, UnifiedInvestmentResult | None, ConfidenceDecisionTraceRecord]:
        """Validate provider data before scoring and preserve the audit trace."""
        normalized_symbol = symbol.strip().upper() if isinstance(symbol, str) else ""
        packet, report = ResilientMarketDataProvider.get_validated_market_data(
            normalized_symbol
        )
        decision = MarketDataDecisionGate.evaluate_decision(report)

        base_confidence = 0.85
        adjusted_confidence = max(
            0.0, base_confidence - decision.confidence_penalty
        )

        if not decision.allowed_in_scoring:
            trace_record = ConfidenceAuditLogger.create_trace(
                symbol=normalized_symbol,
                raw_state=report.data_state,
                valid=report.is_valid,
                directive=decision.directive,
                base_conf=base_confidence,
                penalty=decision.confidence_penalty,
                adj_conf=0.0,
                composite_score=0.0,
                action="REJECT_DATA",
            )
            return packet, decision, None, trace_record

        if packet.current_price is None or packet.current_price <= 0:
            invalid_report = MarketDataIntegrityGate.validate_packet(packet)
            trace_record = ConfidenceAuditLogger.create_trace(
                symbol=normalized_symbol,
                raw_state=invalid_report.data_state,
                valid=False,
                directive="REJECT_INVALID_MARKET_DATA",
                base_conf=base_confidence,
                penalty=1.0,
                adj_conf=0.0,
                composite_score=0.0,
                action="REJECT_DATA",
            )
            return packet, decision, None, trace_record

        # The scoring layer is not allowed to invent company fundamentals.
        # It receives only provider-backed market data until the upstream
        # fundamentals adapters are connected.
        ai_score = AIScoreResult(
            symbol=normalized_symbol,
            growth_score=0.0,
            quality_score=0.0,
            profitability_score=0.0,
            capital_allocation_score=0.0,
            valuation_score=0.0,
            momentum_score=0.0,
            risk_score=0.0,
            composite_score=0.0,
            breakdown_details={
                "current_price": packet.current_price,
                "data_state": decision.directive,
                "confidence_penalty": decision.confidence_penalty,
                "adjusted_confidence": adjusted_confidence,
                "scoring_status": "FUNDAMENTALS_REQUIRED",
            },
        )

        # Do not classify an all-zero placeholder score as an investment decision.
        result = self.orchestrator.evaluate(
            ai_score,
            holdings=None,
            portfolio_weight=0.0,
        )
        trace_record = ConfidenceAuditLogger.create_trace(
            symbol=normalized_symbol,
            raw_state=report.data_state,
            valid=report.is_valid,
            directive=decision.directive,
            base_conf=base_confidence,
            penalty=decision.confidence_penalty,
            adj_conf=adjusted_confidence,
            composite_score=ai_score.composite_score,
            action="REJECT_INCOMPLETE_RESEARCH",
        )
        return packet, decision, None, trace_record
