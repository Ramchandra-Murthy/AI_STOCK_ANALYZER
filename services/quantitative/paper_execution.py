from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List


ENGINE_VERSION = "EROS-3.0-BLOCK-69"


@dataclass
class PaperFill:
    symbol: str
    action: str
    requested_quantity: float
    filled_quantity: float
    reference_price: float
    fill_price: float
    gross_value: float
    slippage_value: float
    slippage_bps: float
    transaction_cost: float
    net_value: float
    fill_status: str
    broker_submission: bool
    engine_version: str = ENGINE_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EROSPaperExecutionEngine:
    """
    EROS 3.0 Block 69.

    Paper execution and transaction-cost-analysis engine.

    This engine NEVER submits an order to a broker.

    It converts an approved execution intent into a simulated fill
    and calculates deterministic execution-quality metrics.
    """

    ALLOWED_ACTIONS = {
        "BUY",
        "SELL",
        "HOLD",
    }

    def __init__(
        self,
        buy_slippage_bps: float = 5.0,
        sell_slippage_bps: float = 5.0,
        transaction_cost_bps: float = 10.0,
        max_fill_ratio: float = 1.0,
    ) -> None:

        if buy_slippage_bps < 0:
            raise ValueError(
                "buy_slippage_bps must be >= 0"
            )

        if sell_slippage_bps < 0:
            raise ValueError(
                "sell_slippage_bps must be >= 0"
            )

        if transaction_cost_bps < 0:
            raise ValueError(
                "transaction_cost_bps must be >= 0"
            )

        if not 0 < max_fill_ratio <= 1:
            raise ValueError(
                "max_fill_ratio must be > 0 and <= 1"
            )

        self.buy_slippage_bps = float(buy_slippage_bps)
        self.sell_slippage_bps = float(sell_slippage_bps)
        self.transaction_cost_bps = float(
            transaction_cost_bps
        )
        self.max_fill_ratio = float(max_fill_ratio)

    def _blocked(
        self,
        symbol: str,
        action: str,
        quantity: float,
        reference_price: float,
        status: str,
    ) -> Dict[str, Any]:

        return {
            "symbol": symbol,
            "action": action,
            "requested_quantity": quantity,
            "filled_quantity": 0.0,
            "reference_price": reference_price,
            "fill_price": 0.0,
            "gross_value": 0.0,
            "slippage_value": 0.0,
            "slippage_bps": 0.0,
            "transaction_cost": 0.0,
            "net_value": 0.0,
            "fill_status": status,
            "broker_submission": False,
            "engine_version": ENGINE_VERSION,
        }

    def simulate_fill(
        self,
        intent: Dict[str, Any],
        fill_ratio: float = 1.0,
    ) -> Dict[str, Any]:

        symbol = str(
            intent.get("symbol", "")
        ).strip().upper()

        action = str(
            intent.get("action", "")
        ).upper().strip()

        requested_quantity = float(
            intent.get(
                "quantity",
                intent.get(
                    "requested_quantity",
                    0.0,
                ),
            )
            or 0.0
        )

        reference_price = float(
            intent.get(
                "reference_price",
                intent.get(
                    "price",
                    0.0,
                ),
            )
            or 0.0
        )

        execution_allowed = bool(
            intent.get(
                "execution_allowed",
                False,
            )
        )

        if not symbol:
            return self._blocked(
                symbol,
                action,
                requested_quantity,
                reference_price,
                "BLOCKED_MISSING_SYMBOL",
            )

        if action not in self.ALLOWED_ACTIONS:
            return self._blocked(
                symbol,
                action,
                requested_quantity,
                reference_price,
                "BLOCKED_INVALID_ACTION",
            )

        if action == "HOLD":
            return self._blocked(
                symbol,
                action,
                requested_quantity,
                reference_price,
                "HOLD_NO_FILL",
            )

        if not execution_allowed:
            return self._blocked(
                symbol,
                action,
                requested_quantity,
                reference_price,
                "BLOCKED_EXECUTION_NOT_ALLOWED",
            )

        if requested_quantity <= 0:
            return self._blocked(
                symbol,
                action,
                requested_quantity,
                reference_price,
                "BLOCKED_INVALID_QUANTITY",
            )

        if reference_price <= 0:
            return self._blocked(
                symbol,
                action,
                requested_quantity,
                reference_price,
                "BLOCKED_INVALID_PRICE",
            )

        if not 0 < fill_ratio <= 1:
            return self._blocked(
                symbol,
                action,
                requested_quantity,
                reference_price,
                "BLOCKED_INVALID_FILL_RATIO",
            )

        fill_ratio = min(
            float(fill_ratio),
            self.max_fill_ratio,
        )

        filled_quantity = round(
            requested_quantity * fill_ratio,
            6,
        )

        if filled_quantity <= 0:
            return self._blocked(
                symbol,
                action,
                requested_quantity,
                reference_price,
                "BLOCKED_ZERO_FILL",
            )

        if action == "BUY":
            slippage_bps = self.buy_slippage_bps
            fill_price = (
                reference_price
                * (1.0 + slippage_bps / 10000.0)
            )
        else:
            slippage_bps = self.sell_slippage_bps
            fill_price = (
                reference_price
                * (1.0 - slippage_bps / 10000.0)
            )

        fill_price = round(
            fill_price,
            6,
        )

        gross_value = round(
            filled_quantity * fill_price,
            6,
        )

        benchmark_value = (
            filled_quantity
            * reference_price
        )

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
            gross_value
            * self.transaction_cost_bps
            / 10000.0,
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

        if fill_ratio >= 1.0:
            fill_status = "FILLED"
        else:
            fill_status = "PARTIAL"

        return PaperFill(
            symbol=symbol,
            action=action,
            requested_quantity=requested_quantity,
            filled_quantity=filled_quantity,
            reference_price=round(
                reference_price,
                6,
            ),
            fill_price=fill_price,
            gross_value=gross_value,
            slippage_value=slippage_value,
            slippage_bps=slippage_bps,
            transaction_cost=transaction_cost,
            net_value=net_value,
            fill_status=fill_status,
            broker_submission=False,
        ).to_dict()

    def execute_intents(
        self,
        intents: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        fills: List[Dict[str, Any]] = []

        for intent in intents:

            fill_ratio = float(
                intent.get(
                    "fill_ratio",
                    1.0,
                )
            )

            fill = self.simulate_fill(
                intent,
                fill_ratio=fill_ratio,
            )

            fills.append(fill)

        filled = [
            item
            for item in fills
            if item["fill_status"] == "FILLED"
        ]

        partial = [
            item
            for item in fills
            if item["fill_status"] == "PARTIAL"
        ]

        blocked = [
            item
            for item in fills
            if item["fill_status"].startswith(
                "BLOCKED"
            )
        ]

        hold = [
            item
            for item in fills
            if item["fill_status"] == "HOLD_NO_FILL"
        ]

        total_gross = round(
            sum(
                item["gross_value"]
                for item in fills
            ),
            6,
        )

        total_slippage = round(
            sum(
                item["slippage_value"]
                for item in fills
            ),
            6,
        )

        total_cost = round(
            sum(
                item["transaction_cost"]
                for item in fills
            ),
            6,
        )

        total_net = round(
            sum(
                item["net_value"]
                for item in fills
            ),
            6,
        )

        execution_count = (
            len(filled)
            + len(partial)
        )

        if execution_count > 0:
            average_slippage_bps = round(
                sum(
                    item["slippage_bps"]
                    for item in fills
                    if item["fill_status"]
                    in {"FILLED", "PARTIAL"}
                )
                / execution_count,
                6,
            )
        else:
            average_slippage_bps = 0.0

        return {
            "engine_version": ENGINE_VERSION,
            "status": "SUCCESS",
            "broker_submission": False,
            "execution_mode": "PAPER",
            "intent_count": len(intents),
            "filled_count": len(filled),
            "partial_count": len(partial),
            "blocked_count": len(blocked),
            "hold_count": len(hold),
            "total_gross_value": total_gross,
            "total_slippage_value": total_slippage,
            "average_slippage_bps": average_slippage_bps,
            "total_transaction_cost": total_cost,
            "total_net_value": total_net,
            "fills": fills,
        }

    def generate_tca(
        self,
        execution_result: Dict[str, Any],
    ) -> Dict[str, Any]:

        fills = execution_result.get(
            "fills",
            [],
        )

        executed = [
            item
            for item in fills
            if item["fill_status"]
            in {"FILLED", "PARTIAL"}
        ]

        requested_quantity = round(
            sum(
                item["requested_quantity"]
                for item in fills
            ),
            6,
        )

        filled_quantity = round(
            sum(
                item["filled_quantity"]
                for item in fills
            ),
            6,
        )

        fill_rate = (
            filled_quantity
            / requested_quantity
            if requested_quantity > 0
            else 0.0
        )

        total_cost = round(
            sum(
                item["transaction_cost"]
                for item in executed
            ),
            6,
        )

        total_slippage = round(
            sum(
                item["slippage_value"]
                for item in executed
            ),
            6,
        )

        total_value = round(
            sum(
                item["gross_value"]
                for item in executed
            ),
            6,
        )

        return {
            "engine_version": ENGINE_VERSION,
            "status": "SUCCESS",
            "execution_mode": "PAPER",
            "broker_submission": False,
            "requested_quantity": requested_quantity,
            "filled_quantity": filled_quantity,
            "fill_rate": round(
                fill_rate,
                6,
            ),
            "executed_orders": len(executed),
            "total_slippage": total_slippage,
            "total_transaction_cost": total_cost,
            "total_execution_cost": round(
                total_slippage + total_cost,
                6,
            ),
            "executed_value": total_value,
        }


__all__ = [
    "EROSPaperExecutionEngine",
    "PaperFill",
    "ENGINE_VERSION",
]
