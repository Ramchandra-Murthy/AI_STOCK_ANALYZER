from __future__ import annotations

from datetime import datetime, timezone
from math import sqrt
from typing import Any, Callable, Dict, Optional, Tuple

from services.market_data.provider_resilience import ResilientMarketDataProvider
from services.market_data.decision_gate import MarketDataDecisionGate, MarketDataDecisionResult
from services.market_data.confidence_trace import ConfidenceAuditLogger, ConfidenceDecisionTraceRecord
from services.scoring.models import AIScoreResult
from services.scoring.block18_orchestrator import UnifiedResearchToDecisionOrchestrator, UnifiedInvestmentResult


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _score_live_market(packet: Any) -> tuple[Dict[str, float], Dict[str, Any]]:
    """
    Derive only scores that are supported by the live OHLCV packet.

    Fundamental pillars are deliberately not synthesized here. A missing
    fundamental dataset must remain missing rather than becoming a plausible
    hard-coded score.
    """
    history = list(packet.ohlcv_history or [])
    closes = []
    for row in history:
        try:
            close = float(row.get("close"))
        except (TypeError, ValueError):
            continue
        if close > 0:
            closes.append(close)

    current = float(packet.current_price)
    previous = float(packet.previous_close)

    returns = []
    for earlier, later in zip(closes, closes[1:]):
        if earlier > 0:
            returns.append((later / earlier) - 1.0)

    momentum_base = (current / previous - 1.0) if previous > 0 else 0.0
    momentum_score = round(_clamp(50.0 + momentum_base * 500.0), 2)

    if len(returns) >= 2:
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        annualized_volatility = sqrt(variance) * sqrt(252.0)
    else:
        annualized_volatility = 0.0

    risk_score = round(_clamp(100.0 - annualized_volatility * 150.0), 2)

    # Only observed market pillars contribute to the composite.
    composite = round((momentum_score * 0.60) + (risk_score * 0.40), 2)

    details = {
        "scoring_source": "canonical-live-market-packet",
        "fundamental_pillars_available": False,
        "observed_pillars": ["momentum", "market_risk"],
        "momentum_return": round(momentum_base, 6),
        "annualized_volatility": round(annualized_volatility, 6),
        "history_observations": len(closes),
        "scored_at": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "growth_score": 0.0,
        "quality_score": 0.0,
        "profitability_score": 0.0,
        "capital_allocation_score": 0.0,
        "valuation_score": 0.0,
        "momentum_score": momentum_score,
        "risk_score": risk_score,
        "composite_score": composite,
    }, details


class FullyIntegratedMarketPipeline:
    """
    EROS 3.0 Block 23K Fully Integrated Market Pipeline.

    The scoring stage is now evidence-driven: only values derivable from the
    canonical LIVE packet are scored. Unavailable fundamental pillars are
    explicitly recorded as unavailable instead of being fabricated.
    """

    def __init__(self, policy_profile: str = "Institutional") -> None:
        self.orchestrator = UnifiedResearchToDecisionOrchestrator(policy_profile=policy_profile)

    def evaluate_stock_securely(
        self,
        symbol: str,
        ticker_factory: Optional[Callable[[str], Any]] = None,
    ) -> Tuple[Any, MarketDataDecisionResult, Optional[UnifiedInvestmentResult], ConfidenceDecisionTraceRecord]:
        packet, report = ResilientMarketDataProvider.get_validated_market_data(
            symbol,
            ticker_factory=ticker_factory,
        )
        decision = MarketDataDecisionGate.evaluate_decision(report)

        base_confidence = 0.85
        adjusted_conf = max(0.0, base_confidence - decision.confidence_penalty)

        if not decision.allowed_in_scoring:
            trace_record = ConfidenceAuditLogger.create_trace(
                symbol=symbol,
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

        scores, scoring_details = _score_live_market(packet)

        ai_score = AIScoreResult(
            symbol=symbol,
            growth_score=scores["growth_score"],
            quality_score=scores["quality_score"],
            profitability_score=scores["profitability_score"],
            capital_allocation_score=scores["capital_allocation_score"],
            valuation_score=scores["valuation_score"],
            momentum_score=scores["momentum_score"],
            risk_score=scores["risk_score"],
            composite_score=scores["composite_score"],
            breakdown_details={
                **scoring_details,
                "current_price": packet.current_price,
                "previous_close": packet.previous_close,
                "data_state": report.data_state,
                "market_price_source": packet.details.get("source"),
                "market_data_state": report.data_state,
                "confidence_penalty": decision.confidence_penalty,
                "adjusted_confidence": adjusted_conf,
            },
        )

        result = self.orchestrator.evaluate(ai_score, holdings=None, portfolio_weight=0.05)

        trace_record = ConfidenceAuditLogger.create_trace(
            symbol=symbol,
            raw_state=report.data_state,
            valid=report.is_valid,
            directive=decision.directive,
            base_conf=base_confidence,
            penalty=decision.confidence_penalty,
            adj_conf=adjusted_conf,
            composite_score=ai_score.composite_score,
            action=result.final_action,
        )

        return packet, decision, result, trace_record
