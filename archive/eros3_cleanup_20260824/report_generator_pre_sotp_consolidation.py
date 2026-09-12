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
        current_price: float,
        target_price: float,
        sotp_result: SOTPResult,
        investment_thesis: str,
    ) -> EquityResearchReport:
        upside = (target_price - current_price) / max(current_price, 1e-4)

        if upside >= 0.15:
            rec = "BUY"
        elif upside >= 0.05:
            rec = "ACCUMULATE"
        elif upside >= -0.05:
            rec = "HOLD"
        elif upside >= -0.15:
            rec = "REDUCE"
        else:
            rec = "SELL"

        logger.info(f"[{ticker}] Report generated. Recommendation: {rec} (Upside: {upside:.2%})")

        return EquityResearchReport(
            ticker=ticker,
            company_name=company_name,
            current_price=current_price,
            target_price=target_price,
            recommendation=rec,
            investment_thesis=investment_thesis,
            sotp_result=sotp_result,
        )
