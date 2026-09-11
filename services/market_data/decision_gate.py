from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from services.market_data.integrity import MarketDataValidationReport


@dataclass(frozen=True, slots=True)
class MarketDataDecisionResult:
    symbol: str
    directive: str
    confidence_penalty: float
    allowed_in_scoring: bool
    warning_message: str | None
    details: dict[str, Any] = field(default_factory=dict)


class MarketDataDecisionGate:
    """Govern whether validated market data may enter the scoring pipeline."""

    @staticmethod
    def evaluate_decision(
        report: MarketDataValidationReport,
    ) -> MarketDataDecisionResult:
        state = report.data_state
        base_details = {
            "engine_version": "EROS-3.0-BLOCK-23F",
            "state": state,
        }

        if state == "LIVE":
            return MarketDataDecisionResult(
                symbol=report.symbol,
                directive="USE_LIVE",
                confidence_penalty=0.0,
                allowed_in_scoring=True,
                warning_message=None,
                details=base_details,
            )

        if state == "FALLBACK":
            return MarketDataDecisionResult(
                symbol=report.symbol,
                directive="USE_FALLBACK_WITH_WARNING",
                confidence_penalty=0.15,
                allowed_in_scoring=True,
                warning_message=(
                    f"Data retrieved via fallback parity adapter for {report.symbol}. "
                    "Confidence penalized by 15%."
                ),
                details=base_details,
            )

        if state == "STALE":
            return MarketDataDecisionResult(
                symbol=report.symbol,
                directive="USE_STALE_WITH_WARNING",
                confidence_penalty=0.30,
                allowed_in_scoring=True,
                warning_message=(
                    f"Market data for {report.symbol} is stale "
                    f"(age: {report.freshness_age_seconds}s). "
                    "Confidence penalized by 30%."
                ),
                details=base_details,
            )

        return MarketDataDecisionResult(
            symbol=report.symbol,
            directive="REJECT_DATA",
            confidence_penalty=1.0,
            allowed_in_scoring=False,
            warning_message=(
                f"Market data for {report.symbol} is INVALID. "
                f"Errors: {report.errors}. Rejected from scoring pipeline."
            ),
            details=base_details,
        )
