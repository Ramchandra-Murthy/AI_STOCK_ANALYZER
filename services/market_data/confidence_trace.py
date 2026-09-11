from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


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
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    details: dict[str, Any] = field(default_factory=dict)


class ConfidenceAuditLogger:
    """Generate immutable audit records for confidence attenuation decisions."""

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
        action: str,
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
                "audit_level": "Institutional Strict",
            },
        )
