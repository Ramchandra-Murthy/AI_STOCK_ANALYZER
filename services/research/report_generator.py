from __future__ import annotations

from dataclasses import dataclass

from core.enums import Status
from core.logger import logger
from services.sotp.sotp_engine import SOTPResult


@dataclass(slots=True, frozen=True)
class EquityResearchReport:
    ticker: str
    company_name: str
    current_price: float
    target_price: float
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
        if current_price is None or target_price is None or current_price <= 0:
            rec = recommendation or "INSUFFICIENT DATA"
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
        elif upside >= 0.15:
            rec = "BUY"
        elif upside >= 0.05:
            rec = "ACCUMULATE"
        elif upside >= -0.05:
            rec = "HOLD"
        elif upside >= -0.15:
            rec = "REDUCE"
        else:
            rec = "SELL"

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
        )
