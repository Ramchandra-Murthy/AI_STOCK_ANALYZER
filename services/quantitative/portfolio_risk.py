from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PortfolioRiskLimits:
    max_position_weight: float = 0.25
    max_top3_weight: float = 0.75
    max_hhi: float = 0.25
    max_stale_positions: int = 0
    max_error_positions: int = 0
    min_cash_weight: float = 0.0


class EROSPortfolioRiskEngine:
    """
    EROS 3.0 Portfolio Risk and Governance Engine.

    Evaluates an already-optimized portfolio without changing
    the portfolio optimizer or market-data pipeline.

    Governance states:

        PASS
        REVIEW
        BLOCK

    The engine is deliberately deterministic and uses only
    information supplied in the portfolio records.
    """

    def __init__(
        self,
        policy_profile: str = "Institutional",
        limits: PortfolioRiskLimits | None = None,
    ) -> None:

        self.policy_profile = policy_profile
        self.limits = limits or PortfolioRiskLimits()

        if not 0 <= self.limits.max_position_weight <= 1:
            raise ValueError("max_position_weight must be between 0 and 1")

        if not 0 <= self.limits.max_top3_weight <= 1:
            raise ValueError("max_top3_weight must be between 0 and 1")

        if not 0 <= self.limits.max_hhi <= 1:
            raise ValueError("max_hhi must be between 0 and 1")

        if self.limits.max_stale_positions < 0:
            raise ValueError("max_stale_positions must be >= 0")

        if self.limits.max_error_positions < 0:
            raise ValueError("max_error_positions must be >= 0")

    @staticmethod
    def _weight(item: dict[str, Any]) -> float:
        value = item.get("optimized_weight", item.get("target_weight", 0.0))

        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def calculate_metrics(
        self,
        portfolio: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:

        if not portfolio:
            return {
                "security_count": 0,
                "total_weight": 0.0,
                "cash_weight": 1.0,
                "max_position_weight": 0.0,
                "top3_weight": 0.0,
                "hhi": 0.0,
                "stale_positions": 0,
                "error_positions": 0,
                "negative_positions": 0,
                "overweight_positions": 0,
            }

        weights = [self._weight(item) for item in portfolio]

        total_weight = sum(weights)

        positive_weights = sorted(
            [w for w in weights if w > 0],
            reverse=True,
        )

        max_position = max(positive_weights, default=0.0)

        top3_weight = sum(positive_weights[:3])

        hhi = sum(w * w for w in positive_weights)

        stale_positions = sum(1 for item in portfolio if bool(item.get("is_stale", False)))

        error_positions = sum(
            1 for item in portfolio if str(item.get("status", "")).upper() == "ERROR"
        )

        negative_positions = sum(1 for w in weights if w < 0)

        overweight_positions = sum(1 for w in weights if w > self.limits.max_position_weight)

        cash_weight = max(0.0, 1.0 - total_weight)

        return {
            "security_count": len(portfolio),
            "total_weight": total_weight,
            "cash_weight": cash_weight,
            "max_position_weight": max_position,
            "top3_weight": top3_weight,
            "hhi": hhi,
            "stale_positions": stale_positions,
            "error_positions": error_positions,
            "negative_positions": negative_positions,
            "overweight_positions": overweight_positions,
        }

    def evaluate(
        self,
        portfolio: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:

        metrics = self.calculate_metrics(portfolio)

        blocking_reasons: list[str] = []
        review_reasons: list[str] = []

        total_weight = metrics["total_weight"]

        if metrics["negative_positions"] > 0:
            blocking_reasons.append("NEGATIVE_POSITION")

        if metrics["error_positions"] > self.limits.max_error_positions:
            blocking_reasons.append("ERROR_POSITIONS")

        if metrics["overweight_positions"] > 0:
            blocking_reasons.append("POSITION_LIMIT_BREACH")

        if metrics["hhi"] > self.limits.max_hhi:
            blocking_reasons.append("CONCENTRATION_HHI_BREACH")

        if metrics["top3_weight"] > self.limits.max_top3_weight:
            blocking_reasons.append("TOP3_CONCENTRATION_BREACH")

        if metrics["stale_positions"] > self.limits.max_stale_positions:
            blocking_reasons.append("STALE_DATA")

        if total_weight > 1.0 + 1e-9:
            blocking_reasons.append("TOTAL_WEIGHT_OVER_100_PERCENT")

        if metrics["cash_weight"] < self.limits.min_cash_weight - 1e-9:
            blocking_reasons.append("MINIMUM_CASH_BREACH")

        if total_weight < 1.0 - 1e-9:
            review_reasons.append("UNALLOCATED_CASH")

        if not portfolio:
            review_reasons.append("EMPTY_PORTFOLIO")

        if blocking_reasons:
            governance = "BLOCK"
        elif review_reasons:
            governance = "REVIEW"
        else:
            governance = "PASS"

        risk_score = 0.0

        risk_score += min(metrics["hhi"] * 100.0, 40.0)
        risk_score += min(metrics["max_position_weight"] * 40.0, 40.0)
        risk_score += min(metrics["stale_positions"] * 10.0, 20.0)

        risk_score = min(100.0, risk_score)

        return {
            "policy_profile": self.policy_profile,
            "governance": governance,
            "risk_score": round(risk_score, 4),
            "metrics": metrics,
            "blocking_reasons": blocking_reasons,
            "review_reasons": review_reasons,
            "status": "SUCCESS",
        }

    def certify(
        self,
        portfolio: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:

        result = self.evaluate(portfolio)

        return {
            "policy_profile": result["policy_profile"],
            "governance": result["governance"],
            "risk_score": result["risk_score"],
            "status": result["status"],
            "certified": result["governance"] == "PASS",
            "blocking_reasons": result["blocking_reasons"],
            "review_reasons": result["review_reasons"],
            "metrics": result["metrics"],
        }


__all__ = [
    "PortfolioRiskLimits",
    "EROSPortfolioRiskEngine",
]
