from __future__ import annotations

import json
import logging
from services.report.models import GeneratedReport
from services.research.models import ResearchResult

logger = logging.getLogger(__name__)


class ReportEngine:
    """Renders structured research results into institutional report formats (Markdown, HTML, JSON)."""

    def generate(self, research: ResearchResult) -> GeneratedReport:
        """Render reports across multiple formats."""
        logger.info("Generating reports for symbol: %s", research.symbol)

        # Markdown Rendering
        md = f"""# Equity Research Report: {research.symbol}

## Executive Summary
* **AI Recommendation**: {research.ai_recommendation}
* **Confidence Score**: {research.confidence_score * 100:.1f}%
* **Economic Moat**: {research.economic_moat}

## Investment Thesis
{research.thesis.summary}
### Key Drivers
"""
        for driver in research.thesis.drivers:
            md += f"* {driver}\n"

        md += f"""
## Risk Summary
* **Primary Risk**: {research.risks.primary_risk}
### Mitigants
"""
        for mitigant in research.risks.mitigants:
            md += f"* {mitigant}\n"

        # HTML Rendering
        html = f"""<div class="equity-report">
  <h1>Equity Research Report: {research.symbol}</h1>
  <div class="summary">
    <p><strong>AI Recommendation:</strong> {research.ai_recommendation}</p>
    <p><strong>Confidence Score:</strong> {research.confidence_score * 100:.1f}%</p>
    <p><strong>Economic Moat:</strong> {research.economic_moat}</p>
  </div>
  <div class="thesis">
    <h2>Investment Thesis</h2>
    <p>{research.thesis.summary}</p>
  </div>
  <div class="risks">
    <h2>Risk Summary</h2>
    <p><strong>Primary Risk:</strong> {research.risks.primary_risk}</p>
  </div>
</div>"""

        # JSON Rendering
        payload = {
            "symbol": research.symbol,
            "ai_recommendation": research.ai_recommendation,
            "confidence_score": research.confidence_score,
            "economic_moat": research.economic_moat,
            "thesis": {
                "summary": research.thesis.summary,
                "drivers": research.thesis.drivers
            },
            "risks": {
                "primary_risk": research.risks.primary_risk,
                "mitigants": research.risks.mitigants
            }
        }
        json_data = json.dumps(payload, indent=2)

        return GeneratedReport(
            symbol=research.symbol,
            markdown_content=md,
            html_content=html,
            json_content=json_data,
            format_type="MULTI-FORMAT"
        )
