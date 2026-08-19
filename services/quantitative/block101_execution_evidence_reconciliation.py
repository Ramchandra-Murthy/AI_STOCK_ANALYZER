from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from numbers import Number
from typing import Any, Dict, Mapping


STATUS_CERTIFIED = "CERTIFIED"
STATUS_BLOCKED = "BLOCKED"

RECONCILED = "RECONCILED"
EXCEPTION = "EXCEPTION"
BLOCKED = "BLOCKED"

ENGINE_VERSION = "EROS-3.0-BLOCK-101"


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _number(value: Any):
    if isinstance(value, bool):
        return None

    if isinstance(value, Number):
        return float(value)

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _id(prefix: str, payload: Mapping[str, Any]) -> str:
    raw = repr(sorted(payload.items())).encode("utf-8")
    digest = sha256(raw).hexdigest().upper()[:20]
    return f"{prefix}-{digest}"


class EROSBlock101ExecutionEvidenceReconciliationGate:
    """
    EROS 3.0 Block 101

    Paper Execution Evidence Reconciliation Gate.

    Consumes certified Block 100 paper-execution evidence and
    deterministically reconciles execution, fill, quantity, price,
    value, cost, and lineage evidence.

    This block performs no portfolio mutation, no order creation,
    no broker submission, and no live execution.
    """

    def __init__(self) -> None:
        self._reconciliation = []

    @property
    def engine_version(self) -> str:
        return ENGINE_VERSION

    def certify(
        self,
        *,
        execution: Mapping[str, Any],
    ) -> Dict[str, Any]:

        source = deepcopy(dict(execution))

        validation = self._validate(source)

        if validation["status"] != STATUS_CERTIFIED:
            result = self._blocked(
                source,
                validation["reason_code"],
            )
            self._reconciliation.append(deepcopy(result))
            return result

        result = self._reconcile(source)

        self._reconciliation.append(deepcopy(result))
        return result

    def evaluate(
        self,
        *,
        execution: Mapping[str, Any],
    ) -> Dict[str, Any]:
        return self.certify(execution=execution)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "status": STATUS_CERTIFIED,
            "block_id": "101",
            "engine_version": ENGINE_VERSION,
            "reconciliation": deepcopy(
                self._reconciliation
            ),
        }

    def _validate(
        self,
        execution: Mapping[str, Any],
    ) -> Dict[str, Any]:

        if not isinstance(execution, Mapping):
            return self._invalid("MALFORMED_EXECUTION")

        if _text(execution.get("status")) != STATUS_CERTIFIED:
            return self._invalid(
                "SOURCE_STATUS_NOT_CERTIFIED"
            )

        if _text(execution.get("block_id")) != "100":
            return self._invalid(
                "INVALID_SOURCE_BLOCK"
            )

        if not _text(execution.get("execution_id")):
            return self._invalid(
                "MISSING_EXECUTION_ID"
            )

        if not _text(execution.get("source_intent_id")):
            return self._invalid(
                "MISSING_SOURCE_INTENT_ID"
            )

        execution_status = _text(
            execution.get("execution_status")
        ).upper()

        if execution_status not in {
            "SIMULATED",
            "PARTIAL",
            "BLOCKED",
        }:
            return self._invalid(
                "INVALID_EXECUTION_STATUS"
            )

        fill_status = _text(
            execution.get("fill_status")
        ).upper()

        if fill_status not in {
            "FILLED",
            "PARTIAL",
            "BLOCKED",
        }:
            return self._invalid(
                "INVALID_FILL_STATUS"
            )

        requested = _number(
            execution.get("requested_quantity")
        )

        filled = _number(
            execution.get("filled_quantity")
        )

        if requested is None or requested < 0:
            return self._invalid(
                "INVALID_REQUESTED_QUANTITY"
            )

        if filled is None or filled < 0:
            return self._invalid(
                "INVALID_FILLED_QUANTITY"
            )

        if filled > requested:
            return self._invalid(
                "FILLED_QUANTITY_EXCEEDS_REQUESTED"
            )

        reference_price = _number(
            execution.get("reference_price")
        )

        if reference_price is None:
            return self._invalid(
                "MISSING_REFERENCE_PRICE"
            )

        fill_price = _number(
            execution.get("fill_price")
        )

        if fill_status == "FILLED":
            if fill_price is None or fill_price <= 0:
                return self._invalid(
                    "INVALID_FILLED_PRICE"
                )

            if filled != requested:
                return self._invalid(
                    "FILLED_QUANTITY_MISMATCH"
                )

        if fill_status == "PARTIAL":
            if not (
                0 < filled < requested
            ):
                return self._invalid(
                    "INVALID_PARTIAL_QUANTITY"
                )

            if fill_price is None or fill_price <= 0:
                return self._invalid(
                    "INVALID_PARTIAL_PRICE"
                )

        if fill_status == "BLOCKED":
            if filled != 0:
                return self._invalid(
                    "BLOCKED_EXECUTION_HAS_FILL"
                )

        required_numeric = (
            "gross_value",
            "slippage_value",
            "slippage_bps",
            "transaction_cost",
            "net_value",
        )

        for field in required_numeric:
            if _number(execution.get(field)) is None:
                return self._invalid(
                    f"MISSING_{field.upper()}"
                )

        if execution.get(
            "non_mutation_invariant"
        ) is not True:
            return self._invalid(
                "NON_MUTATION_INVARIANT_FAILED"
            )

        if execution.get(
            "broker_submission"
        ) is not False:
            return self._invalid(
                "BROKER_SUBMISSION_INVARIANT_FAILED"
            )

        if execution.get(
            "live_order_submission"
        ) is not False:
            return self._invalid(
                "LIVE_ORDER_SUBMISSION_INVARIANT_FAILED"
            )

        if execution.get(
            "execution_blocked"
        ) is not True:
            return self._invalid(
                "EXECUTION_BLOCK_INVARIANT_FAILED"
            )

        return {
            "status": STATUS_CERTIFIED
        }

    def _reconcile(
        self,
        source: Mapping[str, Any],
    ) -> Dict[str, Any]:

        execution_status = _text(
            source.get("execution_status")
        ).upper()

        fill_status = _text(
            source.get("fill_status")
        ).upper()

        requested = float(
            source["requested_quantity"]
        )

        filled = float(
            source["filled_quantity"]
        )

        fill_ratio = (
            filled / requested
            if requested > 0
            else 0.0
        )

        quantity_reconciled = (
            filled <= requested
            and (
                fill_status != "FILLED"
                or filled == requested
            )
        )

        price_reconciled = (
            fill_status == "BLOCKED"
            or _number(source.get("fill_price")) is not None
        )

        value_reconciled = all(
            _number(source.get(field)) is not None
            for field in (
                "gross_value",
                "net_value",
            )
        )

        cost_reconciled = all(
            _number(source.get(field)) is not None
            for field in (
                "slippage_value",
                "slippage_bps",
                "transaction_cost",
            )
        )

        lineage_reconciled = (
            _text(source.get("block_id")) == "100"
            and bool(
                _text(source.get("execution_id"))
            )
            and bool(
                _text(source.get("source_intent_id"))
            )
        )

        if execution_status == "BLOCKED":
            reconciliation_status = BLOCKED
        elif all(
            (
                quantity_reconciled,
                price_reconciled,
                value_reconciled,
                cost_reconciled,
                lineage_reconciled,
            )
        ):
            reconciliation_status = RECONCILED
        else:
            reconciliation_status = EXCEPTION

        payload = {
            "execution_id": source.get(
                "execution_id"
            ),
            "source_intent_id": source.get(
                "source_intent_id"
            ),
            "reconciliation_status":
                reconciliation_status,
        }

        return {
            "status": STATUS_CERTIFIED,
            "reconciliation_status":
                reconciliation_status,
            "reconciliation_id": _id(
                "EROS101-STRESS-RECONCILIATION",
                payload,
            ),
            "block_id": "101",
            "engine_version": ENGINE_VERSION,
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),

            "source_block": "100",
            "source_execution_id":
                source.get("execution_id"),
            "source_intent_id":
                source.get("source_intent_id"),

            "symbol": source.get("symbol"),
            "action": source.get("action"),

            "requested_quantity": requested,
            "filled_quantity": filled,
            "fill_ratio": fill_ratio,

            "reference_price":
                source.get("reference_price"),
            "fill_price":
                source.get("fill_price"),

            "gross_value":
                source.get("gross_value"),
            "slippage_value":
                source.get("slippage_value"),
            "slippage_bps":
                source.get("slippage_bps"),
            "transaction_cost":
                source.get("transaction_cost"),
            "net_value":
                source.get("net_value"),

            "fill_status": fill_status,
            "execution_status": execution_status,

            "reconciliation_reason":
                "Paper execution evidence reconciled."
                if reconciliation_status == RECONCILED
                else "Paper execution evidence requires review.",

            "quantity_reconciled":
                quantity_reconciled,
            "price_reconciled":
                price_reconciled,
            "value_reconciled":
                value_reconciled,
            "cost_reconciled":
                cost_reconciled,
            "lineage_reconciled":
                lineage_reconciled,

            "non_mutation_invariant":
                True,
            "broker_submission":
                False,
            "live_order_submission":
                False,
            "execution_blocked":
                True,
        }

    @staticmethod
    def _invalid(
        reason: str,
    ) -> Dict[str, Any]:

        return {
            "status": STATUS_BLOCKED,
            "reason_code": reason,
        }

    @staticmethod
    def _blocked(
        source: Mapping[str, Any],
        reason: str,
    ) -> Dict[str, Any]:

        return {
            "status": STATUS_BLOCKED,
            "reconciliation_status": BLOCKED,
            "reconciliation_id": _id(
                "EROS101-STRESS-RECONCILIATION",
                {
                    "execution_id":
                        source.get("execution_id"),
                    "reason": reason,
                },
            ),
            "block_id": "101",
            "engine_version": ENGINE_VERSION,
            "source_block": "100",
            "source_execution_id":
                source.get("execution_id"),
            "source_intent_id":
                source.get("source_intent_id"),
            "reconciliation_reason": reason,
            "non_mutation_invariant": True,
            "broker_submission": False,
            "live_order_submission": False,
            "execution_blocked": True,
        }
