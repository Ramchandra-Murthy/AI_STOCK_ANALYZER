from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.risk_management.models import PortfolioRiskProfile
from services.risk_management.resilience import RiskResilienceEngine
from services.risk_management.stress_engine import StressTestingEngine


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, float(value)))


@dataclass(frozen=True, slots=True)
class RiskScoreResult:
    symbol: str
    risk_score: float
    volatility: float
    drawdown: float
    liquidity_score: float
    leverage_ratio: float
    resilience_score: float
    stress_impact: float
    details: dict[str, Any]


class RiskScoringEngine:
    """
    EROS 3.0 Risk Scoring Engine.
    Safely handles PortfolioRiskProfile attributes and evaluates institutional risk scores (0-100).
    """

    def __init__(self) -> None:
        self.resilience_engine = RiskResilienceEngine()
        self.stress_engine = StressTestingEngine()

    def evaluate(
        self,
        symbol: str,
        profile: PortfolioRiskProfile | None = None,
    ) -> RiskScoreResult:
        if not profile:
            try:
                profile = PortfolioRiskProfile()
            except Exception:
                profile = None

        # Extract attributes safely with institutional defaults
        volatility = float(getattr(profile, "volatility", 0.20)) if profile else 0.20
        drawdown = float(getattr(profile, "drawdown", 0.15)) if profile else 0.15
        liquidity_score = float(getattr(profile, "liquidity_score", 80.0)) if profile else 80.0
        leverage_ratio = float(getattr(profile, "leverage_ratio", 1.2)) if profile else 1.2

        resilience = 85.0
        try:
            if profile and hasattr(self.resilience_engine, "evaluate"):
                resilience = float(self.resilience_engine.evaluate(profile))
        except Exception:
            pass

        stress_result = {}
        try:
            if hasattr(self.stress_engine, "run_stress_test"):
                stress_result = self.stress_engine.run_stress_test("Market Crash -20%")
            elif callable(self.stress_engine):
                stress_result = self.stress_engine()
        except Exception:
            pass

        stress_impact = float(
            stress_result.get("impact", -0.1) if isinstance(stress_result, dict) else -0.1
        )

        vol_score = _clamp(100.0 - (volatility * 200.0))
        dd_score = _clamp(100.0 - (drawdown * 250.0))
        liq_score = _clamp(liquidity_score)
        lev_score = _clamp(100.0 - max(0.0, (leverage_ratio - 1.0) * 50.0))

        risk_score = round(
            vol_score * 0.25
            + dd_score * 0.25
            + liq_score * 0.20
            + lev_score * 0.15
            + resilience * 0.15,
            2,
        )

        details = {
            "engine_version": "EROS-3.0-BLOCK-15",
            "volatility_score": vol_score,
            "drawdown_score": dd_score,
            "liquidity_component": liq_score,
            "leverage_score": lev_score,
            "resilience_score": resilience,
            "stress_test": stress_result,
        }

        return RiskScoreResult(
            symbol=symbol,
            risk_score=risk_score,
            volatility=volatility,
            drawdown=drawdown,
            liquidity_score=liquidity_score,
            leverage_ratio=leverage_ratio,
            resilience_score=resilience,
            stress_impact=stress_impact,
            details=details,
        )
