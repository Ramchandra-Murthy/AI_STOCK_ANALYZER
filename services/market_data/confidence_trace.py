from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime

@dataclass(frozen=True, slots=True)
class ConfidenceDecisionTraceRecord:
    symbol: str
    raw_data_state: str
    validation_status: bool
    decision_directive: str
    base_confidence: float
    confidence_penalty: float
    adjusted_confidence: float
    composite_ai_score: float
    final_investment_action: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)

class ConfidenceAuditLogger:
    """
    EROS 3.0 Block 23J Confidence Decision Trace Logger.
    Generates immutable, machine-readable audit trails for market data confidence attenuation.
    """
    @staticmethod
    def create_trace(
        symbol: str,
        raw_state: str,
        valid: bool,
        directive: str,
        base_conf: float,
        penalty: float,
        adj_conf: float,
        composite_score: float,
        action: str
    ) -> ConfidenceDecisionTraceRecord:
        return ConfidenceDecisionTraceRecord(
            symbol=symbol,
            raw_data_state=raw_state,
            validation_status=valid,
            decision_directive=directive,
            base_confidence=base_conf,
            confidence_penalty=penalty,
            adjusted_confidence=adj_conf,
            composite_ai_score=composite_score,
            final_investment_action=action,
            details={
                "engine_version": "EROS-3.0-BLOCK-23J",
                "audit_level": "Institutional Strict"
            }
        )
