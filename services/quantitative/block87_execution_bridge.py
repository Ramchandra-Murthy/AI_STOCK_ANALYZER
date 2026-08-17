from __future__ import annotations

"""
EROS 3.0 - Block 87
Controlled Execution Bridge.

Purpose:
    Convert an APPROVED Block 86 control decision into a canonical
    execution request using the existing InstitutionalExecutionEngine.

Safety:
    - Never submits broker orders.
    - Never upgrades BLOCKED/REVIEW decisions.
    - Requires Block 86 APPROVED + execution_allowed=True.
    - Enforces deterministic idempotency.
    - Preserves Block 86 decision provenance.
"""

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from typing import Any, Dict, List, Mapping, Optional

from services.execution.execution_engine import InstitutionalExecutionEngine
from services.execution.transaction_cost import TransactionCostAnalyzer


ENGINE_VERSION = "EROS-3.0-BLOCK-87"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}

    if isinstance(value, Mapping):
        return dict(value)

    if is_dataclass(value):
        return asdict(value)

    if hasattr(value, "to_dict") and callable(value.to_dict):
        result = value.to_dict()
        return dict(result) if isinstance(result, Mapping) else {}

    if hasattr(value, "__dict__"):
        return dict(value.__dict__)

    return {"value": value}


def _number(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default


def _hash_payload(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class Block87ExecutionResult:
    status: str
    execution_allowed: bool
    decision_id: str
    request_id: str
    idempotency_key: str
    symbol: str
    action: str
    order_count: int
    orders: List[Dict[str, Any]] = field(default_factory=list)
    total_notional: float = 0.0
    total_transaction_cost: float = 0.0
    transaction_cost_bps: float = 0.0
    rationale: List[str] = field(default_factory=list)
    blocking_reasons: List[str] = field(default_factory=list)
    audit_evidence: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    engine_version: str = ENGINE_VERSION
    timestamp: str = field(default_factory=_utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EROSBlock87ExecutionBridge:
    """
    Controlled bridge between Block 86 and the existing execution service.

    Block 87 does NOT decide whether a trade should happen.
    Block 86 already made that decision.

    Block 87 may only:
        APPROVED + execution_allowed=True
            -> generate canonical execution orders

        anything else
            -> BLOCK
    """

    EXECUTABLE_ACTIONS = {"BUY", "SELL", "REDUCE"}
    BLOCKING_CONTROL_STATES = {
        "BLOCKED",
        "BLOCK",
        "REVIEW",
        "REJECTED",
        "FAILED",
        "ERROR",
    }

    def __init__(
        self,
        execution_policy: str = "VWAP-oriented",
        max_allocation_weight: float = 0.25,
    ) -> None:

        if not execution_policy.strip():
            raise ValueError("execution_policy must not be empty")

        if not 0.0 < max_allocation_weight <= 1.0:
            raise ValueError(
                "max_allocation_weight must be > 0 and <= 1"
            )

        self.execution_policy = execution_policy
        self.max_allocation_weight = float(max_allocation_weight)

        # In-memory deterministic idempotency registry.
        # A future persistent execution store can replace this without
        # changing the Block 87 public contract.
        self._completed_requests: Dict[str, Block87ExecutionResult] = {}

    @staticmethod
    def _decision_symbol(decision: Mapping[str, Any]) -> str:
        return str(decision.get("symbol", "")).strip().upper()

    @staticmethod
    def _decision_id(decision: Mapping[str, Any]) -> str:
        return str(decision.get("decision_id", "")).strip()

    @staticmethod
    def _action(decision: Mapping[str, Any]) -> str:
        return str(decision.get("final_action", "")).strip().upper()

    def _build_idempotency_key(
        self,
        decision: Mapping[str, Any],
        allocations: List[Mapping[str, Any]],
    ) -> str:

        payload = {
            "decision_id": self._decision_id(decision),
            "symbol": self._decision_symbol(decision),
            "final_action": self._action(decision),
            "execution_policy": self.execution_policy,
            "allocations": allocations,
        }

        return "EROS87-" + _hash_payload(payload)[:24].upper()

    def _blocked(
        self,
        decision: Mapping[str, Any],
        reason: str,
        *,
        request_id: str = "",
        idempotency_key: str = "",
    ) -> Block87ExecutionResult:

        symbol = self._decision_symbol(decision)
        action = self._action(decision)
        decision_id = self._decision_id(decision)

        return Block87ExecutionResult(
            status="BLOCKED",
            execution_allowed=False,
            decision_id=decision_id,
            request_id=request_id or (
                "EROS87-" + _hash_payload(
                    {
                        "decision_id": decision_id,
                        "reason": reason,
                    }
                )[:16].upper()
            ),
            idempotency_key=idempotency_key,
            symbol=symbol,
            action="BLOCK",
            order_count=0,
            orders=[],
            rationale=[
                "Block 87 did not receive an executable authorization."
            ],
            blocking_reasons=[reason],
            audit_evidence={
                "block86_decision_id": decision_id,
                "broker_submission": False,
                "live_order_submission": False,
            },
            metadata={
                "source": "EROS-3.0-BLOCK-86",
                "execution_policy": self.execution_policy,
            },
        )

    def _validate_allocations(
        self,
        decision: Mapping[str, Any],
        allocations: List[Mapping[str, Any]],
    ) -> List[Dict[str, Any]]:

        decision_symbol = self._decision_symbol(decision)
        decision_action = self._action(decision)

        if not allocations:
            raise ValueError("No execution allocations supplied")

        normalized: List[Dict[str, Any]] = []

        for index, raw in enumerate(allocations):

            row = _to_dict(raw)

            symbol = str(
                row.get("symbol", decision_symbol)
            ).strip().upper()

            if not symbol:
                raise ValueError(
                    f"Allocation {index}: missing symbol"
                )

            if decision_symbol and symbol != decision_symbol:
                raise ValueError(
                    f"Allocation {index}: symbol {symbol} does not "
                    f"match Block 86 symbol {decision_symbol}"
                )

            action = str(
                row.get("action", decision_action)
            ).strip().upper()

            if action != decision_action:
                raise ValueError(
                    f"Allocation {index}: action {action} does not "
                    f"match Block 86 action {decision_action}"
                )

            weight = _number(
                row.get(
                    "trade_weight",
                    row.get("allocation_pct", 0.0),
                ),
                0.0,
            )

            if weight < 0:
                raise ValueError(
                    f"{symbol}: negative allocation weight"
                )

            if weight > self.max_allocation_weight:
                raise ValueError(
                    f"{symbol}: allocation weight {weight:.4f} "
                    f"exceeds Block 87 limit "
                    f"{self.max_allocation_weight:.4f}"
                )

            normalized.append(
                {
                    **row,
                    "symbol": symbol,
                    "action": action,
                    "trade_weight": weight,
                    "block86_decision_id": self._decision_id(
                        decision
                    ),
                }
            )

        return normalized

    @staticmethod
    def _calculate_tca(
        orders: List[Mapping[str, Any]],
    ) -> Dict[str, Any]:

        rows: List[Dict[str, Any]] = []
        total_notional = 0.0
        total_cost = 0.0

        for order in orders:

            action = str(
                order.get("action", "")
            ).upper()

            if action == "HOLD":
                continue

            quantity = _number(
                order.get("quantity"),
                0.0,
            )

            price = _number(
                order.get("limit_price"),
                0.0,
            )

            notional = abs(quantity * price)

            if notional <= 0:
                continue

            participation = max(
                0.0,
                min(
                    1.0,
                    _number(
                        order.get(
                            "order_size_pct_adv",
                            0.0,
                        ),
                        0.0,
                    ),
                ),
            )

            tca = TransactionCostAnalyzer.analyze_order_costs(
                notional,
                participation,
            )

            total_notional += notional
            total_cost += _number(
                tca.get(
                    "total_transaction_cost",
                    0.0,
                )
            )

            rows.append(
                {
                    "symbol": str(
                        order.get("symbol", "")
                    ).upper(),
                    "action": action,
                    "notional": round(notional, 2),
                    **tca,
                }
            )

        cost_bps = (
            total_cost / total_notional * 10000.0
            if total_notional > 0
            else 0.0
        )

        return {
            "orders": rows,
            "order_count": len(rows),
            "total_notional": round(total_notional, 2),
            "total_transaction_cost": round(total_cost, 2),
            "transaction_cost_bps": round(cost_bps, 4),
        }

    def execute(
        self,
        decision: Any,
        allocations: List[Mapping[str, Any]],
    ) -> Block87ExecutionResult:

        decision_dict = _to_dict(decision)

        decision_id = self._decision_id(decision_dict)
        control_state = str(
            decision_dict.get(
                "control_state",
                "UNKNOWN",
            )
        ).upper()

        execution_allowed = bool(
            decision_dict.get(
                "execution_allowed",
                False,
            )
        )

        action = self._action(decision_dict)

        idempotency_key = self._build_idempotency_key(
            decision_dict,
            list(allocations),
        )

        if idempotency_key in self._completed_requests:
            previous = self._completed_requests[
                idempotency_key
            ]

            return Block87ExecutionResult(
                **{
                    **previous.to_dict(),
                    "status": "DUPLICATE",
                    "rationale": [
                        *previous.rationale,
                        "Duplicate execution request detected; "
                        "original execution result returned.",
                    ],
                }
            )

        if not decision_id:
            return self._blocked(
                decision_dict,
                "Missing Block 86 decision_id.",
                idempotency_key=idempotency_key,
            )

        if control_state != "APPROVED":
            result = self._blocked(
                decision_dict,
                f"Block 86 control_state is {control_state}; "
                "only APPROVED decisions may reach execution.",
                idempotency_key=idempotency_key,
            )
            self._completed_requests[idempotency_key] = result
            return result

        if not execution_allowed:
            result = self._blocked(
                decision_dict,
                "Block 86 execution_allowed is false.",
                idempotency_key=idempotency_key,
            )
            self._completed_requests[idempotency_key] = result
            return result

        if action not in self.EXECUTABLE_ACTIONS:
            result = self._blocked(
                decision_dict,
                f"Block 86 action {action} is not executable.",
                idempotency_key=idempotency_key,
            )
            self._completed_requests[idempotency_key] = result
            return result

        try:
            normalized = self._validate_allocations(
                decision_dict,
                list(allocations),
            )
        except ValueError as exc:

            result = self._blocked(
                decision_dict,
                str(exc),
                idempotency_key=idempotency_key,
            )

            self._completed_requests[idempotency_key] = result

            return result

        orders = InstitutionalExecutionEngine.generate_orders(
            normalized,
            execution_policy=self.execution_policy,
        )

        order_dicts: List[Dict[str, Any]] = []

        for order in orders:

            row = _to_dict(order)

            row["metadata"] = {
                **_to_dict(row.get("metadata")),
                "block86_decision_id": decision_id,
                "block87_idempotency_key": idempotency_key,
                "broker_submission": False,
                "live_order_submission": False,
            }

            order_dicts.append(row)

        tca = self._calculate_tca(order_dicts)

        request_id = (
            "EROS87-"
            + _hash_payload(
                {
                    "decision_id": decision_id,
                    "idempotency_key": idempotency_key,
                    "orders": order_dicts,
                }
            )[:16].upper()
        )

        result = Block87ExecutionResult(
            status="EXECUTION_READY",
            execution_allowed=True,
            decision_id=decision_id,
            request_id=request_id,
            idempotency_key=idempotency_key,
            symbol=self._decision_symbol(decision_dict),
            action=action,
            order_count=len(order_dicts),
            orders=order_dicts,
            total_notional=tca["total_notional"],
            total_transaction_cost=tca[
                "total_transaction_cost"
            ],
            transaction_cost_bps=tca[
                "transaction_cost_bps"
            ],
            rationale=[
                "Block 86 authorization was APPROVED.",
                "Execution permission was explicitly enabled.",
                "Orders generated through the existing "
                "InstitutionalExecutionEngine.",
                "No broker or live-order submission performed.",
            ],
            blocking_reasons=[],
            audit_evidence={
                "block86_decision_id": decision_id,
                "block86_decision_hash": _to_dict(
                    decision_dict.get(
                        "audit_evidence"
                    )
                ).get("decision_hash"),
                "block87_request_id": request_id,
                "block87_idempotency_key": idempotency_key,
                "broker_submission": False,
                "live_order_submission": False,
                "execution_engine": (
                    "InstitutionalExecutionEngine"
                ),
            },
            metadata={
                "source": "EROS-3.0-BLOCK-86",
                "execution_policy": self.execution_policy,
                "engine_version": ENGINE_VERSION,
            },
        )

        self._completed_requests[idempotency_key] = result

        return result

    def certify(
        self,
        decision: Any,
        allocations: List[Mapping[str, Any]],
    ) -> Block87ExecutionResult:

        return self.execute(
            decision,
            allocations,
        )


__all__ = [
    "ENGINE_VERSION",
    "Block87ExecutionResult",
    "EROSBlock87ExecutionBridge",
]
