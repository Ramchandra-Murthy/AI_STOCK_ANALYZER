from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping


ENGINE_VERSION = "EROS-3.0-BLOCK-90"
STATE_SCHEMA_VERSION = "1.0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def _dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _hash_payload(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class PortfolioPositionState:
    symbol: str
    quantity: float
    average_cost: float
    current_price: float
    realized_pnl: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "quantity": round(self.quantity, 6),
            "average_cost": round(self.average_cost, 6),
            "current_price": round(self.current_price, 6),
            "realized_pnl": round(self.realized_pnl, 6),
        }


@dataclass(frozen=True)
class PortfolioStateRecord:
    state_id: str
    portfolio_id: str
    state_schema_version: str
    engine_version: str
    timestamp_utc: str
    settlement_id: str
    audit_id: str
    decision_id: str
    symbol: str
    action: str
    state_status: str
    state_allowed: bool
    cash_balance_before: float
    cash_balance_after: float
    cash_delta: float
    position_quantity_before: float
    position_quantity_after: float
    position_delta: float
    average_cost_before: float
    average_cost_after: float
    execution_price: float
    transaction_cost: float
    realized_pnl: float
    positions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state_id": self.state_id,
            "portfolio_id": self.portfolio_id,
            "state_schema_version": self.state_schema_version,
            "engine_version": self.engine_version,
            "timestamp_utc": self.timestamp_utc,
            "settlement_id": self.settlement_id,
            "audit_id": self.audit_id,
            "decision_id": self.decision_id,
            "symbol": self.symbol,
            "action": self.action,
            "state_status": self.state_status,
            "state_allowed": self.state_allowed,
            "cash_balance_before": self.cash_balance_before,
            "cash_balance_after": self.cash_balance_after,
            "cash_delta": self.cash_delta,
            "position_quantity_before": self.position_quantity_before,
            "position_quantity_after": self.position_quantity_after,
            "position_delta": self.position_delta,
            "average_cost_before": self.average_cost_before,
            "average_cost_after": self.average_cost_after,
            "execution_price": self.execution_price,
            "transaction_cost": self.transaction_cost,
            "realized_pnl": self.realized_pnl,
            "positions": list(self.positions),
        }


@dataclass(frozen=True)
class Block90PortfolioCertificate:
    status: str
    state_status: str
    state_id: str
    portfolio_id: str
    settlement_id: str
    audit_id: str
    decision_id: str
    state_allowed: bool
    certificate_hash: str
    created_at_utc: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "state_status": self.state_status,
            "state_id": self.state_id,
            "portfolio_id": self.portfolio_id,
            "settlement_id": self.settlement_id,
            "audit_id": self.audit_id,
            "decision_id": self.decision_id,
            "state_allowed": self.state_allowed,
            "certificate_hash": self.certificate_hash,
            "created_at_utc": self.created_at_utc,
        }


