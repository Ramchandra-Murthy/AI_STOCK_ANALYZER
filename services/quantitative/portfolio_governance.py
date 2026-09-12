from __future__ import annotations

from typing import Any


class EROSExecutionGovernanceEngine:
    """
    EROS 3.0 Portfolio Decision and Execution Governance Engine.

    Converts an optimized portfolio plus portfolio-risk certification
    into a deterministic execution decision.

    Governance states:

        APPROVED
        REVIEW
        BLOCK

    Execution actions:

        EXECUTE
        HOLD
        BLOCK

    The engine does not modify:
        - market data
        - batch screening
        - portfolio optimization
        - portfolio risk calculations

    It acts as the final governance gate before execution.
    """

    def __init__(
        self,
        policy_profile: str = "Institutional",
        max_risk_score: float = 60.0,
        require_risk_pass: bool = True,
        require_live_data: bool = True,
    ) -> None:

        if not 0 <= max_risk_score <= 100:
            raise ValueError("max_risk_score must be between 0 and 100")

        self.policy_profile = policy_profile
        self.max_risk_score = float(max_risk_score)
        self.require_risk_pass = require_risk_pass
        self.require_live_data = require_live_data

    @staticmethod
    def _status(portfolio: list[dict[str, Any]] | None) -> str:
        if not portfolio:
            return "EMPTY"

        if any(str(item.get("status", "")).upper() == "ERROR" for item in portfolio):
            return "ERROR"

        return "SUCCESS"

    @staticmethod
    def _stale_count(portfolio: list[dict[str, Any]] | None) -> int:

        if not portfolio:
            return 0

        return sum(1 for item in portfolio if bool(item.get("is_stale", False)))

    @staticmethod
    def _total_weight(portfolio: list[dict[str, Any]] | None) -> float:

        if not portfolio:
            return 0.0

        total = 0.0

        for item in portfolio:
            value = item.get(
                "optimized_weight",
                item.get("target_weight", 0.0),
            )

            try:
                total += float(value)
            except (TypeError, ValueError):
                continue

        return total

    def evaluate(
        self,
        portfolio: list[dict[str, Any]] | None,
        risk_result: dict[str, Any] | None,
    ) -> dict[str, Any]:

        blocking_reasons: list[str] = []
        review_reasons: list[str] = []

        portfolio_status = self._status(portfolio)
        stale_count = self._stale_count(portfolio)
        total_weight = self._total_weight(portfolio)

        if not portfolio:
            blocking_reasons.append("EMPTY_PORTFOLIO")

        if portfolio_status == "ERROR":
            blocking_reasons.append("PORTFOLIO_ERRORS")

        if self.require_live_data and stale_count > 0:
            blocking_reasons.append("STALE_MARKET_DATA")

        if total_weight > 1.0 + 1e-9:
            blocking_reasons.append("PORTFOLIO_WEIGHT_OVER_100_PERCENT")

        if risk_result is None:
            blocking_reasons.append("MISSING_RISK_CERTIFICATION")

            risk_governance = "UNKNOWN"
            risk_score = 100.0

        else:

            risk_governance = str(
                risk_result.get(
                    "governance",
                    "UNKNOWN",
                )
            ).upper()

            try:
                risk_score = float(
                    risk_result.get(
                        "risk_score",
                        100.0,
                    )
                )
            except (TypeError, ValueError):
                risk_score = 100.0

            if self.require_risk_pass:
                if risk_governance != "PASS":
                    blocking_reasons.append("RISK_GOVERNANCE_NOT_PASS")

            if risk_score > self.max_risk_score:
                blocking_reasons.append("RISK_SCORE_LIMIT_BREACH")

        if total_weight < 1.0 - 1e-9:
            review_reasons.append("UNALLOCATED_PORTFOLIO_WEIGHT")

        if not blocking_reasons and review_reasons:
            governance = "REVIEW"
            execution_action = "HOLD"

        elif blocking_reasons:
            governance = "BLOCK"
            execution_action = "BLOCK"

        else:
            governance = "APPROVED"
            execution_action = "EXECUTE"

        return {
            "policy_profile": self.policy_profile,
            "governance": governance,
            "execution_action": execution_action,
            "status": "SUCCESS",
            "portfolio_status": portfolio_status,
            "security_count": len(portfolio or []),
            "total_weight": round(total_weight, 8),
            "stale_count": stale_count,
            "risk_governance": risk_governance,
            "risk_score": round(risk_score, 4),
            "blocking_reasons": blocking_reasons,
            "review_reasons": review_reasons,
            "execution_approved": execution_action == "EXECUTE",
        }

    def certify(
        self,
        portfolio: list[dict[str, Any]] | None,
        risk_result: dict[str, Any] | None,
    ) -> dict[str, Any]:

        result = self.evaluate(
            portfolio,
            risk_result,
        )

        return {
            "policy_profile": result["policy_profile"],
            "governance": result["governance"],
            "execution_action": result["execution_action"],
            "status": result["status"],
            "certified": result["execution_approved"],
            "execution_approved": result["execution_approved"],
            "risk_governance": result["risk_governance"],
            "risk_score": result["risk_score"],
            "security_count": result["security_count"],
            "total_weight": result["total_weight"],
            "blocking_reasons": result["blocking_reasons"],
            "review_reasons": result["review_reasons"],
        }


__all__ = [
    "EROSExecutionGovernanceEngine",
]
