from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List


ENGINE_VERSION = "EROS-3.0-BLOCK-68"


@dataclass
class ExecutionIntent:
    symbol: str
    action: str
    quantity: float
    reference_price: float
    limit_price: float
    allocation_pct: float
    confidence: float
    status: str
    execution_allowed: bool
    reasons: List[str]
    warnings: List[str]
    engine_version: str = ENGINE_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EROSExecutionIntentEngine:
    """
    EROS 3.0 Block 68.

    Converts a Block 67 execution-approved portfolio decision
    into a deterministic execution intent.

    IMPORTANT:
    This engine DOES NOT submit orders to a broker.

    It produces an execution intent/order plan only.
    """

    ALLOWED_ACTIONS = {
        "BUY",
        "SELL",
        "HOLD",
    }

    def __init__(
        self,
        max_order_allocation: float = 0.25,
        min_confidence: float = 0.50,
        require_fresh_data: bool = True,
    ) -> None:

        self.max_order_allocation = float(max_order_allocation)
        self.min_confidence = float(min_confidence)
        self.require_fresh_data = bool(require_fresh_data)

    def _reject(
        self,
        symbol: str,
        action: str,
        quantity: float,
        reference_price: float,
        allocation_pct: float,
        confidence: float,
        reasons: List[str],
        warnings: List[str] | None = None,
    ) -> Dict[str, Any]:

        return ExecutionIntent(
            symbol=symbol,
            action=action,
            quantity=quantity,
            reference_price=reference_price,
            limit_price=reference_price,
            allocation_pct=allocation_pct,
            confidence=confidence,
            status="BLOCKED",
            execution_allowed=False,
            reasons=reasons,
            warnings=warnings or [],
        ).to_dict()

    def evaluate(
        self,
        decision: Dict[str, Any],
    ) -> Dict[str, Any]:

        reasons: List[str] = []
        warnings: List[str] = []

        symbol = str(decision.get("symbol", "")).strip()
        action = str(decision.get("final_action", "")).upper().strip()

        quantity = float(decision.get("quantity", 0.0) or 0.0)
        reference_price = float(
            decision.get("price", decision.get("reference_price", 0.0)) or 0.0
        )

        allocation = float(
            decision.get(
                "optimized_weight",
                decision.get("allocation_weight", 0.0),
            ) or 0.0
        )

        confidence = float(decision.get("confidence", 0.0) or 0.0)

        governance = str(
            decision.get("governance", "")
        ).upper().strip()

        execution_approved = bool(
            decision.get("execution_approved", False)
        )

        status = str(
            decision.get("status", "")
        ).upper().strip()

        is_stale = bool(decision.get("is_stale", False))

        # ------------------------------------------------------
        # BASIC IDENTIFIER CHECKS
        # ------------------------------------------------------

        if not symbol:
            reasons.append("MISSING_SYMBOL")

        if action not in self.ALLOWED_ACTIONS:
            reasons.append("INVALID_ACTION")

        # ------------------------------------------------------
        # GOVERNANCE CHECK
        # ------------------------------------------------------

        if governance != "APPROVED":
            reasons.append("GOVERNANCE_NOT_APPROVED")

        if not execution_approved:
            reasons.append("EXECUTION_NOT_APPROVED")

        if status and status != "SUCCESS":
            reasons.append("UPSTREAM_STATUS_NOT_SUCCESS")

        # ------------------------------------------------------
        # MARKET DATA CHECK
        # ------------------------------------------------------

        if self.require_fresh_data and is_stale:
            reasons.append("STALE_MARKET_DATA")

        if reference_price <= 0:
            reasons.append("INVALID_REFERENCE_PRICE")

        # ------------------------------------------------------
        # ORDER CHECKS
        # ------------------------------------------------------

        if action in {"BUY", "SELL"} and quantity <= 0:
            reasons.append("INVALID_ORDER_QUANTITY")

        if allocation < 0:
            reasons.append("NEGATIVE_ALLOCATION")

        if allocation > self.max_order_allocation:
            reasons.append("ORDER_ALLOCATION_LIMIT_BREACH")

        # ------------------------------------------------------
        # CONFIDENCE CHECK
        # ------------------------------------------------------

        if action in {"BUY", "SELL"} and confidence < self.min_confidence:
            reasons.append("CONFIDENCE_BELOW_EXECUTION_THRESHOLD")

        # ------------------------------------------------------
        # HOLD
        # ------------------------------------------------------

        if action == "HOLD":

            return ExecutionIntent(
                symbol=symbol,
                action=action,
                quantity=0.0,
                reference_price=reference_price,
                limit_price=reference_price,
                allocation_pct=allocation,
                confidence=confidence,
                status="HOLD",
                execution_allowed=False,
                reasons=[],
                warnings=["HOLD_ACTION_NO_ORDER_CREATED"],
            ).to_dict()

        # ------------------------------------------------------
        # BLOCK
        # ------------------------------------------------------

        if reasons:

            return self._reject(
                symbol=symbol,
                action=action,
                quantity=quantity,
                reference_price=reference_price,
                allocation_pct=allocation,
                confidence=confidence,
                reasons=reasons,
                warnings=warnings,
            )

        # ------------------------------------------------------
        # DETERMINISTIC LIMIT PRICE
        #
        # The engine intentionally does not introduce
        # an aggressive execution price.
        #
        # The reference price becomes the initial limit price.
        # ------------------------------------------------------

        limit_price = round(reference_price, 2)

        return ExecutionIntent(
            symbol=symbol,
            action=action,
            quantity=round(quantity, 4),
            reference_price=round(reference_price, 2),
            limit_price=limit_price,
            allocation_pct=round(allocation, 6),
            confidence=round(confidence, 6),
            status="APPROVED",
            execution_allowed=True,
            reasons=[],
            warnings=warnings,
        ).to_dict()

    def build_order_plan(
        self,
        portfolio: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        intents: List[Dict[str, Any]] = []

        for decision in portfolio:

            intent = self.evaluate(decision)

            intents.append(intent)

        approved = [
            item
            for item in intents
            if item["execution_allowed"] is True
        ]

        blocked = [
            item
            for item in intents
            if item["status"] == "BLOCKED"
        ]

        hold = [
            item
            for item in intents
            if item["status"] == "HOLD"
        ]

        return {
            "engine_version": ENGINE_VERSION,
            "status": "SUCCESS",
            "broker_submission": False,
            "execution_mode": "INTENT_ONLY",
            "intent_count": len(intents),
            "approved_count": len(approved),
            "blocked_count": len(blocked),
            "hold_count": len(hold),
            "execution_intents": intents,
        }

    def certify(
        self,
        portfolio: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        result = self.build_order_plan(portfolio)

        approved = result["approved_count"]
        blocked = result["blocked_count"]
        hold = result["hold_count"]

        result["certified"] = (
            result["status"] == "SUCCESS"
            and result["broker_submission"] is False
            and blocked == 0
            and hold == 0
            and approved > 0
        )

        result["certification_status"] = (
            "CERTIFIED"
            if result["certified"]
            else "REVIEW_REQUIRED"
        )

        return result
