from __future__ import annotations

"""
EROS 3.0 - Block 88
Execution Audit & Reconciliation Engine

Design:
    Block 87 Execution Bridge
        -> order generation / controlled paper execution
        -> Block 88 audit + reconciliation

Block 88 NEVER upgrades a blocked decision. It only:
    - reconciles approved execution results
    - detects exceptions
    - produces a deterministic audit certificate
    - preserves traceability from decision -> order -> fill -> TCA

No broker/live order submission is performed by this module.
"""

import hashlib
import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

ENGINE_VERSION = "EROS-3.0-BLOCK-88"
AUDIT_SCHEMA_VERSION = "1.0"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        result = value.to_dict()
        return dict(result) if isinstance(result, Mapping) else {}
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {}


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _number(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def _hash_payload(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest().upper()


def _first(payload: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return default


@dataclass(frozen=True)
class ExecutionAuditRecord:
    audit_id: str
    audit_schema_version: str
    engine_version: str
    timestamp_utc: str

    decision_id: str
    symbol: str
    requested_action: str
    final_action: str

    execution_status: str
    execution_allowed: bool

    expected_order_count: int
    actual_order_count: int
    expected_fill_count: int
    actual_fill_count: int

    expected_quantity: float
    actual_quantity: float
    quantity_variance: float

    expected_notional: float
    actual_notional: float
    notional_variance: float

    expected_transaction_cost: float
    actual_transaction_cost: float
    transaction_cost_variance: float

    reconciliation_status: str
    exception_count: int
    exceptions: list[str] = field(default_factory=list)

    broker_submission: bool = False
    live_order_submission: bool = False
    paper_execution: bool = True

    source_order_ids: list[str] = field(default_factory=list)
    source_fill_ids: list[str] = field(default_factory=list)

    audit_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Block88AuditCertificate:
    status: str
    reconciliation_status: str
    audit_id: str
    decision_id: str
    symbol: str
    exception_count: int
    audit_hash: str
    execution_allowed: bool
    broker_submission: bool
    live_order_submission: bool
    certificate_hash: str
    created_at_utc: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EROSBlock88AuditReconciliationEngine:
    """
    Institutional execution audit and reconciliation layer.

    Input may be:
      - Block 87 result object
      - Block 87 result dict
      - compatible order/fill/TCA dictionaries

    The engine is deliberately fail-closed.
    """

    def __init__(
        self,
        quantity_tolerance: float = 1e-9,
        notional_tolerance: float = 1.0,
        cost_tolerance: float = 1.0,
    ) -> None:
        self.quantity_tolerance = max(float(quantity_tolerance), 0.0)
        self.notional_tolerance = max(float(notional_tolerance), 0.0)
        self.cost_tolerance = max(float(cost_tolerance), 0.0)

    @staticmethod
    def _decision(payload: Mapping[str, Any]) -> dict[str, Any]:
        value = _first(payload, "decision", "control_decision", default={})
        return _dict(value)

    @staticmethod
    def _orders(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
        value = _first(payload, "orders", "execution_orders", "order_plan", default=[])
        return [_dict(x) for x in _list(value) if _dict(x)]

    @staticmethod
    def _fills(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
        value = _first(payload, "fills", "paper_fills", "executions", default=[])
        return [_dict(x) for x in _list(value) if _dict(x)]

    @staticmethod
    def _tca(payload: Mapping[str, Any]) -> dict[str, Any]:
        return _dict(_first(payload, "tca", "transaction_cost_analysis", default={}))

    @staticmethod
    def _decision_id(decision: Mapping[str, Any]) -> str:
        return _text(
            _first(
                decision,
                "decision_id",
                "control_decision_id",
                "id",
                default="UNKNOWN-DECISION",
            )
        )

    @staticmethod
    def _symbol(decision: Mapping[str, Any], payload: Mapping[str, Any]) -> str:
        return _text(
            _first(
                decision,
                "symbol",
                default=_first(payload, "symbol", default=""),
            )
        ).upper()

    @staticmethod
    def _action(decision: Mapping[str, Any], payload: Mapping[str, Any]) -> str:
        return _text(
            _first(
                decision,
                "final_action",
                "action",
                default=_first(payload, "action", default="BLOCK"),
            )
        ).upper()

    @staticmethod
    def _allowed(decision: Mapping[str, Any], payload: Mapping[str, Any]) -> bool:
        return bool(
            _first(
                decision,
                "execution_allowed",
                default=_first(payload, "execution_allowed", default=False),
            )
        )

    @staticmethod
    def _status(decision: Mapping[str, Any], payload: Mapping[str, Any]) -> str:
        # Block 88 contract:
        # execution status is independent from trading action.
        # Never interpret BUY / SELL / HOLD as execution status.
        return _text(
            _first(
                payload,
                "execution_status",
                "status",
                default=_first(
                    decision,
                    "execution_status",
                    "status",
                    default="BLOCKED",
                ),
            )
        ).upper()

    @staticmethod
    def _order_id(order: Mapping[str, Any]) -> str:
        return _text(_first(order, "order_id", "execution_id", "id", default=""))

    @staticmethod
    def _fill_id(fill: Mapping[str, Any]) -> str:
        return _text(_first(fill, "fill_id", "execution_id", "id", default=""))

    @staticmethod
    def _quantity(item: Mapping[str, Any]) -> float:
        return _number(_first(item, "quantity", "filled_quantity", "qty", default=0.0))

    @staticmethod
    def _price(item: Mapping[str, Any]) -> float:
        return _number(
            _first(item, "price", "fill_price", "average_price", "limit_price", default=0.0)
        )

    @staticmethod
    def _notional(item: Mapping[str, Any]) -> float:
        explicit = _first(item, "notional", "notional_value", "gross_notional")
        if explicit is not None:
            return _number(explicit)
        return abs(
            EROSBlock88AuditReconciliationEngine._quantity(item)
            * EROSBlock88AuditReconciliationEngine._price(item)
        )

    @staticmethod
    def _cost(tca: Mapping[str, Any]) -> float:
        for key in (
            "total_cost",
            "transaction_cost",
            "estimated_transaction_cost",
            "total_transaction_cost",
        ):
            if key in tca:
                return _number(tca[key])
        return 0.0

    def _validate_gate(
        self,
        decision: Mapping[str, Any],
        payload: Mapping[str, Any],
        exceptions: list[str],
    ) -> None:
        if not self._allowed(decision, payload):
            exceptions.append("EXECUTION_NOT_ALLOWED")

        status = self._status(decision, payload)
        if status not in {"EXECUTION_READY", "APPROVED", "READY"}:
            exceptions.append(f"INVALID_EXECUTION_STATUS:{status}")

        if bool(_first(payload, "broker_submission", default=False)):
            exceptions.append("BROKER_SUBMISSION_DETECTED")

        if bool(_first(payload, "live_order_submission", default=False)):
            exceptions.append("LIVE_ORDER_SUBMISSION_DETECTED")

    def reconcile(
        self,
        execution_result: Any,
        *,
        expected_orders: Iterable[Mapping[str, Any]] | None = None,
        expected_fills: Iterable[Mapping[str, Any]] | None = None,
        expected_tca: Mapping[str, Any] | None = None,
    ) -> ExecutionAuditRecord:
        payload = _dict(execution_result)
        decision = self._decision(payload)

        orders = self._orders(payload)
        fills = self._fills(payload)
        tca = self._tca(payload)

        if expected_orders is not None:
            expected_order_list = [_dict(x) for x in expected_orders]
        else:
            expected_order_list = orders

        if expected_fills is not None:
            expected_fill_list = [_dict(x) for x in expected_fills]
        else:
            expected_fill_list = fills

        expected_tca_dict = _dict(expected_tca) if expected_tca is not None else tca

        exceptions: list[str] = []
        self._validate_gate(decision, payload, exceptions)

        decision_id = self._decision_id(decision)
        symbol = self._symbol(decision, payload)
        requested_action = _text(
            _first(
                decision,
                "requested_action",
                "action",
                default=_first(payload, "requested_action", default=""),
            )
        ).upper()
        final_action = self._action(decision, payload)

        if not symbol:
            exceptions.append("MISSING_SYMBOL")

        if not decision_id or decision_id == "UNKNOWN-DECISION":
            exceptions.append("MISSING_DECISION_ID")

        order_ids = [self._order_id(x) for x in orders if self._order_id(x)]
        fill_ids = [self._fill_id(x) for x in fills if self._fill_id(x)]

        if len(order_ids) != len(set(order_ids)):
            exceptions.append("DUPLICATE_ORDER_ID")

        if len(fill_ids) != len(set(fill_ids)):
            exceptions.append("DUPLICATE_FILL_ID")

        expected_quantity = sum(
            self._quantity(x)
            for x in (expected_fill_list if expected_fills is not None else expected_order_list)
        )

        actual_quantity = sum(self._quantity(x) for x in fills)

        # ------------------------------------------------------
        # BLOCK 88 EXECUTED-NOTIONAL CONTRACT
        #
        # Orders describe the requested execution.
        # Fills describe the actual executed execution.
        #
        # Paper execution may legitimately introduce modeled
        # slippage between order price and fill price.
        #
        # Therefore, when expected fills are supplied, executed
        # notional must be reconciled against expected fills,
        # NOT against the original order price.
        #
        # Without expected fills, retain the order-notional
        # fallback for backward compatibility.
        # ------------------------------------------------------

        if expected_fills is not None:
            expected_notional = sum(self._notional(x) for x in expected_fill_list)
        else:
            expected_notional = sum(self._notional(x) for x in expected_order_list)

        actual_notional = sum(self._notional(x) for x in fills)

        expected_cost = self._cost(expected_tca_dict)
        actual_cost = self._cost(tca)

        quantity_variance = actual_quantity - expected_quantity
        notional_variance = actual_notional - expected_notional
        cost_variance = actual_cost - expected_cost

        if len(orders) != len(expected_order_list):
            exceptions.append("ORDER_COUNT_MISMATCH")

        if expected_order_list and abs(quantity_variance) > self.quantity_tolerance:
            exceptions.append("QUANTITY_MISMATCH")

        if expected_order_list and abs(notional_variance) > self.notional_tolerance:
            exceptions.append("NOTIONAL_MISMATCH")

        if expected_tca is not None and abs(cost_variance) > self.cost_tolerance:
            exceptions.append("TRANSACTION_COST_MISMATCH")

        if expected_order_list and not fills:
            exceptions.append("MISSING_FILLS")

        # An audit must never certify a blocked execution as reconciled.
        if exceptions:
            reconciliation_status = "EXCEPTION"
            execution_status = (
                "BLOCKED" if not self._allowed(decision, payload) else "AUDIT_EXCEPTION"
            )
        else:
            reconciliation_status = "RECONCILED"
            execution_status = "RECONCILED"

        audit_seed = {
            "schema": AUDIT_SCHEMA_VERSION,
            "engine": ENGINE_VERSION,
            "decision_id": decision_id,
            "symbol": symbol,
            "requested_action": requested_action,
            "final_action": final_action,
            "execution_status": execution_status,
            "execution_allowed": self._allowed(decision, payload),
            "orders": orders,
            "fills": fills,
            "tca": tca,
            "exceptions": sorted(exceptions),
        }

        audit_hash = _hash_payload(audit_seed)
        audit_id = f"EROS88-{audit_hash[:16]}"

        return ExecutionAuditRecord(
            audit_id=audit_id,
            audit_schema_version=AUDIT_SCHEMA_VERSION,
            engine_version=ENGINE_VERSION,
            timestamp_utc=_utc_now(),
            decision_id=decision_id,
            symbol=symbol,
            requested_action=requested_action,
            final_action=final_action,
            execution_status=execution_status,
            execution_allowed=self._allowed(decision, payload),
            expected_order_count=len(expected_order_list),
            actual_order_count=len(orders),
            expected_fill_count=len(expected_fill_list),
            actual_fill_count=len(fills),
            expected_quantity=expected_quantity,
            actual_quantity=actual_quantity,
            quantity_variance=quantity_variance,
            expected_notional=expected_notional,
            actual_notional=actual_notional,
            notional_variance=notional_variance,
            expected_transaction_cost=expected_cost,
            actual_transaction_cost=actual_cost,
            transaction_cost_variance=cost_variance,
            reconciliation_status=reconciliation_status,
            exception_count=len(exceptions),
            exceptions=sorted(set(exceptions)),
            broker_submission=False,
            live_order_submission=False,
            paper_execution=True,
            source_order_ids=sorted(set(order_ids)),
            source_fill_ids=sorted(set(fill_ids)),
            audit_hash=audit_hash,
        )

    def certify(self, audit: Any) -> Block88AuditCertificate:
        record = _dict(audit)

        reconciliation_status = _text(record.get("reconciliation_status"), "EXCEPTION").upper()
        exceptions = _list(record.get("exceptions"))

        execution_allowed = bool(record.get("execution_allowed", False))
        broker_submission = bool(record.get("broker_submission", False))
        live_submission = bool(record.get("live_order_submission", False))

        if (
            reconciliation_status == "RECONCILED"
            and not exceptions
            and execution_allowed
            and not broker_submission
            and not live_submission
        ):
            status = "CERTIFIED"
        else:
            status = "BLOCKED"

        seed = {
            "audit_id": record.get("audit_id", ""),
            "audit_hash": record.get("audit_hash", ""),
            "reconciliation_status": reconciliation_status,
            "status": status,
            "execution_allowed": execution_allowed,
            "broker_submission": broker_submission,
            "live_order_submission": live_submission,
        }

        certificate_hash = _hash_payload(seed)

        return Block88AuditCertificate(
            status=status,
            reconciliation_status=reconciliation_status,
            audit_id=_text(record.get("audit_id"), "UNKNOWN-AUDIT"),
            decision_id=_text(record.get("decision_id"), "UNKNOWN-DECISION"),
            symbol=_text(record.get("symbol")).upper(),
            exception_count=len(exceptions),
            audit_hash=_text(record.get("audit_hash")),
            execution_allowed=execution_allowed,
            broker_submission=broker_submission,
            live_order_submission=live_submission,
            certificate_hash=certificate_hash,
            created_at_utc=_utc_now(),
        )

    def audit_and_certify(
        self,
        execution_result: Any,
        *,
        expected_orders: Iterable[Mapping[str, Any]] | None = None,
        expected_fills: Iterable[Mapping[str, Any]] | None = None,
        expected_tca: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        audit = self.reconcile(
            execution_result,
            expected_orders=expected_orders,
            expected_fills=expected_fills,
            expected_tca=expected_tca,
        )
        certificate = self.certify(audit)
        return {
            "status": "PASS" if certificate.status == "CERTIFIED" else "BLOCKED",
            "audit": audit.to_dict(),
            "certificate": certificate.to_dict(),
        }
