from __future__ import annotations

import logging
from typing import Any

from backend.research.evidence.models.research_evidence import ResearchEvidence
from backend.research.evidence.services.evidence_service import EvidenceService
from backend.research.models.research_case import ResearchCase

logger = logging.getLogger(__name__)


class EvidenceAdapter:
    """
    Base adapter for translating core EROS engine outputs
    into structured institutional ResearchEvidence items.
    """

    @staticmethod
    def extract(case: ResearchCase, output: dict[str, Any]) -> list[ResearchEvidence]:
        raise NotImplementedError("Subclasses must implement extract()")


class FundamentalsEvidenceAdapter(EvidenceAdapter):
    """
    Extracts fundamental performance metrics and converts them
    into structured ResearchEvidence.
    """

    @staticmethod
    def extract(case: ResearchCase, metrics: dict[str, Any]) -> list[ResearchEvidence]:
        evidence_items = []

        # Revenue Growth Check
        rev_growth = metrics.get("revenue_growth") or metrics.get("cagr")
        if rev_growth is not None:
            polarity = (
                "POSITIVE"
                if rev_growth > 0.10
                else ("NEUTRAL" if rev_growth >= 0.0 else "NEGATIVE")
            )
            ev = EvidenceService.create_evidence(
                case,
                category="FUNDAMENTAL",
                statement=f"Revenue growth metric recorded at {rev_growth * 100:.1f}%",
                value=rev_growth,
                source="FundamentalsEngine",
                source_type="INTERNAL",
                confidence=0.95,
                materiality=0.85,
                recency=0.95,
                polarity=polarity,
            )
            evidence_items.append(ev)

        # Return on Capital (ROCE / ROE) Check
        roce = metrics.get("roce") or metrics.get("roe")
        if roce is not None:
            polarity = "POSITIVE" if roce > 0.15 else ("NEUTRAL" if roce >= 0.08 else "NEGATIVE")
            ev = EvidenceService.create_evidence(
                case,
                category="QUALITY",
                statement=f"Return on capital evaluated at {roce * 100:.1f}%",
                value=roce,
                source="FundamentalsEngine",
                source_type="INTERNAL",
                confidence=0.95,
                materiality=0.90,
                recency=0.95,
                polarity=polarity,
            )
            evidence_items.append(ev)

        return evidence_items


class ValuationEvidenceAdapter(EvidenceAdapter):
    """
    Extracts valuation model outputs (DCF / Margin of Safety)
    and converts them into structured ResearchEvidence.
    """

    @staticmethod
    def extract(case: ResearchCase, valuation_result: dict[str, Any]) -> list[ResearchEvidence]:
        evidence_items = []

        intrinsic_value = valuation_result.get("intrinsic_value") or valuation_result.get(
            "blended_valuation"
        )
        margin_of_safety = valuation_result.get("margin_of_safety")

        if intrinsic_value is not None:
            ev = EvidenceService.create_evidence(
                case,
                category="VALUATION",
                statement=f"Calculated intrinsic valuation stands at {intrinsic_value:.2f}",
                value=intrinsic_value,
                source="ValuationEngine",
                source_type="INTERNAL",
                confidence=0.90,
                materiality=0.95,
                recency=1.0,
                polarity="POSITIVE" if (margin_of_safety and margin_of_safety > 0) else "NEUTRAL",
            )
            evidence_items.append(ev)

        if margin_of_safety is not None:
            polarity = (
                "POSITIVE"
                if margin_of_safety > 0.15
                else ("NEUTRAL" if margin_of_safety >= 0.0 else "NEGATIVE")
            )
            ev = EvidenceService.create_evidence(
                case,
                category="VALUATION",
                statement=f"Margin of safety calculated at {margin_of_safety * 100:.1f}%",
                value=margin_of_safety,
                source="ValuationEngine",
                source_type="INTERNAL",
                confidence=0.90,
                materiality=0.95,
                recency=1.0,
                polarity=polarity,
            )
            evidence_items.append(ev)

        return evidence_items


class RiskEvidenceAdapter(EvidenceAdapter):
    """
    Extracts risk profile metrics and converts them
    into structured ResearchEvidence.
    """

    @staticmethod
    def extract(case: ResearchCase, risk_metrics: dict[str, Any]) -> list[ResearchEvidence]:
        evidence_items = []

        debt_to_equity = risk_metrics.get("debt_to_equity")
        if debt_to_equity is not None:
            polarity = (
                "POSITIVE"
                if debt_to_equity < 0.5
                else ("NEUTRAL" if debt_to_equity <= 1.0 else "NEGATIVE")
            )
            ev = EvidenceService.create_evidence(
                case,
                category="RISK",
                statement=f"Leverage ratio Debt/Equity evaluated at {debt_to_equity:.2f}",
                value=debt_to_equity,
                source="RiskManagementEngine",
                source_type="INTERNAL",
                confidence=0.95,
                materiality=0.85,
                recency=0.95,
                polarity=polarity,
            )
            evidence_items.append(ev)

        return evidence_items
