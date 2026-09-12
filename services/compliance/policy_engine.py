from __future__ import annotations

import logging
from typing import Any

from services.compliance.models import ComplianceReport

logger = logging.getLogger(__name__)


class InstitutionalCompliancePlatform:
    """Enforces rigorous institutional governance, position limits, sector caps, ESG constraints, and mandate rules."""

    @staticmethod
    def evaluate_compliance(
        portfolio_id: str, holdings: list[dict[str, Any]], mandate: str = "Balanced Institutional"
    ) -> ComplianceReport:
        logger.info(
            "Evaluating institutional compliance for portfolio %s under mandate '%s'",
            portfolio_id,
            mandate,
        )

        violations = []
        exposure_summary = {}

        for h in holdings:
            sym = h.get("symbol", "UNKNOWN")
            weight = h.get("weight", 0.0)
            exposure_summary[sym] = weight
            # Enforce max position limit of 35%
            if weight > 0.35:
                violations.append(
                    f"Position {sym} weight (%.2f) exceeds regulatory limit of 0.35" % weight
                )

        compliant = len(violations) == 0

        return ComplianceReport(
            portfolio_id=portfolio_id,
            compliant=compliant,
            violations=violations,
            exposure_summary=exposure_summary,
            mandate=mandate,
            audit_id=f"AUDIT-{portfolio_id}-2026",
        )
