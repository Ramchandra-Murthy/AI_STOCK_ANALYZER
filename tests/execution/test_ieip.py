from __future__ import annotations

from services.execution.execution_engine import InstitutionalExecutionEngine
from services.execution.models import ExecutionOrder
from services.execution.transaction_cost import TransactionCostAnalyzer


def test_execution_order_immutability() -> None:
    order = ExecutionOrder(
        symbol="RELIANCE.NS",
        action="BUY",
        quantity=150.0,
        limit_price=2940.0,
        execution_priority="HIGH",
        estimated_slippage=3.5,
        estimated_transaction_cost=120.0,
        rationale=["Strong conviction"],
    )
    assert order.symbol == "RELIANCE.NS"
    assert order.action == "BUY"
    assert order.quantity == 150.0
    assert order.timestamp is not None
    assert isinstance(order.metadata, dict)


def test_institutional_execution_engine() -> None:
    allocations = [{"symbol": "RELIANCE.NS", "action": "BUY", "trade_weight": 0.05}]
    orders = InstitutionalExecutionEngine.generate_orders(allocations, "VWAP-oriented")
    assert len(orders) == 1
    assert orders[0].symbol == "RELIANCE.NS"
    assert orders[0].action == "BUY"
    assert orders[0].quantity > 0
    assert orders[0].estimated_transaction_cost > 0


def test_transaction_cost_analyzer() -> None:
    tca = TransactionCostAnalyzer.analyze_order_costs(1000000.0, 0.02)
    assert tca["total_transaction_cost"] > 0
    assert tca["brokerage"] > 0
    assert tca["market_impact"] > 0
