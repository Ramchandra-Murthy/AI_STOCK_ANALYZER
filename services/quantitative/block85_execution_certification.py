from __future__ import annotations

"""
EROS 3.0 - Block 85
Quantitative Execution Certification Layer

Purpose:
    Integrate the Block 84 quantitative execution stack with the existing
    execution, validation and simulation services without creating a second
    execution engine.

Safety:
    This module never submits broker orders. It produces certification only.
"""

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
import inspect
import math
from typing import Any, Dict, Iterable, List, Mapping, Optional

from services.execution.transaction_cost import TransactionCostAnalyzer


ENGINE_VERSION = "EROS-3.0-BLOCK-85"


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


def _call_compatible(method: Any, candidates: Iterable[Dict[str, Any]]) -> Any:
    """
    Call an existing service without hard-coding a second contract.

    The first candidate whose keyword set is compatible with the target
    signature is used. If no candidate is compatible, the method is not called.
    """
    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        return None

    params = signature.parameters
    accepts_kwargs = any(
        p.kind == inspect.Parameter.VAR_KEYWORD
        for p in params.values()
    )

    for candidate in candidates:
        if accepts_kwargs:
            return method(**candidate)
        if all(key in params for key in candidate):
            return method(**candidate)

    return None


@dataclass(frozen=True)
class Block85Certification:
    status: str
    execution_allowed: bool
    certification_score: float
    order_count: int
    approved_order_count: int
    blocked_order_count: int
    total_notional: float
    total_transaction_cost: float
    risk_status: str
    governance_status: str
    validation_status: str
    simulation_status: str
    warnings: List[str] = field(default_factory=list)
    blocking_reasons: List[str] = field(default_factory=list)
    assumptions_detected: List[str] = field(default_factory=list)
    execution_orders: List[Dict[str, Any]] = field(default_factory=list)
    tca: Dict[str, Any] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)
    simulation: Dict[str, Any] = field(default_factory=dict)
    risk: Dict[str, Any] = field(default_factory=dict)
    governance: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    engine_version: str = ENGINE_VERSION
    timestamp: str = field(default_factory=_utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EROSBlock85ExecutionCertificationEngine:
    """
    Institutional certification gate for Block 84 execution outputs.

    It:
      1. validates order structure,
      2. calculates TCA using the existing TCA service,
      3. consumes supplied risk/governance/validation/simulation evidence,
      4. detects unsafe assumptions,
      5. produces a deterministic certification.

    It never places or submits a broker order.
    """

    ALLOWED_ACTIONS = {"BUY", "SELL", "HOLD"}
    PASS_STATES = {"PASS", "PASSED", "APPROVED", "SUCCESS", "CERTIFIED"}
    REVIEW_STATES = {"REVIEW", "WARNING", "WARN", "PARTIAL"}
    BLOCK_STATES = {"BLOCK", "BLOCKED", "FAIL", "FAILED", "ERROR", "REJECTED"}

    def __init__(
        self,
        max_order_weight: float = 0.25,
        max_transaction_cost_bps: float = 100.0,
        require_risk_pass: bool = True,
        require_governance_approval: bool = True,
        reject_missing_price: bool = True,
    ) -> None:
        if not 0.0 < max_order_weight <= 1.0:
            raise ValueError("max_order_weight must be > 0 and <= 1")
        if max_transaction_cost_bps < 0:
            raise ValueError("max_transaction_cost_bps must be >= 0")

        self.max_order_weight = float(max_order_weight)
        self.max_transaction_cost_bps = float(max_transaction_cost_bps)
        self.require_risk_pass = bool(require_risk_pass)
        self.require_governance_approval = bool(require_governance_approval)
        self.reject_missing_price = bool(reject_missing_price)

    @staticmethod
    def _state(value: Any, default: str = "UNKNOWN") -> str:
        if isinstance(value, Mapping):
            for key in (
                "status", "state", "governance_status",
                "risk_status", "validation_status", "simulation_status"
            ):
                if key in value:
                    return str(value[key]).upper()
        for key in ("status", "state", "governance_status", "risk_status"):
            if hasattr(value, key):
                return str(getattr(value, key)).upper()
        return default

    def _validate_orders(
        self,
        orders: List[Mapping[str, Any]],
    ) -> tuple[List[Dict[str, Any]], List[str], List[str], float]:
        valid: List[Dict[str, Any]] = []
        warnings: List[str] = []
        blocking: List[str] = []
        total_notional = 0.0

        for index, raw in enumerate(orders):
            order = _to_dict(raw)
            symbol = str(order.get("symbol", "")).strip().upper()
            action = str(order.get("action", "")).strip().upper()
            quantity = _number(order.get("quantity"), -1.0)
            price = _number(
                order.get("limit_price", order.get("reference_price")),
                0.0,
            )

            if not symbol:
                blocking.append(f"Order {index}: missing symbol")
                continue

            if action not in self.ALLOWED_ACTIONS:
                blocking.append(f"{symbol}: invalid action '{action}'")
                continue

            if quantity < 0:
                blocking.append(f"{symbol}: negative/invalid quantity")
                continue

            if action == "HOLD":
                valid.append(order)
                continue

            if self.reject_missing_price and price <= 0:
                blocking.append(f"{symbol}: missing positive execution price")
                continue

            notional = abs(quantity * price)
            total_notional += notional

            weight = _number(
                order.get("allocation_pct",
                         order.get("trade_weight", 0.0)),
                0.0,
            )
            if weight > self.max_order_weight:
                blocking.append(
                    f"{symbol}: order weight {weight:.4f} exceeds "
                    f"limit {self.max_order_weight:.4f}"
                )

            valid.append(order)

        return valid, warnings, blocking, total_notional

    def _calculate_tca(
        self,
        orders: List[Mapping[str, Any]],
        adv_participation: float = 0.0,
    ) -> Dict[str, Any]:
        per_order: List[Dict[str, Any]] = []
        total_cost = 0.0
        total_notional = 0.0

        for raw in orders:
            order = _to_dict(raw)
            action = str(order.get("action", "")).upper()
            if action == "HOLD":
                continue

            quantity = _number(order.get("quantity"), 0.0)
            price = _number(
                order.get("limit_price", order.get("reference_price")),
                0.0,
            )
            notional = abs(quantity * price)
            if notional <= 0:
                continue

            participation = _number(
                order.get("order_size_pct_adv", adv_participation),
                0.0,
            )
            participation = max(0.0, min(1.0, participation))

            tca = TransactionCostAnalyzer.analyze_order_costs(
                notional,
                participation,
            )
            row = {
                "symbol": str(order.get("symbol", "")).upper(),
                "action": action,
                "notional": round(notional, 2),
                **tca,
            }
            per_order.append(row)
            total_cost += _number(tca.get("total_transaction_cost"))
            total_notional += notional

        cost_bps = (
            total_cost / total_notional * 10000.0
            if total_notional > 0
            else 0.0
        )

        return {
            "orders": per_order,
            "order_count": len(per_order),
            "total_notional": round(total_notional, 2),
            "total_transaction_cost": round(total_cost, 2),
            "transaction_cost_bps": round(cost_bps, 4),
        }

    def certify(
        self,
        orders: Optional[List[Mapping[str, Any]]] = None,
        risk: Optional[Any] = None,
        governance: Optional[Any] = None,
        validation: Optional[Any] = None,
        simulation: Optional[Any] = None,
        assumptions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        adv_participation: float = 0.0,
    ) -> Block85Certification:
        orders = list(orders or [])
        valid_orders, warnings, blocking, total_notional = self._validate_orders(orders)

        risk_dict = _to_dict(risk)
        governance_dict = _to_dict(governance)
        validation_dict = _to_dict(validation)
        simulation_dict = _to_dict(simulation)

        risk_status = self._state(risk, "UNKNOWN")
        governance_status = self._state(governance, "UNKNOWN")
        validation_status = self._state(validation, "UNKNOWN")
        simulation_status = self._state(simulation, "UNKNOWN")

        if self.require_risk_pass and risk_status not in self.PASS_STATES:
            blocking.append(f"Risk certification is not PASS: {risk_status}")

        if self.require_governance_approval and governance_status not in {
            "APPROVED", "PASS", "PASSED", "CERTIFIED"
        }:
            blocking.append(
                f"Governance certification is not APPROVED: {governance_status}"
            )

        if validation is not None and validation_status in self.BLOCK_STATES:
            blocking.append(f"Validation failed: {validation_status}")

        if simulation is not None and simulation_status in self.BLOCK_STATES:
            blocking.append(f"Simulation failed: {simulation_status}")

        detected = list(assumptions or [])

        # Surface known non-live assumptions rather than silently treating them
        # as live execution facts.
        for order in valid_orders:
            if _number(order.get("current_price"), 0.0) <= 0 and (
                _number(order.get("limit_price"), 0.0) > 0
            ):
                detected.append(
                    f"{str(order.get('symbol', '')).upper()}: "
                    "current market price not supplied"
                )
            if "2500.0" == str(order.get("limit_price", "")):
                detected.append(
                    f"{str(order.get('symbol', '')).upper()}: "
                    "possible fallback-price assumption detected"
                )

        tca = self._calculate_tca(valid_orders, adv_participation)
        tca_bps = _number(tca.get("transaction_cost_bps"))

        if tca_bps > self.max_transaction_cost_bps:
            blocking.append(
                f"TCA cost {tca_bps:.4f} bps exceeds "
                f"limit {self.max_transaction_cost_bps:.4f} bps"
            )

        # Assumptions are retained as audit evidence but are not automatically
        # treated as execution warnings. A governance/risk/data failure must
        # independently establish a blocking condition.

        approved_count = len(valid_orders) - len(
            [reason for reason in blocking if "Order " in reason]
        )
        approved_count = max(0, min(len(valid_orders), approved_count))

        score = 100.0
        score -= min(40.0, 10.0 * len(blocking))
        score -= min(15.0, 3.0 * len(warnings))
        score -= min(15.0, tca_bps / 10.0)
        score = max(0.0, round(score, 2))

        if blocking:
            status = "BLOCKED"
            execution_allowed = False
        elif warnings:
            status = "REVIEW"
            execution_allowed = False
        else:
            status = "CERTIFIED"
            execution_allowed = True

        return Block85Certification(
            status=status,
            execution_allowed=execution_allowed,
            certification_score=score,
            order_count=len(orders),
            approved_order_count=approved_count,
            blocked_order_count=max(0, len(orders) - approved_count),
            total_notional=round(
                max(total_notional, _number(tca.get("total_notional"))), 2
            ),
            total_transaction_cost=_number(
                tca.get("total_transaction_cost")
            ),
            risk_status=risk_status,
            governance_status=governance_status,
            validation_status=validation_status,
            simulation_status=simulation_status,
            warnings=warnings,
            blocking_reasons=blocking,
            assumptions_detected=sorted(set(detected)),
            execution_orders=[_to_dict(x) for x in valid_orders],
            tca=tca,
            validation=validation_dict,
            simulation=simulation_dict,
            risk=risk_dict,
            governance=governance_dict,
            metadata={
                **(metadata or {}),
                "broker_submission": False,
                "live_order_submission": False,
                "engine_version": ENGINE_VERSION,
            },
        )

    def certify_block84_outputs(
        self,
        *,
        portfolio: Optional[List[Mapping[str, Any]]] = None,
        execution_intents: Optional[List[Mapping[str, Any]]] = None,
        order_plan: Optional[List[Mapping[str, Any]]] = None,
        risk_result: Optional[Any] = None,
        governance_result: Optional[Any] = None,
        validation_result: Optional[Any] = None,
        simulation_result: Optional[Any] = None,
        assumptions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Block85Certification:
        orders = list(order_plan or execution_intents or portfolio or [])

        # If the caller supplies execution intents, normalize their explicit
        # execution permission into the certification layer.
        normalized: List[Dict[str, Any]] = []
        for item in orders:
            row = _to_dict(item)
            if "execution_allowed" in row and not bool(row["execution_allowed"]):
                normalized.append({
                    **row,
                    "action": row.get("action", "HOLD"),
                    "quantity": row.get("quantity", 0.0),
                })
            else:
                normalized.append(row)

        return self.certify(
            orders=normalized,
            risk=risk_result,
            governance=governance_result,
            validation=validation_result,
            simulation=simulation_result,
            assumptions=assumptions,
            metadata=metadata,
        )


__all__ = [
    "ENGINE_VERSION",
    "Block85Certification",
    "EROSBlock85ExecutionCertificationEngine",
]

