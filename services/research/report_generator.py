from __future__ import annotations

from dataclasses import dataclass

from core.enums import Status
from core.logger import logger
from services.sotp.sotp_engine import SOTPResult


@dataclass(slots=True, frozen=True)
class EquityResearchReport:
    ticker: str
    company_name: str
    current_price: float | None
    target_price: float | None
    recommendation: str
    investment_thesis: str
    sotp_result: SOTPResult
    status: Status = Status.OK


class ResearchReportGenerator:
    """Compiles structured institutional research reports from valuation outputs."""

    @staticmethod
    def generate_report(
        ticker: str,
        company_name: str,
        current_price: float | None,
        target_price: float | None,
        sotp_result: SOTPResult,
        investment_thesis: str,
        recommendation: str | None = None,
    ) -> EquityResearchReport:
        """Build a report without creating a second investment recommendation.

        The recommendation supplied by the authoritative decision layer is
        preserved. Missing or unusable recommendation evidence is surfaced as
        INSUFFICIENT DATA rather than being inferred from valuation upside.
        """
        if current_price is None or target_price is None or current_price <= 0:
            rec = (
                recommendation
                if recommendation and recommendation not in ("N/A", "UNKNOWN")
                else "INSUFFICIENT DATA"
            )
            return EquityResearchReport(
                ticker=ticker,
                company_name=company_name,
                current_price=current_price,
                target_price=target_price,
                recommendation=rec,
                investment_thesis=investment_thesis,
                sotp_result=sotp_result,
                status=Status.ERROR,
            )

        upside = (target_price - current_price) / current_price

        if recommendation and recommendation not in ("N/A", "UNKNOWN"):
            rec = recommendation
            status = Status.OK
        else:
            rec = "INSUFFICIENT DATA"
            status = Status.ERROR

        logger.info(
            f"[{ticker}] Report generated. Recommendation: {rec} (Upside: {upside:.2%})"
        )

        return EquityResearchReport(
            ticker=ticker,
            company_name=company_name,
            current_price=current_price,
            target_price=target_price,
            recommendation=rec,
            investment_thesis=investment_thesis,
            sotp_result=sotp_result,
            status=status,
        )
