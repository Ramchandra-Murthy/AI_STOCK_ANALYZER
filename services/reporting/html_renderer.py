from __future__ import annotations

from services.reporting.report_models import InstitutionalResearchReport

class ReportRenderer:
    """Multi-format renderer for institutional research reports (Markdown and HTML)."""

    @staticmethod
    def to_markdown(report: InstitutionalResearchReport) -> str:
        return f"""# EROS Institutional Research Report: {report.symbol}
**Recommendation**: {report.recommendation}  
**Timestamp**: {report.timestamp}

## Executive Summary
{report.executive_summary}

## Valuation Analysis
{report.valuation_section}

## Business Quality
{report.quality_section}

## Risk Assessment
{report.risk_section}

## Forecasting & Scenarios
{report.forecast_section}

## Portfolio Context
{report.portfolio_section}

## Appendix & Audit Trail
{report.appendix}
"""

    @staticmethod
    def to_html(report: InstitutionalResearchReport) -> str:
        md = ReportRenderer.to_markdown(report)
        return f"<html><head><title>EROS Report - {report.symbol}</title></head><body><pre>{md}</pre></body></html>"
