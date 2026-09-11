from __future__ import annotations

from typing import Any

from services.market_data.confidence_trace import (
    ConfidenceAuditLogger,
    ConfidenceDecisionTraceRecord,
)
from services.market_data.decision_gate import MarketDataDecisionGate, MarketDataDecisionResult
from services.market_data.integrity import MarketDataIntegrityGate
from services.market_data.provider_resilience import ResilientMarketDataProvider
from services.scoring.models import AIScoreResult


class FullyIntegratedMarketPipeline:
    """Production market-data gate that never converts incomplete data into a decision."""

    def __init__(self, policy_profile: str = "Institutional") -> None:
        self.policy_profile = policy_profile

    def evaluate_stock_securely(
        self, symbol: str
    ) -> tuple[Any, MarketDataDecisionResult, None, ConfidenceDecisionTraceRecord]:
        normalized_symbol = symbol.strip().upper() if isinstance(symbol, str) else ""
        packet, report = ResilientMarketDataProvider.get_validated_market_data(normalized_symbol)
        decision = MarketDataDecisionGate.evaluate_decision(report)
        base_confidence = 0.0

        if not decision.allowed_in_scoring:
            trace_record = ConfidenceAuditLogger.create_trace(
                symbol=normalized_symbol,
                raw_state=report.data_state,
                valid=report.is_valid,
                directive=decision.directive,
                base_conf=base_confidence,
                penalty=1.0,
                adj_conf=0.0,
                composite_score=0.0,
                action="REJECT_DATA",
            )
            return packet, decision, None, trace_record

        # Market price is necessary but not sufficient for an investment score.
        # Until fundamentals/research adapters are connected, explicitly return
        # an incomplete-research state rather than manufacturing pillar scores.
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
                "data_state": report.data_state,
                "scoring_status": "FUNDAMENTALS_REQUIRED",
            },
        )
        # Validate construction for interface compatibility without treating it as
        # an investment decision. The placeholder is intentionally not propagated.
        _ = ai_score
        trace_record = ConfidenceAuditLogger.create_trace(
            symbol=normalized_symbol,
            raw_state=report.data_state,
            valid=report.is_valid,
            directive="REJECT_INCOMPLETE_RESEARCH",
            base_conf=base_confidence,
            penalty=1.0,
            adj_conf=0.0,
            composite_score=0.0,
            action="REJECT_INCOMPLETE_RESEARCH",
        )
        return packet, decision, None, trace_record
