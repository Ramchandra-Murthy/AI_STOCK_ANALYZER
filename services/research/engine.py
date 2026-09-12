from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ResearchEngine:
    """Synthesize research only from supplied, validated research inputs."""

    def synthesize(self, valuation: object) -> object:
        """Return a research result for an object carrying a non-empty symbol.

        The legacy engine previously returned hard-coded BUY/confidence/thesis values.
        This compatibility layer now reports insufficient research rather than inventing
        company-specific conclusions.
        """
        symbol = getattr(valuation, "symbol", None) if not isinstance(valuation, str) else valuation
        symbol = symbol.strip().upper() if isinstance(symbol, str) else ""
        if not symbol:
            raise ValueError("symbol must be present for research synthesis")

        logger.info("Research synthesis requested for %s", symbol)

        class ResearchResult:
            def __init__(self, resolved_symbol: str) -> None:
                self.symbol = resolved_symbol
                self.ai_recommendation = "UNAVAILABLE"
                self.confidence_score = 0.0
                self.thesis = (
                    "Research evidence is unavailable; no investment conclusion is issued."
                )
                self.risks = "Insufficient validated research evidence."

        return ResearchResult(symbol)