class EROSBlock90PortfolioStateEngine:
    """
    Controlled portfolio-state boundary after Block 89 settlement.

    Block 90 does not create or authorize trades.

    It only applies a portfolio-state transition when:
        settlement_status == SETTLED
        settlement_allowed == True
        certificate status == CERTIFIED

    Duplicate settlement IDs are idempotent and cannot create
    a second portfolio-state mutation.

    Blocked, invalid, or duplicate requests never mutate state.
    """

    VALID_ACTIONS = {"BUY", "SELL", "REDUCE"}

    def __init__(
        self,
        portfolio_id: str = "EROS-PORTFOLIO-DEFAULT",
        initial_cash: float = 0.0,
    ) -> None:
        self.portfolio_id = _text(
            portfolio_id,
            "EROS-PORTFOLIO-DEFAULT",
        )
        self.cash_balance = round(float(initial_cash), 6)
        self.positions: Dict[str, PortfolioPositionState] = {}
        self._processed_settlements: Dict[str, str] = {}
        self._state_history: List[PortfolioStateRecord] = []

    @staticmethod
    def _settlement(
        payload: Mapping[str, Any],
    ) -> Dict[str, Any]:
        value = payload.get("settlement", payload)
        return _dict(value)

    @staticmethod
    def _certificate(
        payload: Mapping[str, Any],
    ) -> Dict[str, Any]:
        return _dict(payload.get("certificate", {}))

    @staticmethod
    def _settlement_id(
        settlement: Mapping[str, Any],
        certificate: Mapping[str, Any],
    ) -> str:
        return _text(
            settlement.get(
                "settlement_id",
                certificate.get("settlement_id", ""),
            )
        )

    @staticmethod
    def _audit_id(
        settlement: Mapping[str, Any],
        certificate: Mapping[str, Any],
    ) -> str:
        return _text(
            settlement.get(
                "audit_id",
                certificate.get("audit_id", ""),
            )
        )

    @staticmethod
    def _decision_id(
        settlement: Mapping[str, Any],
        certificate: Mapping[str, Any],
    ) -> str:
        return _text(
            settlement.get(
                "decision_id",
                certificate.get("decision_id", ""),
            )
        )

    @staticmethod
    def _symbol(
        settlement: Mapping[str, Any],
    ) -> str:
        return _text(
            settlement.get("symbol", "")
        ).upper()

    @staticmethod
    def _action(
        settlement: Mapping[str, Any],
    ) -> str:
        return _text(
            settlement.get("action", "")
        ).upper()

    @staticmethod
    def _allowed(
        settlement: Mapping[str, Any],
        certificate: Mapping[str, Any],
    ) -> bool:
        return bool(
            settlement.get(
                "settlement_allowed",
                certificate.get(
                    "settlement_allowed",
                    False,
                ),
            )
        )

    @staticmethod
    def _status(
        settlement: Mapping[str, Any],
        certificate: Mapping[str, Any],
    ) -> str:
        return _text(
            settlement.get(
                "settlement_status",
                certificate.get(
                    "settlement_status",
                    "BLOCKED",
                ),
            ),
            "BLOCKED",
        ).upper()

    def _build_state(
        self,
        *,
        settlement: Mapping[str, Any],
        certificate: Mapping[str, Any],
        before_cash: float,
        before_position: PortfolioPositionState | None,
    ) -> PortfolioStateRecord:

        settlement_id = self._settlement_id(
            settlement,
            certificate,
        )
        audit_id = self._audit_id(
            settlement,
            certificate,
        )
        decision_id = self._decision_id(
            settlement,
            certificate,
        )
        symbol = self._symbol(settlement)
        action = self._action(settlement)

        position_delta = _number(
            settlement.get("position_delta")
        )
        cash_delta = _number(
            settlement.get("cash_delta")
        )
        execution_price = _number(
            settlement.get("average_fill_price")
        )
        transaction_cost = _number(
            settlement.get("transaction_cost")
        )
        realized_pnl = _number(
            settlement.get("realized_pnl")
        )

        before_quantity = (
            before_position.quantity
            if before_position is not None
            else 0.0
        )

        before_average_cost = (
            before_position.average_cost
            if before_position is not None
            else 0.0
        )

        after_quantity = round(
            before_quantity + position_delta,
            6,
        )

        if after_quantity < -0.000001:
            raise ValueError(
                "SETTLEMENT_POSITION_UNDERFLOW"
            )

        if action == "BUY":
            old_cost = (
                before_quantity * before_average_cost
            )
            new_cost = (
                old_cost
                + abs(position_delta) * execution_price
            )

            average_cost_after = (
                new_cost / after_quantity
                if after_quantity > 0
                else 0.0
            )

        elif action in {"SELL", "REDUCE"}:
            average_cost_after = (
                before_average_cost
                if after_quantity > 0
                else 0.0
            )

        else:
            average_cost_after = before_average_cost

        after_cash = round(
            before_cash + cash_delta,
            6,
        )

        positions = dict(self.positions)

        if after_quantity <= 0.000001:
            positions.pop(symbol, None)
        else:
            positions[symbol] = PortfolioPositionState(
                symbol=symbol,
                quantity=after_quantity,
                average_cost=round(
                    average_cost_after,
                    6,
                ),
                current_price=round(
                    execution_price,
                    6,
                ),
                realized_pnl=round(
                    (
                        (
                            before_position.realized_pnl
                            if before_position
                            else 0.0
                        )
                        + realized_pnl
                    ),
                    6,
                ),
            )

        position_dicts = [
            positions[key].to_dict()
            for key in sorted(positions)
        ]

        seed = {
            "schema": STATE_SCHEMA_VERSION,
            "engine": ENGINE_VERSION,
            "portfolio_id": self.portfolio_id,
            "settlement_id": settlement_id,
            "audit_id": audit_id,
            "decision_id": decision_id,
            "symbol": symbol,
            "action": action,
            "cash_before": before_cash,
            "cash_after": after_cash,
            "position_before": before_quantity,
            "position_after": after_quantity,
            "average_cost_before": before_average_cost,
            "average_cost_after": average_cost_after,
            "positions": position_dicts,
        }

        state_hash = _hash_payload(seed)

        return PortfolioStateRecord(
            state_id=f"EROS90-{state_hash[:16]}",
            portfolio_id=self.portfolio_id,
            state_schema_version=STATE_SCHEMA_VERSION,
            engine_version=ENGINE_VERSION,
            timestamp_utc=_utc_now(),
            settlement_id=settlement_id,
            audit_id=audit_id,
            decision_id=decision_id,
            symbol=symbol,
            action=action,
            state_status="APPLIED",
            state_allowed=True,
            cash_balance_before=round(
                before_cash,
                6,
            ),
            cash_balance_after=after_cash,
            cash_delta=round(
                cash_delta,
                6,
            ),
            position_quantity_before=round(
                before_quantity,
                6,
            ),
            position_quantity_after=after_quantity,
            position_delta=round(
                position_delta,
                6,
            ),
            average_cost_before=round(
                before_average_cost,
                6,
            ),
            average_cost_after=round(
                average_cost_after,
                6,
            ),
            execution_price=round(
                execution_price,
                6,
            ),
            transaction_cost=round(
                transaction_cost,
                6,
            ),
            realized_pnl=round(
                realized_pnl,
                6,
            ),
            positions=position_dicts,
        )

    def _certificate_for(
        self,
        *,
        status: str,
        state_status: str,
        state_id: str,
        settlement_id: str,
        audit_id: str,
        decision_id: str,
        state_allowed: bool,
    ) -> Block90PortfolioCertificate:

        seed = {
            "status": status,
            "state_status": state_status,
            "state_id": state_id,
            "portfolio_id": self.portfolio_id,
            "settlement_id": settlement_id,
            "audit_id": audit_id,
            "decision_id": decision_id,
            "state_allowed": state_allowed,
        }

        return Block90PortfolioCertificate(
            status=status,
            state_status=state_status,
            state_id=state_id,
            portfolio_id=self.portfolio_id,
            settlement_id=settlement_id,
            audit_id=audit_id,
            decision_id=decision_id,
            state_allowed=state_allowed,
            certificate_hash=_hash_payload(seed),
            created_at_utc=_utc_now(),
        )

    def apply_settlement(
        self,
        payload: Mapping[str, Any],
    ) -> Dict[str, Any]:

        settlement = self._settlement(payload)
        certificate = self._certificate(payload)

        settlement_id = self._settlement_id(
            settlement,
            certificate,
        )
        audit_id = self._audit_id(
            settlement,
            certificate,
        )
        decision_id = self._decision_id(
            settlement,
            certificate,
        )

        status = self._status(
            settlement,
            certificate,
        )
        allowed = self._allowed(
            settlement,
            certificate,
        )

        if settlement_id in self._processed_settlements:
            existing_state_id = self._processed_settlements[
                settlement_id
            ]

            cert = self._certificate_for(
                status="DUPLICATE",
                state_status="DUPLICATE",
                state_id=existing_state_id,
                settlement_id=settlement_id,
                audit_id=audit_id,
                decision_id=decision_id,
                state_allowed=False,
            )

            return {
                "status": "DUPLICATE",
                "state": None,
                "certificate": cert.to_dict(),
                "portfolio": self.snapshot(),
            }

        if status != "SETTLED":
            cert = self._certificate_for(
                status="BLOCKED",
                state_status="BLOCKED",
                state_id="",
                settlement_id=settlement_id,
                audit_id=audit_id,
                decision_id=decision_id,
                state_allowed=False,
            )

            return {
                "status": "BLOCKED",
                "state": None,
                "certificate": cert.to_dict(),
                "portfolio": self.snapshot(),
            }

        if not allowed:
            cert = self._certificate_for(
                status="BLOCKED",
                state_status="BLOCKED",
                state_id="",
                settlement_id=settlement_id,
                audit_id=audit_id,
                decision_id=decision_id,
                state_allowed=False,
            )

            return {
                "status": "BLOCKED",
                "state": None,
                "certificate": cert.to_dict(),
                "portfolio": self.snapshot(),
            }

        if (
            _text(certificate.get("status")).upper()
            != "CERTIFIED"
        ):
            cert = self._certificate_for(
                status="BLOCKED",
                state_status="BLOCKED",
                state_id="",
                settlement_id=settlement_id,
                audit_id=audit_id,
                decision_id=decision_id,
                state_allowed=False,
            )

            return {
                "status": "BLOCKED",
                "state": None,
                "certificate": cert.to_dict(),
                "portfolio": self.snapshot(),
            }

        symbol = self._symbol(settlement)
        action = self._action(settlement)

        if not settlement_id:
            raise ValueError("MISSING_SETTLEMENT_ID")

        if not audit_id:
            raise ValueError("MISSING_AUDIT_ID")

        if not decision_id:
            raise ValueError("MISSING_DECISION_ID")

        if not symbol:
            raise ValueError("MISSING_SYMBOL")

        if action not in self.VALID_ACTIONS:
            raise ValueError(
                f"INVALID_SETTLEMENT_ACTION:{action}"
            )

        before_position = self.positions.get(symbol)
        before_cash = self.cash_balance

        state = self._build_state(
            settlement=settlement,
            certificate=certificate,
            before_cash=before_cash,
            before_position=before_position,
        )

        self.cash_balance = state.cash_balance_after

        if state.position_quantity_after <= 0.000001:
            self.positions.pop(symbol, None)
        else:
            position_data = next(
                item
                for item in state.positions
                if item["symbol"] == symbol
            )

            self.positions[symbol] = (
                PortfolioPositionState(
                    symbol=position_data["symbol"],
                    quantity=position_data["quantity"],
                    average_cost=position_data["average_cost"],
                    current_price=position_data["current_price"],
                    realized_pnl=position_data["realized_pnl"],
                )
            )

        self._processed_settlements[
            settlement_id
        ] = state.state_id

        self._state_history.append(state)

        cert = self._certificate_for(
            status="CERTIFIED",
            state_status="APPLIED",
            state_id=state.state_id,
            settlement_id=settlement_id,
            audit_id=audit_id,
            decision_id=decision_id,
            state_allowed=True,
        )

        return {
            "status": "PASS",
            "state": state.to_dict(),
            "certificate": cert.to_dict(),
            "portfolio": self.snapshot(),
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "portfolio_id": self.portfolio_id,
            "cash_balance": round(
                self.cash_balance,
                6,
            ),
            "position_count": len(self.positions),
            "positions": [
                self.positions[key].to_dict()
                for key in sorted(self.positions)
            ],
            "processed_settlement_count": len(
                self._processed_settlements
            ),
            "state_history_count": len(
                self._state_history
            ),
        }

    def state_history(self) -> List[Dict[str, Any]]:
        return [
            state.to_dict()
            for state in self._state_history
        ]
