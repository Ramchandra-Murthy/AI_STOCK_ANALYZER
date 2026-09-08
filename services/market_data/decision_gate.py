from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from services.market_data.integrity import MarketDataValidationReport


ENGINE_VERSION = "EROS-3.0-BLOCK-23F-REPAIRED"


@dataclass(frozen=True, slots=True)
class MarketDataDecisionResult:
    symbol: str
    directive: str
    confidence_penalty: float
    allowed_in_scoring: bool
    warning_message: Optional[str]
    details: Dict[str, Any] = field(default_factory=dict)


class MarketDataDecisionGate:
    """
    Non-bypassable decision boundary for market-data quality.

    LIVE is the only state permitted into live scoring. FALLBACK and STALE are
    preserved as diagnostic states, but are blocked rather than confidence-
    attenuated. INVALID is also blocked.
    """

    @staticmethod
    def evaluate_decision(
        report: MarketDataValidationReport,
    ) -> MarketDataDecisionResult:
        state = report.data_state

        if state == "LIVE" and report.is_valid:
            return MarketDataDecisionResult(
                symbol=report.symbol,
                directive="USE_LIVE",
                confidence_penalty=0.0,
                allowed_in_scoring=True,
                warning_message=None,
                details={
                    "engine_version": ENGINE_VERSION,
                    "state": state,
                    "live_scoring_allowed": True,
                },
            )

        if state == "FALLBACK":
            return MarketDataDecisionResult(
                symbol=report.symbol,
                directive="REJECT_FALLBACK",
                confidence_penalty=1.0,
                allowed_in_scoring=False,
                warning_message=(
                    f"Fallback market data for {report.symbol} is diagnostic-only "
                    "and cannot enter live scoring."
                ),
                details={
                    "engine_version": ENGINE_VERSION,
                    "state": state,
                    "live_scoring_allowed": False,
                },
            )

        if state == "STALE":
            return MarketDataDecisionResult(
                symbol=report.symbol,
                directive="REJECT_STALE",
                confidence_penalty=1.0,
                allowed_in_scoring=False,
                warning_message=(
                    f"Market data for {report.symbol} is stale "
                    f"(age: {report.freshness_age_seconds}s)."
                ),
                details={
                    "engine_version": ENGINE_VERSION,
                    "state": state,
                    "live_scoring_allowed": False,
                },
            )

        return MarketDataDecisionResult(
            symbol=report.symbol,
            directive="REJECT_DATA",
            confidence_penalty=1.0,
            allowed_in_scoring=False,
            warning_message=(
                f"Market data for {report.symbol} is invalid and was rejected. "
                f"Errors: {report.errors}"
            ),
            details={
                "engine_version": ENGINE_VERSION,
                "state": state,
                "live_scoring_allowed": False,
            },
        )


__all__ = [
    "ENGINE_VERSION",
    "MarketDataDecisionGate",
    "MarketDataDecisionResult",
]
