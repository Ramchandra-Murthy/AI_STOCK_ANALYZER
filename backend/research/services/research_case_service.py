from __future__ import annotations

import logging

from backend.research.models.research_case import ResearchCase

logger = logging.getLogger(__name__)


class ResearchCaseService:
    """
    Coordinates creation and lifecycle management of
    institutional research cases.
    """

    @staticmethod
    def create_case(
        symbol: str,
        objective: str,
        research_type: str = "Long-Term Equity",
        analyst: str = "EROS",
    ) -> ResearchCase:
        if not symbol:
            raise ValueError("symbol is required")
        case_id = f"RESEARCH-{symbol}-2026"
        case = ResearchCase(
            case_id=case_id,
            symbol=symbol,
            research_type=research_type,
            objective=objective,
            analyst=analyst,
            status="OPEN",
        )
        logger.info(
            "Created research case %s for %s",
            case.case_id,
            symbol,
        )
        return case

    @staticmethod
    def add_evidence(
        case: ResearchCase,
        evidence: str,
    ) -> ResearchCase:
        if not evidence:
            raise ValueError("evidence is required")
        if evidence not in case.evidence:
            case.evidence.append(evidence)
        case.updated_at = __import__("datetime").datetime.utcnow().isoformat()
        return case

    @staticmethod
    def update_thesis(
        case: ResearchCase,
        thesis: str,
    ) -> ResearchCase:
        case.investment_thesis = thesis
        case.updated_at = __import__("datetime").datetime.utcnow().isoformat()
        return case

    @staticmethod
    def close_case(
        case: ResearchCase,
        conclusion: str,
    ) -> ResearchCase:
        case.conclusion = conclusion
        case.status = "CLOSED"
        case.updated_at = __import__("datetime").datetime.utcnow().isoformat()
        logger.info(
            "Closed research case %s",
            case.case_id,
        )
        return case
