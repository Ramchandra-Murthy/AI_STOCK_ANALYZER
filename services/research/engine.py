from __future__ import annotations

import logging
from typing import Any, Mapping, Optional

from services.research.models import InvestmentThesis, ResearchResult, RiskSummary

logger = logging.getLogger(__name__)


class ResearchEngine:
    """Evidence-bound research synthesizer.

    This layer does not manufacture an investment thesis from a symbol alone.
    Callers should provide an evidence packet; missing evidence remains explicit.
    """

    def synthesize(self, valuation: Any, evidence: Optional[Mapping[str, Any]] = None) -> ResearchResult:
        if hasattr(valuation, "symbol"):
            symbol = valuation.symbol
        elif isinstance(valuation, str):
            symbol = valuation
        else:
            symbol = getattr(valuation, "symbol", "UNKNOWN")

        packet = dict(evidence or {})
        observed = packet.get("observed_pillars", [])
        data_state = packet.get("market_data_state", "UNKNOWN")
        fundamental_available = bool(packet.get("fundamental_pillars_available", False))

        drivers = []
        if "momentum" in observed:
            drivers.append("Observed market momentum")
        if "market_risk" in observed:
            drivers.append("Observed market-risk conditions")
        if fundamental_available:
            drivers.append("Observed fundamental evidence")

        if not drivers:
            thesis = InvestmentThesis(
                summary="Insufficient evidence to form an investment thesis.",
                drivers=[],
            )
        else:
            thesis = InvestmentThesis(
                summary=f"Evidence-based assessment using {', '.join(observed)}; market data state: {data_state}.",
                drivers=drivers,
            )

        primary_risk = (
            "Fundamental evidence unavailable."
            if not fundamental_available
            else "Investment risk remains dependent on the supplied evidence."
        )
        risks = RiskSummary(primary_risk=primary_risk)

        # ResearchEngine reports evidence quality; it does not invent a confidence value.
        evidence_count = len(observed) + int(fundamental_available)
        confidence = min(1.0, evidence_count / 4.0)
        recommendation = "HOLD" if evidence_count == 0 else "RESEARCH_ONLY"

        logger.info("Synthesizing evidence-bound research for %s", symbol)
        return ResearchResult(
            symbol=symbol,
            thesis=thesis,
            risks=risks,
            economic_moat="UNASSESSED" if not fundamental_available else "ASSESSED",
            ai_recommendation=recommendation,
            confidence_score=confidence,
        )
