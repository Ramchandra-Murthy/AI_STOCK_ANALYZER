from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List
from services.market_data.integrity import MarketDataValidationReport

@dataclass(frozen=True, slots=True)
class MarketDataDecisionResult:
    symbol: str
    directive: str  # "USE_LIVE", "USE_FALLBACK_WITH_WARNING", "USE_STALE_WITH_WARNING", "REJECT_DATA"
    confidence_penalty: float  # e.g., 0.0, 0.15, 0.30, 1.0
    allowed_in_scoring: bool
    warning_message: Optional[str]
    details: Dict[str, Any] = field(default_factory=dict)

class MarketDataDecisionGate:
    """
    EROS 3.0 Block 23F Market Data Decision Gate.
    Governs whether market data packets can proceed into EROS scoring and calculates confidence penalties.
    """
    @staticmethod
    def evaluate_decision(report: MarketDataValidationReport) -> MarketDataDecisionResult:
        state = report.data_state

        if state == "LIVE":
            return MarketDataDecisionResult(
                symbol=report.symbol,
                directive="USE_LIVE",
                confidence_penalty=0.0,
                allowed_in_scoring=True,
                warning_message=None,
                details={"engine_version": "EROS-3.0-BLOCK-23F", "state": state}
            )
        elif state == "FALLBACK":
            return MarketDataDecisionResult(
                symbol=report.symbol,
                directive="USE_FALLBACK_WITH_WARNING",
                confidence_penalty=0.15,
                allowed_in_scoring=True,
                warning_message=f"Data retrieved via fallback parity adapter for {report.symbol}. Confidence penalized by 15%.",
                details={"engine_version": "EROS-3.0-BLOCK-23F", "state": state}
            )
        elif state == "STALE":
            return MarketDataDecisionResult(
                symbol=report.symbol,
                directive="USE_STALE_WITH_WARNING",
                confidence_penalty=0.30,
                allowed_in_scoring=True,
                warning_message=f"Market data for {report.symbol} is stale (age: {report.freshness_age_seconds}s). Confidence penalized by 30%.",
                details={"engine_version": "EROS-3.0-BLOCK-23F", "state": state}
            )
        else:
            return MarketDataDecisionResult(
                symbol=report.symbol,
                directive="REJECT_DATA",
                confidence_penalty=1.0,
                allowed_in_scoring=False,
                warning_message=f"Market data for {report.symbol} is INVALID. Errors: {report.errors}. Rejected from scoring pipeline.",
                details={"engine_version": "EROS-3.0-BLOCK-23F", "state": state}
            )
