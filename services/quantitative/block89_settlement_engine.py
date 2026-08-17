from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional


ENGINE_VERSION = "EROS-3.0-BLOCK-89"
SETTLEMENT_SCHEMA_VERSION = "1.0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)

    if hasattr(value, "to_dict"):
        converted = value.to_dict()
        if isinstance(converted, Mapping):
            return dict(converted)

    if hasattr(value, "__dict__"):
        return dict(value.__dict__)

    return {}


def _list(value: Any) -> List[Any]:
    if value is None:
        return []

    if isinstance(value, list):
        return list(value)

    if isinstance(value, tuple):
        return list(value)

    return [value]


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default

    text = str(value).strip()

    return text if text else default


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _hash_payload(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        dict(payload),
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(canonical).hexdigest().upper()


def _first(
    payload: Mapping[str, Any],
    *keys: str,
    default: Any = None,
) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]

    return default


@dataclass(frozen=True)
class SettlementRecord:
    settlement_id: str
    settlement_schema_version: str
    engine_version: str
    timestamp_utc: str

    audit_id: str
    certificate_hash: str
    decision_id: str
    symbol: str
    action: str

    settlement_status: str
    settlement_allowed: bool

    order_count: int
    fill_count: int

    settled_quantity: float
    average_fill_price: float

    gross_value: float
    transaction_cost: float
    net_cash_value: float

    cash_delta: float
    position_delta: float

    realized_pnl: float

    broker_submission: bool
    live_order_submission: bool
    paper_settlement: bool

    source_order_ids: List[str] = field(default_factory=list)
    source_fill_ids: List[str] = field(default_factory=list)

    exceptions: List[str] = field(default_factory=list)

    settlement_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Block89SettlementCertificate:
    status: str
    settlement_status: str

    settlement_id: str
    audit_id: str
    certificate_hash: str

    decision_id: str
    symbol: str

    settlement_allowed: bool

    exception_count: int

    broker_submission: bool
    live_order_submission: bool
    paper_settlement: bool

    settlement_hash: str
    certificate_hash_89: str

    created_at_utc: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EROSBlock89SettlementEngine:
    """
    EROS 3.0 Block 89
    ------------------

    Controlled post-trade settlement/accounting layer.

    Block 89 does NOT create or submit orders.

    It consumes the Block 88 audit/certificate contract and may
    settle only an execution that is:

        CERTIFIED
        +
        RECONCILED
        +
        execution_allowed=True
        +
        broker_submission=False
        +
        live_order_submission=False

    Settlement is paper/internal accounting only.
    """

    SETTLEMENT_READY_STATUSES = {
        "CERTIFIED",
    }

    RECONCILED_STATUS = "RECONCILED"

    def __init__(self) -> None:
        self._completed_settlements: Dict[str, SettlementRecord] = {}

    @staticmethod
    def _audit(payload: Mapping[str, Any]) -> Dict[str, Any]:
        return _dict(payload.get("audit"))

    @staticmethod
    def _certificate(payload: Mapping[str, Any]) -> Dict[str, Any]:
        return _dict(payload.get("certificate"))

    @staticmethod
    def _orders(payload: Mapping[str, Any]) -> List[Dict[str, Any]]:
        return [
            _dict(item)
            for item in _list(payload.get("orders"))
            if isinstance(item, Mapping) or hasattr(item, "__dict__")
        ]

    @staticmethod
    def _fills(payload: Mapping[str, Any]) -> List[Dict[str, Any]]:
        return [
            _dict(item)
            for item in _list(payload.get("fills"))
            if isinstance(item, Mapping) or hasattr(item, "__dict__")
        ]

    @staticmethod
    def _audit_id(
        audit: Mapping[str, Any],
        certificate: Mapping[str, Any],
    ) -> str:
        return _text(
            _first(
                certificate,
                "audit_id",
                default=_first(
                    audit,
                    "audit_id",
                    default="UNKNOWN-AUDIT",
                ),
            ),
            "UNKNOWN-AUDIT",
        )

    @staticmethod
    def _certificate_hash(certificate: Mapping[str, Any]) -> str:
        return _text(
            certificate.get("certificate_hash"),
            "",
        )

    @staticmethod
    def _decision_id(
        audit: Mapping[str, Any],
        certificate: Mapping[str, Any],
    ) -> str:
        return _text(
            _first(
                certificate,
                "decision_id",
                default=_first(
                    audit,
                    "decision_id",
                    default="UNKNOWN-DECISION",
                ),
            ),
            "UNKNOWN-DECISION",
        )

    @staticmethod
    def _symbol(
        audit: Mapping[str, Any],
        fills: Iterable[Mapping[str, Any]],
        orders: Iterable[Mapping[str, Any]],
    ) -> str:
        symbol = _text(audit.get("symbol")).upper()

        if symbol:
            return symbol

        for item in list(fills) + list(orders):
            symbol = _text(item.get("symbol")).upper()
            if symbol:
                return symbol

        return ""

    @staticmethod
    def _action(
        audit: Mapping[str, Any],
        fills: Iterable[Mapping[str, Any]],
        orders: Iterable[Mapping[str, Any]],
    ) -> str:
        action = _text(audit.get("final_action")).upper()

        if action:
            return action

        for item in list(fills) + list(orders):
            action = _text(item.get("action")).upper()
            if action:
                return action

        return ""

    @staticmethod
    def _allowed(
        certificate: Mapping[str, Any],
        audit: Mapping[str, Any],
    ) -> bool:
        return bool(
            _first(
                certificate,
                "settlement_allowed",
                default=_first(
                    certificate,
                    "execution_allowed",
                    default=audit.get("execution_allowed", False),
                ),
            )
        )

    @staticmethod
    def _quantity(fill: Mapping[str, Any]) -> float:
        return _number(
            _first(
                fill,
                "filled_quantity",
                "quantity",
                "executed_quantity",
                default=0.0,
            )
        )

    @staticmethod
    def _price(fill: Mapping[str, Any]) -> float:
        return _number(
            _first(
                fill,
                "fill_price",
                "executed_price",
                "price",
                default=0.0,
            )
        )

    @staticmethod
    def _gross_value(fill: Mapping[str, Any]) -> float:
        explicit = _first(
            fill,
            "gross_value",
            "executed_value",
            "notional",
            default=None,
        )

        if explicit is not None:
            return _number(explicit)

        return EROSBlock89SettlementEngine._quantity(fill) * (
            EROSBlock89SettlementEngine._price(fill)
        )

    @staticmethod
    def _transaction_cost(fill: Mapping[str, Any]) -> float:
        return _number(
            _first(
                fill,
                "transaction_cost",
                "execution_cost",
                default=0.0,
            )
        )

    @staticmethod
    def _fill_id(fill: Mapping[str, Any]) -> str:
        return _text(
            _first(
                fill,
                "fill_id",
                "execution_id",
                "id",
                default="",
            )
        )

    @staticmethod
    def _order_id(order: Mapping[str, Any]) -> str:
        return _text(
            _first(
                order,
                "order_id",
                "id",
                default="",
            )
        )

    def _validate_certificate(
        self,
        audit: Mapping[str, Any],
        certificate: Mapping[str, Any],
        exceptions: List[str],
    ) -> None:
        certificate_status = _text(
            certificate.get("status"),
            "BLOCKED",
        ).upper()

        reconciliation_status = _text(
            certificate.get("reconciliation_status"),
            "EXCEPTION",
        ).upper()

        execution_allowed = self._allowed(
            certificate,
            audit,
        )

        broker_submission = bool(
            certificate.get("broker_submission", False)
        )

        live_submission = bool(
            certificate.get(
                "live_order_submission",
                False,
            )
        )

        if certificate_status not in self.SETTLEMENT_READY_STATUSES:
            exceptions.append(
                f"INVALID_CERTIFICATE_STATUS:{certificate_status}"
            )

        if reconciliation_status != self.RECONCILED_STATUS:
            exceptions.append(
                f"INVALID_RECONCILIATION_STATUS:{reconciliation_status}"
            )

        if not execution_allowed:
            exceptions.append("EXECUTION_NOT_ALLOWED")

        if broker_submission:
            exceptions.append("BROKER_SUBMISSION_DETECTED")

        if live_submission:
            exceptions.append("LIVE_ORDER_SUBMISSION_DETECTED")

        if bool(audit.get("exceptions")):
            exceptions.append("AUDIT_EXCEPTIONS_PRESENT")

    def _build_settlement(
        self,
        *,
        audit: Mapping[str, Any],
        certificate: Mapping[str, Any],
        orders: List[Dict[str, Any]],
        fills: List[Dict[str, Any]],
        exceptions: List[str],
    ) -> SettlementRecord:
        audit_id = self._audit_id(audit, certificate)
        certificate_hash = self._certificate_hash(certificate)
        decision_id = self._decision_id(audit, certificate)

        symbol = self._symbol(audit, fills, orders)
        action = self._action(audit, fills, orders)

        settled_quantity = round(
            sum(self._quantity(fill) for fill in fills),
            6,
        )

        gross_value = round(
            sum(self._gross_value(fill) for fill in fills),
            6,
        )

        transaction_cost = round(
            sum(
                self._transaction_cost(fill)
                for fill in fills
            ),
            6,
        )

        average_fill_price = (
            gross_value / settled_quantity
            if settled_quantity > 0
            else 0.0
        )

        if action in {"SELL", "REDUCE"}:
            cash_delta = round(
                gross_value - transaction_cost,
                6,
            )
            position_delta = -settled_quantity
            realized_pnl = round(
                gross_value - transaction_cost,
                6,
            )
            net_cash_value = cash_delta
        elif action == "BUY":
            cash_delta = round(
                -(gross_value + transaction_cost),
                6,
            )
            position_delta = settled_quantity
            realized_pnl = 0.0
            net_cash_value = cash_delta
        else:
            cash_delta = 0.0
            position_delta = 0.0
            realized_pnl = 0.0
            net_cash_value = 0.0

        allowed = (
            not exceptions
            and bool(certificate.get("execution_allowed", False))
        )

        settlement_status = (
            "SETTLED"
            if allowed
            else "BLOCKED"
        )

        seed = {
            "schema": SETTLEMENT_SCHEMA_VERSION,
            "engine": ENGINE_VERSION,
            "audit_id": audit_id,
            "certificate_hash": certificate_hash,
            "decision_id": decision_id,
            "symbol": symbol,
            "action": action,
            "settlement_status": settlement_status,
            "settlement_allowed": allowed,
            "orders": orders,
            "fills": fills,
            "exceptions": sorted(set(exceptions)),
            "gross_value": gross_value,
            "transaction_cost": transaction_cost,
            "cash_delta": cash_delta,
            "position_delta": position_delta,
        }

        settlement_hash = _hash_payload(seed)
        settlement_id = (
            f"EROS89-{settlement_hash[:16]}"
        )

        return SettlementRecord(
            settlement_id=settlement_id,
            settlement_schema_version=SETTLEMENT_SCHEMA_VERSION,
            engine_version=ENGINE_VERSION,
            timestamp_utc=_utc_now(),
            audit_id=audit_id,
            certificate_hash=certificate_hash,
            decision_id=decision_id,
            symbol=symbol,
            action=action,
            settlement_status=settlement_status,
            settlement_allowed=allowed,
            order_count=len(orders),
            fill_count=len(fills),
            settled_quantity=settled_quantity,
            average_fill_price=round(
                average_fill_price,
                6,
            ),
            gross_value=gross_value,
            transaction_cost=transaction_cost,
            net_cash_value=net_cash_value,
            cash_delta=cash_delta,
            position_delta=position_delta,
            realized_pnl=realized_pnl,
            broker_submission=False,
            live_order_submission=False,
            paper_settlement=True,
            source_order_ids=sorted(
                set(
                    self._order_id(order)
                    for order in orders
                    if self._order_id(order)
                )
            ),
            source_fill_ids=sorted(
                set(
                    self._fill_id(fill)
                    for fill in fills
                    if self._fill_id(fill)
                )
            ),
            exceptions=sorted(set(exceptions)),
            settlement_hash=settlement_hash,
        )

    def settle(
        self,
        audit_certificate: Any,
        *,
        orders: Optional[
            Iterable[Mapping[str, Any]]
        ] = None,
        fills: Optional[
            Iterable[Mapping[str, Any]]
        ] = None,
    ) -> Dict[str, Any]:
        payload = _dict(audit_certificate)

        audit = self._audit(payload)
        certificate = self._certificate(payload)

        order_list = (
            [_dict(item) for item in orders]
            if orders is not None
            else self._orders(payload)
        )

        fill_list = (
            [_dict(item) for item in fills]
            if fills is not None
            else self._fills(payload)
        )

        exceptions: List[str] = []

        self._validate_certificate(
            audit,
            certificate,
            exceptions,
        )

        if not audit:
            exceptions.append("MISSING_AUDIT")

        if not certificate:
            exceptions.append("MISSING_CERTIFICATE")

        if not fill_list:
            exceptions.append("MISSING_FILLS")

        if order_list and fill_list:
            expected_quantity = round(
                sum(
                    _number(
                        _first(
                            item,
                            "filled_quantity",
                            "quantity",
                            "requested_quantity",
                            default=0.0,
                        )
                    )
                    for item in fill_list
                ),
                6,
            )

            actual_quantity = round(
                sum(
                    self._quantity(item)
                    for item in fill_list
                ),
                6,
            )

            if abs(
                actual_quantity - expected_quantity
            ) > 1e-6:
                exceptions.append(
                    "FILL_QUANTITY_INTERNAL_MISMATCH"
                )

        settlement = self._build_settlement(
            audit=audit,
            certificate=certificate,
            orders=order_list,
            fills=fill_list,
            exceptions=exceptions,
        )

        settlement_key = (
            settlement.certificate_hash
            or settlement.audit_id
        )

        if settlement_key in self._completed_settlements:
            previous = self._completed_settlements[
                settlement_key
            ]

            return {
                "status": "DUPLICATE",
                "settlement": previous.to_dict(),
                "certificate": self._certificate_for(
                    previous,
                    duplicate=True,
                ),
            }

        self._completed_settlements[
            settlement_key
        ] = settlement

        return {
            "status": (
                "PASS"
                if settlement.settlement_status == "SETTLED"
                else "BLOCKED"
            ),
            "settlement": settlement.to_dict(),
            "certificate": self._certificate_for(
                settlement,
                duplicate=False,
            ),
        }

    def _certificate_for(
        self,
        settlement: SettlementRecord,
        *,
        duplicate: bool,
    ) -> Dict[str, Any]:
        status = (
            "DUPLICATE"
            if duplicate
            else (
                "CERTIFIED"
                if settlement.settlement_status == "SETTLED"
                else "BLOCKED"
            )
        )

        seed = {
            "settlement_id": settlement.settlement_id,
            "settlement_hash": settlement.settlement_hash,
            "audit_id": settlement.audit_id,
            "certificate_hash": settlement.certificate_hash,
            "settlement_status": settlement.settlement_status,
            "status": status,
            "settlement_allowed": settlement.settlement_allowed,
            "broker_submission": False,
            "live_order_submission": False,
            "paper_settlement": True,
        }

        return Block89SettlementCertificate(
            status=status,
            settlement_status=settlement.settlement_status,
            settlement_id=settlement.settlement_id,
            audit_id=settlement.audit_id,
            certificate_hash=settlement.certificate_hash,
            decision_id=settlement.decision_id,
            symbol=settlement.symbol,
            settlement_allowed=settlement.settlement_allowed,
            exception_count=len(settlement.exceptions),
            broker_submission=False,
            live_order_submission=False,
            paper_settlement=True,
            settlement_hash=settlement.settlement_hash,
            certificate_hash_89=_hash_payload(seed),
            created_at_utc=_utc_now(),
        ).to_dict()


__all__ = [
    "ENGINE_VERSION",
    "SETTLEMENT_SCHEMA_VERSION",
    "SettlementRecord",
    "Block89SettlementCertificate",
    "EROSBlock89SettlementEngine",
]
