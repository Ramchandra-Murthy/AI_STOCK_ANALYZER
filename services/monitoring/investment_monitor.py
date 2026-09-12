from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from services.scoring.block18_orchestrator import UnifiedInvestmentResult


@dataclass(frozen=True, slots=True)
class InvestmentMonitoringSnapshot:
    symbol: str
    composite_score: float
    rating: str
    risk_score: float
    valuation_score: float
    momentum_score: float
    research_score: float
    confidence_score: float
    moat_score: float
    portfolio_weight: float
    action: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    details: dict[str, Any] = field(default_factory=dict)


class InvestmentMonitor:
    """
    EROS 3.0 Block 20A Investment Monitor.
    Captures standardized monitoring snapshots from UnifiedInvestmentResult.
    """

    @staticmethod
    def capture_snapshot(result: UnifiedInvestmentResult) -> InvestmentMonitoringSnapshot:
        dec = result.decision
        res = result.research
        conf = result.confidence

        return InvestmentMonitoringSnapshot(
            symbol=result.symbol,
            composite_score=dec.composite_score,
            rating=dec.rating,
            risk_score=dec.risk_score,
            valuation_score=dec.valuation_score,
            momentum_score=dec.momentum_score,
            research_score=res.research_score,
            confidence_score=conf.overall_confidence * 100.0,
            moat_score=res.moat_score,
            portfolio_weight=dec.target_weight,
            action=result.final_action,
            details={
                "engine_version": "EROS-3.0-BLOCK-20A",
                "policy_profile": dec.details.get("policy_profile", "Institutional"),
            },
        )
