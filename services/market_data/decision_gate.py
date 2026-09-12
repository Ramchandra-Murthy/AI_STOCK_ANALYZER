from __future__ import annotations

from dataclasses import dataclass, field

from services.market_data.integrity import MarketDataValidationReport


@dataclass(frozen=True, slots=True)
class MarketDataDecisionResult:
    symbol: str
    directive: str
    confidence_penalty: float
    allowed_in_scoring: bool
    warning_message: str | None
    details: dict[str, object] = field(default_factory=dict)


class MarketDataDecisionGate:
    """Govern whether validated market data may enter analysis."""

    @staticmethod
    def evaluate_decision(report: MarketDataValidationReport) -> MarketDataDecisionResult:
        state = report.data_state
        details = {"engine_version": "EROS-3.0-BLOCK-23F", "state": state}

        if state == "LIVE":
            return MarketDataDecisionResult(
                symbol=report.symbol,
                directive="USE_LIVE",
                confidence_penalty=0.0,
                allowed_in_scoring=True,
                warning_message=None,
                details=details,
            )

        if state == "FALLBACK":
            return MarketDataDecisionResult(
                symbol=report.symbol,
                directive="REJECT_FALLBACK",
                confidence_penalty=1.0,
                allowed_in_scoring=False,
                warning_message=(
                    f"Fallback market data for {report.symbol} is blocked from "
                    "investment scoring."
                ),
                details=details,
            )

        if state == "STALE":
            return MarketDataDecisionResult(
                symbol=report.symbol,
                directive="REJECT_STALE",
                confidence_penalty=1.0,
                allowed_in_scoring=False,
                warning_message=(
                    f"Stale market data for {report.symbol} is blocked from " "investment scoring."
                ),
                details=details,
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
            details=details,
        )
