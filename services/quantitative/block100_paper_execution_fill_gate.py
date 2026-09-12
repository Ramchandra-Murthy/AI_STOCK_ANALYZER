from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

BLOCK_ID = "100"
ENGINE_VERSION = "EROS-3.0-BLOCK-100"

STATUS_CERTIFIED = "CERTIFIED"
STATUS_BLOCKED = "BLOCKED"

EXECUTION_SIMULATED = "SIMULATED"
EXECUTION_PARTIAL = "PARTIAL"
EXECUTION_REJECTED = "REJECTED"
EXECUTION_BLOCKED = "BLOCKED"

ALLOWED_ACTIONS = {"BUY", "SELL", "HOLD"}


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _number(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


class EROSBlock100PaperExecutionFillGate:
    """
    EROS 3.0 Block 100.

    Paper Execution & Fill Validation Gate.

    Block 100 consumes a certified Block 99 execution-intent
    authorization and produces a deterministic paper-execution
    result.

    This block NEVER:
        - submits to a broker
        - creates a live order
        - performs live execution
        - mutates portfolio state
        - mutates valuation
        - mutates performance
        - mutates risk
        - performs optimization
    """

    def __init__(
        self,
        *,
        buy_slippage_bps: float = 5.0,
        sell_slippage_bps: float = 5.0,
        transaction_cost_bps: float = 10.0,
        max_fill_ratio: float = 1.0,
    ) -> None:

        if buy_slippage_bps < 0:
            raise ValueError("buy_slippage_bps must be non-negative")

        if sell_slippage_bps < 0:
            raise ValueError("sell_slippage_bps must be non-negative")

        if transaction_cost_bps < 0:
            raise ValueError("transaction_cost_bps must be non-negative")

        if not 0 < max_fill_ratio <= 1:
            raise ValueError("max_fill_ratio must be between 0 and 1")

        self.buy_slippage_bps = float(buy_slippage_bps)
        self.sell_slippage_bps = float(sell_slippage_bps)
        self.transaction_cost_bps = float(transaction_cost_bps)
        self.max_fill_ratio = float(max_fill_ratio)

        self._execution_records: list[dict[str, Any]] = []

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def certify(
        self,
        *,
        intent: Mapping[str, Any],
        fill_ratio: float = 1.0,
    ) -> dict[str, Any]:

        source = deepcopy(dict(intent))

        validation = self._validate_intent(intent=source)

        if validation["status"] != STATUS_CERTIFIED:
            result = self._blocked_result(
                source,
                validation["reason_code"],
            )
            self._execution_records.append(deepcopy(result))
            return result

        action = _text(source.get("action")).upper()

        if action == "HOLD":
            result = self._blocked_result(
                source,
                "HOLD_NO_PAPER_FILL",
            )
            self._execution_records.append(deepcopy(result))
            return result

        try:
            fill_ratio_value = float(fill_ratio)
        except (TypeError, ValueError):
            return self._blocked_result(
                source,
                "INVALID_FILL_RATIO",
            )

        if not 0 < fill_ratio_value <= 1:
            result = self._blocked_result(
                source,
                "INVALID_FILL_RATIO",
            )
            self._execution_records.append(deepcopy(result))
            return result

        fill_ratio_value = min(
            fill_ratio_value,
            self.max_fill_ratio,
        )

        symbol = _text(source.get("symbol")).upper()

        quantity = _number(
            source.get(
                "quantity",
                source.get("requested_quantity"),
            )
        )

        reference_price = _number(
            source.get(
                "reference_price",
                source.get("price"),
            )
        )

        assert quantity is not None
        assert reference_price is not None

        filled_quantity = round(
            quantity * fill_ratio_value,
            6,
        )

        if filled_quantity <= 0:
            result = self._blocked_result(
                source,
                "ZERO_FILL",
            )
            self._execution_records.append(deepcopy(result))
            return result

        if action == "BUY":
            slippage_bps = self.buy_slippage_bps
            fill_price = reference_price * (1.0 + slippage_bps / 10000.0)
        else:
            slippage_bps = self.sell_slippage_bps
            fill_price = reference_price * (1.0 - slippage_bps / 10000.0)

        fill_price = round(
            fill_price,
            6,
        )

        gross_value = round(
            filled_quantity * fill_price,
            6,
        )

        benchmark_value = filled_quantity * reference_price

        if action == "BUY":
            slippage_value = round(
                gross_value - benchmark_value,
                6,
            )
        else:
            slippage_value = round(
                benchmark_value - gross_value,
                6,
            )

        transaction_cost = round(
            gross_value * self.transaction_cost_bps / 10000.0,
            6,
        )

        if action == "BUY":
            net_value = round(
                gross_value + transaction_cost,
                6,
            )
        else:
            net_value = round(
                gross_value - transaction_cost,
                6,
            )

        fill_status = "FILLED" if fill_ratio_value >= 1.0 else "PARTIAL"

        execution_status = EXECUTION_SIMULATED if fill_status == "FILLED" else EXECUTION_PARTIAL

        execution_id = self._execution_id(
            source,
            fill_ratio_value,
        )

        result = {
            "status": STATUS_CERTIFIED,
            "execution_status": execution_status,
            "execution_id": execution_id,
            "block_id": BLOCK_ID,
            "engine_version": ENGINE_VERSION,
            "created_at": datetime.now(UTC).isoformat(),
            "source_block": "99",
            "source_intent_id": _text(source.get("intent_id")),
            "source_readiness_id": _text(source.get("source_readiness_id")),
            "source_governance_id": _text(source.get("source_governance_id")),
            "symbol": symbol,
            "action": action,
            "requested_quantity": quantity,
            "filled_quantity": filled_quantity,
            "reference_price": reference_price,
            "fill_price": fill_price,
            "gross_value": gross_value,
            "slippage_value": slippage_value,
            "slippage_bps": slippage_bps,
            "transaction_cost": transaction_cost,
            "net_value": net_value,
            "fill_status": fill_status,
            "execution_reason": (
                "Authorized paper execution " "simulated without broker " "submission."
            ),
            "non_mutation_invariant": True,
            "broker_submission": False,
            "live_order_submission": False,
            "execution_blocked": True,
        }

        self._execution_records.append(deepcopy(result))

        return result

    def snapshot(self) -> dict[str, Any]:
        return {
            "block_id": BLOCK_ID,
            "engine_version": ENGINE_VERSION,
            "execution_count": len(self._execution_records),
            "executions": deepcopy(self._execution_records),
        }

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    def _validate_intent(
        self,
        *,
        intent: Mapping[str, Any],
    ) -> dict[str, Any]:

        if not isinstance(
            intent,
            Mapping,
        ):
            return self._validation_blocked("MALFORMED_EXECUTION_INTENT")

        if _text(intent.get("status")) != STATUS_CERTIFIED:
            return self._validation_blocked("SOURCE_STATUS_NOT_CERTIFIED")

        if _text(intent.get("block_id")) != "99":
            return self._validation_blocked("INVALID_SOURCE_BLOCK")

        if not _text(intent.get("intent_id")):
            return self._validation_blocked("MISSING_INTENT_ID")

        authorization_status = _text(intent.get("authorization_status")).upper()

        if authorization_status != "AUTHORIZED":
            return self._validation_blocked("INTENT_NOT_AUTHORIZED")

        intent_status = _text(intent.get("intent_status")).upper()

        if intent_status != "AUTHORIZED":
            return self._validation_blocked("INVALID_INTENT_STATUS")

        if not _text(intent.get("source_readiness_id")):
            return self._validation_blocked("MISSING_SOURCE_READINESS_ID")

        if not _text(intent.get("source_governance_id")):
            return self._validation_blocked("MISSING_SOURCE_GOVERNANCE_ID")

        symbol = _text(intent.get("symbol"))

        if not symbol:
            return self._validation_blocked("MISSING_SYMBOL")

        action = _text(intent.get("action")).upper()

        if action not in ALLOWED_ACTIONS:
            return self._validation_blocked("INVALID_ACTION")

        quantity = _number(
            intent.get(
                "quantity",
                intent.get("requested_quantity"),
            )
        )

        if quantity is None:
            return self._validation_blocked("INVALID_QUANTITY")

        if action in {"BUY", "SELL"}:
            if quantity <= 0:
                return self._validation_blocked("INVALID_QUANTITY")

        reference_price = _number(
            intent.get(
                "reference_price",
                intent.get("price"),
            )
        )

        if reference_price is None:
            return self._validation_blocked("INVALID_REFERENCE_PRICE")

        if action in {"BUY", "SELL"}:
            if reference_price <= 0:
                return self._validation_blocked("INVALID_REFERENCE_PRICE")

        if intent.get("execution_allowed") is not True:
            return self._validation_blocked("EXECUTION_PERMISSION_NOT_GRANTED")

        if intent.get("non_mutation_invariant") is not True:
            return self._validation_blocked("NON_MUTATION_INVARIANT_FAILED")

        if intent.get("broker_submission") is not False:
            return self._validation_blocked("BROKER_SUBMISSION_INVARIANT_FAILED")

        if intent.get("live_order_submission") is not False:
            return self._validation_blocked("LIVE_ORDER_SUBMISSION_INVARIANT_FAILED")

        if intent.get("execution_blocked") is not True:
            return self._validation_blocked("EXECUTION_BLOCK_INVARIANT_FAILED")

        return {"status": STATUS_CERTIFIED}

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _validation_blocked(
        reason: str,
    ) -> dict[str, Any]:

        return {
            "status": STATUS_BLOCKED,
            "reason_code": reason,
        }

    def _blocked_result(
        self,
        intent: Mapping[str, Any],
        reason: str,
    ) -> dict[str, Any]:

        execution_id = self._execution_id(
            intent,
            0.0,
        )

        return {
            "status": STATUS_BLOCKED,
            "execution_status": (EXECUTION_BLOCKED),
            "execution_id": execution_id,
            "block_id": BLOCK_ID,
            "engine_version": ENGINE_VERSION,
            "created_at": datetime.now(UTC).isoformat(),
            "source_block": "99",
            "source_intent_id": _text(intent.get("intent_id")),
            "source_readiness_id": _text(intent.get("source_readiness_id")),
            "source_governance_id": _text(intent.get("source_governance_id")),
            "symbol": _text(intent.get("symbol")).upper(),
            "action": _text(intent.get("action")).upper(),
            "requested_quantity": _number(
                intent.get(
                    "quantity",
                    intent.get("requested_quantity"),
                )
            )
            or 0.0,
            "filled_quantity": 0.0,
            "reference_price": _number(
                intent.get(
                    "reference_price",
                    intent.get("price"),
                )
            )
            or 0.0,
            "fill_price": 0.0,
            "gross_value": 0.0,
            "slippage_value": 0.0,
            "slippage_bps": 0.0,
            "transaction_cost": 0.0,
            "net_value": 0.0,
            "fill_status": "BLOCKED",
            "execution_reason": reason,
            "non_mutation_invariant": True,
            "broker_submission": False,
            "live_order_submission": False,
            "execution_blocked": True,
        }

    @staticmethod
    def _execution_id(
        intent: Mapping[str, Any],
        fill_ratio: float,
    ) -> str:

        raw = "|".join(
            [
                _text(intent.get("intent_id")),
                _text(intent.get("symbol")),
                _text(intent.get("action")),
                str(
                    intent.get(
                        "quantity",
                        intent.get(
                            "requested_quantity",
                            0.0,
                        ),
                    )
                ),
                str(
                    intent.get(
                        "reference_price",
                        intent.get(
                            "price",
                            0.0,
                        ),
                    )
                ),
                str(fill_ratio),
            ]
        )

        digest = sha256(raw.encode("utf-8")).hexdigest()[:20].upper()

        return "EROS100-PAPER-" + digest


__all__ = [
    "EROSBlock100PaperExecutionFillGate",
]
