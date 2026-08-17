from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Mapping


ENGINE_VERSION = "EROS-3.0-BLOCK-91"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _hash_payload(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(canonical).hexdigest().upper()


@dataclass(frozen=True)
class PortfolioValuationRecord:
    valuation_id: str
    valuation_status: str
    portfolio_id: str

    settlement_id: str
    audit_id: str
    decision_id: str

    cash_balance: float
    invested_cost: float
    market_value: float
    portfolio_equity: float

    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    return_pct: float

    cash_weight: float
    invested_weight: float
    position_count: int

    positions: List[Dict[str, Any]] = field(default_factory=list)

    engine_version: str = ENGINE_VERSION
    timestamp_utc: str = field(default_factory=_utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Block91PortfolioValuationCertificate:
    status: str
    valuation_status: str

    valuation_id: str
    portfolio_id: str

    settlement_id: str
    audit_id: str
    decision_id: str

    valuation_hash: str

    position_count: int
    portfolio_equity: float
    total_pnl: float
    return_pct: float

    mutation_allowed: bool = False
    broker_submission: bool = False
    live_order_submission: bool = False

    created_at_utc: str = field(default_factory=_utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EROSBlock91PortfolioValuationEngine:
    """
    EROS 3.0 Block 91.

    Converts certified Block 90 portfolio state into a deterministic
    valuation and performance record.

    Block 91 is observational.

    It MUST NOT:
        - submit orders
        - call a broker
        - perform execution
        - perform settlement
        - mutate Block 90 portfolio state
    """

    def __init__(self) -> None:
        self._processed_valuations: Dict[str, Dict[str, Any]] = {}
        self._valuation_history: List[Dict[str, Any]] = []

    @staticmethod
    def _state(payload: Mapping[str, Any]) -> Dict[str, Any]:
        return _dict(payload.get("state"))

    @staticmethod
    def _portfolio(payload: Mapping[str, Any]) -> Dict[str, Any]:
        return _dict(payload.get("portfolio"))

    @staticmethod
    def _certificate(payload: Mapping[str, Any]) -> Dict[str, Any]:
        return _dict(payload.get("certificate"))

    @staticmethod
    def _settlement_id(
        state: Mapping[str, Any],
        certificate: Mapping[str, Any],
    ) -> str:
        return _text(
            state.get(
                "settlement_id",
                certificate.get("settlement_id", ""),
            )
        )

    @staticmethod
    def _audit_id(
        state: Mapping[str, Any],
        certificate: Mapping[str, Any],
    ) -> str:
        return _text(
            state.get(
                "audit_id",
                certificate.get("audit_id", ""),
            )
        )

    @staticmethod
    def _decision_id(
        state: Mapping[str, Any],
        certificate: Mapping[str, Any],
    ) -> str:
        return _text(
            state.get(
                "decision_id",
                certificate.get("decision_id", ""),
            )
        )

    @staticmethod
    def _portfolio_id(
        state: Mapping[str, Any],
        portfolio: Mapping[str, Any],
    ) -> str:
        return _text(
            state.get(
                "portfolio_id",
                portfolio.get("portfolio_id", ""),
            )
        )

    @staticmethod
    def _status(state: Mapping[str, Any]) -> str:
        return _text(
            state.get(
                "state_status",
                state.get("status", ""),
            )
        ).upper()

    @staticmethod
    def _allowed(
        state: Mapping[str, Any],
        certificate: Mapping[str, Any],
    ) -> bool:
        return bool(
            state.get(
                "state_allowed",
                certificate.get("settlement_allowed", True),
            )
        )

    @staticmethod
    def _market_price(position: Mapping[str, Any]) -> float:
        return _number(
            position.get(
                "current_price",
                position.get("market_price", 0.0),
            )
        )

    @staticmethod
    def _quantity(position: Mapping[str, Any]) -> float:
        return _number(position.get("quantity", 0.0))

    @staticmethod
    def _average_cost(position: Mapping[str, Any]) -> float:
        return _number(position.get("average_cost", 0.0))

    @staticmethod
    def _realized_pnl(position: Mapping[str, Any]) -> float:
        return _number(position.get("realized_pnl", 0.0))

    def _valuation_id(
        self,
        portfolio_id: str,
        settlement_id: str,
    ) -> str:
        raw = f"{portfolio_id}|{settlement_id}|{ENGINE_VERSION}"
        return (
            "EROS91-"
            + hashlib.sha256(raw.encode("utf-8"))
            .hexdigest()[:16]
            .upper()
        )

    def _blocked(
        self,
        *,
        portfolio_id: str,
        settlement_id: str,
        audit_id: str,
        decision_id: str,
        reason: str,
    ) -> Dict[str, Any]:

        valuation_id = self._valuation_id(
            portfolio_id or "UNKNOWN",
            settlement_id or "UNKNOWN",
        )

        certificate = Block91PortfolioValuationCertificate(
            status="BLOCKED",
            valuation_status="BLOCKED",
            valuation_id=valuation_id,
            portfolio_id=portfolio_id,
            settlement_id=settlement_id,
            audit_id=audit_id,
            decision_id=decision_id,
            valuation_hash="",
            position_count=0,
            portfolio_equity=0.0,
            total_pnl=0.0,
            return_pct=0.0,
            mutation_allowed=False,
            broker_submission=False,
            live_order_submission=False,
        )

        return {
            "status": "BLOCKED",
            "valuation": {
                "valuation_id": valuation_id,
                "valuation_status": "BLOCKED",
                "portfolio_id": portfolio_id,
                "settlement_id": settlement_id,
                "audit_id": audit_id,
                "decision_id": decision_id,
                "reason": reason,
            },
            "certificate": certificate.to_dict(),
            "broker_submission": False,
            "live_order_submission": False,
            "mutation_allowed": False,
        }

    def value_portfolio(
        self,
        portfolio_state: Mapping[str, Any],
        market_prices: Mapping[str, Any],
    ) -> Dict[str, Any]:

        state = self._state(portfolio_state)
        portfolio = self._portfolio(portfolio_state)
        certificate_input = self._certificate(portfolio_state)

        settlement_id = self._settlement_id(
            state,
            certificate_input,
        )
        audit_id = self._audit_id(
            state,
            certificate_input,
        )
        decision_id = self._decision_id(
            state,
            certificate_input,
        )
        portfolio_id = self._portfolio_id(
            state,
            portfolio,
        )

        status = self._status(state)

        if status != "APPLIED":
            return self._blocked(
                portfolio_id=portfolio_id,
                settlement_id=settlement_id,
                audit_id=audit_id,
                decision_id=decision_id,
                reason=f"INVALID_STATE_STATUS:{status}",
            )

        if not self._allowed(state, certificate_input):
            return self._blocked(
                portfolio_id=portfolio_id,
                settlement_id=settlement_id,
                audit_id=audit_id,
                decision_id=decision_id,
                reason="STATE_NOT_ALLOWED",
            )

        if not settlement_id:
            return self._blocked(
                portfolio_id=portfolio_id,
                settlement_id="",
                audit_id=audit_id,
                decision_id=decision_id,
                reason="MISSING_SETTLEMENT_ID",
            )

        if not audit_id:
            return self._blocked(
                portfolio_id=portfolio_id,
                settlement_id=settlement_id,
                audit_id="",
                decision_id=decision_id,
                reason="MISSING_AUDIT_ID",
            )

        if not decision_id:
            return self._blocked(
                portfolio_id=portfolio_id,
                settlement_id=settlement_id,
                audit_id=audit_id,
                decision_id="",
                reason="MISSING_DECISION_ID",
            )

        valuation_id = self._valuation_id(
            portfolio_id,
            settlement_id,
        )

        if valuation_id in self._processed_valuations:
            return {
                **self._processed_valuations[valuation_id],
                "status": "DUPLICATE",
                "valuation": {
                    **self._processed_valuations[valuation_id]["valuation"],
                    "valuation_status": "DUPLICATE",
                },
                "certificate": {
                    **self._processed_valuations[valuation_id]["certificate"],
                    "status": "DUPLICATE",
                    "valuation_status": "DUPLICATE",
                },
            }

        raw_positions = state.get(
            "positions",
            portfolio.get("positions", []),
        )

        if not isinstance(raw_positions, list):
            return self._blocked(
                portfolio_id=portfolio_id,
                settlement_id=settlement_id,
                audit_id=audit_id,
                decision_id=decision_id,
                reason="INVALID_POSITIONS",
            )

        cash_balance = _number(
            portfolio.get(
                "cash_balance",
                state.get("cash_after", 0.0),
            )
        )

        positions: List[Dict[str, Any]] = []
        invested_cost = 0.0
        market_value = 0.0
        realized_pnl = 0.0

        for raw in raw_positions:
            position = _dict(raw)

            symbol = _text(position.get("symbol")).upper()

            if not symbol:
                return self._blocked(
                    portfolio_id=portfolio_id,
                    settlement_id=settlement_id,
                    audit_id=audit_id,
                    decision_id=decision_id,
                    reason="MISSING_POSITION_SYMBOL",
                )

            quantity = self._quantity(position)
            average_cost = self._average_cost(position)
            realized = self._realized_pnl(position)

            if quantity < 0.0:
                return self._blocked(
                    portfolio_id=portfolio_id,
                    settlement_id=settlement_id,
                    audit_id=audit_id,
                    decision_id=decision_id,
                    reason=f"NEGATIVE_POSITION:{symbol}",
                )

            price = _number(
                market_prices.get(
                    symbol,
                    self._market_price(position),
                )
            )

            if price <= 0.0:
                return self._blocked(
                    portfolio_id=portfolio_id,
                    settlement_id=settlement_id,
                    audit_id=audit_id,
                    decision_id=decision_id,
                    reason=f"INVALID_MARKET_PRICE:{symbol}",
                )

            cost = quantity * average_cost
            value = quantity * price
            unrealized = value - cost

            invested_cost += cost
            market_value += value
            realized_pnl += realized

            positions.append(
                {
                    "symbol": symbol,
                    "quantity": round(quantity, 6),
                    "average_cost": round(average_cost, 6),
                    "market_price": round(price, 6),
                    "cost_basis": round(cost, 6),
                    "market_value": round(value, 6),
                    "unrealized_pnl": round(unrealized, 6),
                    "realized_pnl": round(realized, 6),
                    "total_pnl": round(
                        unrealized + realized,
                        6,
                    ),
                }
            )

        portfolio_equity = cash_balance + market_value
        unrealized_pnl = market_value - invested_cost
        total_pnl = realized_pnl + unrealized_pnl

        return_pct = (
            (total_pnl / invested_cost) * 100.0
            if invested_cost > 0.0
            else 0.0
        )

        cash_weight = (
            (cash_balance / portfolio_equity) * 100.0
            if portfolio_equity > 0.0
            else 0.0
        )

        invested_weight = (
            (market_value / portfolio_equity) * 100.0
            if portfolio_equity > 0.0
            else 0.0
        )

        valuation_payload = {
            "valuation_id": valuation_id,
            "valuation_status": "VALUED",
            "portfolio_id": portfolio_id,
            "settlement_id": settlement_id,
            "audit_id": audit_id,
            "decision_id": decision_id,
            "cash_balance": round(cash_balance, 6),
            "invested_cost": round(invested_cost, 6),
            "market_value": round(market_value, 6),
            "portfolio_equity": round(portfolio_equity, 6),
            "realized_pnl": round(realized_pnl, 6),
            "unrealized_pnl": round(unrealized_pnl, 6),
            "total_pnl": round(total_pnl, 6),
            "return_pct": round(return_pct, 6),
            "cash_weight": round(cash_weight, 6),
            "invested_weight": round(invested_weight, 6),
            "position_count": len(positions),
            "positions": positions,
            "broker_submission": False,
            "live_order_submission": False,
            "mutation_allowed": False,
        }

        valuation_hash = _hash_payload(
            valuation_payload
        )

        record = PortfolioValuationRecord(
            valuation_id=valuation_id,
            valuation_status="VALUED",
            portfolio_id=portfolio_id,
            settlement_id=settlement_id,
            audit_id=audit_id,
            decision_id=decision_id,
            cash_balance=round(cash_balance, 6),
            invested_cost=round(invested_cost, 6),
            market_value=round(market_value, 6),
            portfolio_equity=round(portfolio_equity, 6),
            realized_pnl=round(realized_pnl, 6),
            unrealized_pnl=round(unrealized_pnl, 6),
            total_pnl=round(total_pnl, 6),
            return_pct=round(return_pct, 6),
            cash_weight=round(cash_weight, 6),
            invested_weight=round(invested_weight, 6),
            position_count=len(positions),
            positions=positions,
        )

        certificate = Block91PortfolioValuationCertificate(
            status="CERTIFIED",
            valuation_status="VALUED",
            valuation_id=valuation_id,
            portfolio_id=portfolio_id,
            settlement_id=settlement_id,
            audit_id=audit_id,
            decision_id=decision_id,
            valuation_hash=valuation_hash,
            position_count=len(positions),
            portfolio_equity=round(
                portfolio_equity,
                6,
            ),
            total_pnl=round(
                total_pnl,
                6,
            ),
            return_pct=round(
                return_pct,
                6,
            ),
            mutation_allowed=False,
            broker_submission=False,
            live_order_submission=False,
        )

        result = {
            "status": "PASS",
            "valuation": record.to_dict(),
            "certificate": certificate.to_dict(),
            "broker_submission": False,
            "live_order_submission": False,
            "mutation_allowed": False,
        }

        self._processed_valuations[
            valuation_id
        ] = result

        self._valuation_history.append(
            result
        )

        return result

    def snapshot(self) -> Dict[str, Any]:
        return {
            "valuation_count": len(
                self._processed_valuations
            ),
            "valuation_history_count": len(
                self._valuation_history
            ),
            "valuation_ids": sorted(
                self._processed_valuations
            ),
        }

    def valuation_history(self) -> List[Dict[str, Any]]:
        return list(self._valuation_history)
