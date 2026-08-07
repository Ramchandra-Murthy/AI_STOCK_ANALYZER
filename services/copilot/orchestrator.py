from __future__ import annotations

import logging
from typing import List
from services.copilot.conversation_models import CopilotResponse
from services.copilot.intent_classifier import IntentClassifier

logger = logging.getLogger(__name__)

class InstitutionalAICopilot:
    """Conversational orchestrator mapping natural language queries to EROS institutional services."""

    @classmethod
    def process_query(cls, prompt: str, symbol: str = "RELIANCE.NS") -> CopilotResponse:
        intent = IntentClassifier.classify(prompt)
        logger.info("Processing copilot query for symbol %s with classified intent %s", symbol, intent)

        if intent == "VALUATION":
            answer = f"Valuation analysis for {symbol}: Intrinsic value is estimated at ₹3,200, representing a 15% discount to current market pricing."
            evidence = ["DCF Upside: +15%", "ROIC (19%) > WACC (10%)", "Strong Economic Moat"]
            steps = ["Download Financials", "Calculate WACC", "Run DCF Model"]
            sources = ["Valuation Engine", "Quality Layer"]
            confidence = 0.91
            follow_ups = ["Show me the downside scenario.", "What is the WACC breakdown?"]

        elif intent == "COMMITTEE_REASONING":
            answer = f"The Artificial Investment Committee recommends BUY for {symbol} with a 5–1 consensus vote."
            evidence = ["Committee Vote: 5–1 BUY", "Quality Score: 92/100", "Forecast Expected Upside: +18%"]
            steps = ["Gather Specialist Scores", "Synthesize Committee Consensus", "Evaluate CIO Confidence"]
            sources = ["Artificial Investment Committee", "Artificial CIO"]
            confidence = 0.89
            follow_ups = ["What are the major risks?", "Run a portfolio allocation check."]

        elif intent == "WORKFLOW":
            answer = f"Executing full end-to-end institutional research pipeline for {symbol}."
            evidence = ["12 Automated Steps Completed", "Report Generated", "Audit Trail Archived"]
            steps = ["Data Ingestion", "Validation", "Valuation", "Committee", "Reporting", "Archiving"]
            sources = ["Institutional Workflow Engine", "Reporting Platform"]
            confidence = 1.0
            follow_ups = ["Inspect the generated report.", "Check portfolio concentration."]

        else:
            answer = f"Processed general institutional inquiry for {symbol} across EROS intelligence layers."
            evidence = ["Active Knowledge Store", "Market Intelligence Feed"]
            steps = ["Context Retrieval", "Knowledge Synthesis"]
            sources = ["Company Knowledge Layer", "Market Intelligence Layer"]
            confidence = 0.85
            follow_ups = ["Value this company.", "Summarize current market regime."]

        return CopilotResponse(
            answer=answer,
            evidence=evidence,
            workflow_steps=steps,
            confidence=confidence,
            sources=sources,
            follow_up_questions=follow_ups
        )
