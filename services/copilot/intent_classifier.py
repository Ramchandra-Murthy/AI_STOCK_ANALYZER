from __future__ import annotations

import logging
from typing import str

logger = logging.getLogger(__name__)

class IntentClassifier:
    """Classifies analyst natural language prompts into structured EROS institutional intents."""

    @staticmethod
    def classify(prompt: str) -> str:
        prompt_lower = prompt.lower()
        logger.info("Classifying prompt intent: '%s'", prompt)

        if "value" in prompt_lower or "dcf" in prompt_lower or "price" in prompt_lower:
            return "VALUATION"
        elif "report" in prompt_lower or "summarize" in prompt_lower:
            return "REPORTING"
        elif "forecast" in prompt_lower or "scenario" in prompt_lower:
            return "FORECASTING"
        elif "committee" in prompt_lower or "buy" in prompt_lower or "sell" in prompt_lower or "why" in prompt_lower:
            return "COMMITTEE_REASONING"
        elif "portfolio" in prompt_lower or "holdings" in prompt_lower or "risk" in prompt_lower:
            return "PORTFOLIO_INTELLIGENCE"
        elif "workflow" in prompt_lower or "pipeline" in prompt_lower or "run" in prompt_lower:
            return "WORKFLOW"
        else:
            return "GENERAL_INQUIRY"
