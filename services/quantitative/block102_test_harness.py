from services.quantitative.block102_frontend_contract import (
    EROSBlock102FrontendContract,
)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    print("=" * 62)
    print("EROS 3.0 - BLOCK 102 SELF TEST")
    print("=" * 62)

    engine = EROSBlock102FrontendContract()

    block94 = {
        "status": "CERTIFIED",
        "certificate_status": "CERTIFIED",
        "certificate_id": "EROS94-TEST",
        "scenario_count": 5,
        "downside_pnl": -1500000.0,
        "upside_pnl": 1000000.0,
        "execution_blocked": True,
    }

    block95 = {
        "status": "CERTIFIED",
        "gate_id": "EROS95-TEST",
        "execution_blocked": True,
    }

    block96 = {
        "status": "CERTIFIED",
        "decision_status": "ADMITTED",
        "decision": "ADMITTED",
        "decision_id": "EROS96-TEST",
        "source_block": "95",
        "execution_blocked": True,
    }

    block97 = {
        "status": "CERTIFIED",
        "readiness_status": "READY",
        "readiness_id": "EROS97-TEST",
        "source_block": "96",
        "source_decision_id": "EROS96-TEST",
        "execution_blocked": True,
    }

    block98 = {
        "status": "CERTIFIED",
        "governance_status": "APPROVED",
        "governance_id": "EROS98-TEST",
        "execution_action": "EXECUTE",
        "source_block": "97",
        "source_readiness_id": "EROS97-TEST",
        "source_decision_id": "EROS96-TEST",
        "execution_blocked": True,
    }

    block99 = {
        "status": "CERTIFIED",
        "intent_status": "AUTHORIZED",
        "authorization_status": "AUTHORIZED",
        "intent_id": "EROS99-TEST",
        "intent_action": "PREPARE",
        "source_block": "98",
        "symbol": "RELIANCE.NS",
        "action": "BUY",
        "quantity": 100.0,
        "reference_price": 2500.0,
        "execution_blocked": True,
    }

    block100 = {
        "status": "CERTIFIED",
        "execution_status": "SIMULATED",
        "execution_id": "EROS100-TEST",
        "source_block": "99",
        "symbol": "RELIANCE.NS",
        "action": "BUY",
        "requested_quantity": 100.0,
        "filled_quantity": 100.0,
        "reference_price": 2500.0,
        "fill_price": 2501.25,
        "fill_status": "FILLED",
        "slippage_bps": 5.0,
        "transaction_cost": 250.0,
        "net_value": 250125.0,
        "execution_blocked": True,
    }

    block101 = {
        "status": "CERTIFIED",
        "reconciliation_status": "RECONCILED",
        "reconciliation_id": "EROS101-TEST",
        "source_block": "100",
        "source_execution_id": "EROS100-TEST",
        "quantity_reconciled": True,
        "price_reconciled": True,
        "value_reconciled": True,
        "cost_reconciled": True,
        "lineage_reconciled": True,
        "execution_blocked": True,
    }

    result = engine.build(
        block94=block94,
        block95=block95,
        block96=block96,
        block97=block97,
        block98=block98,
        block99=block99,
        block100=block100,
        block101=block101,
    )

    check(result["status"] == "CERTIFIED", "Block 102 must certify")
    check(result["block_id"] == "102", "Block ID must be 102")
    check(
        len(result["pipeline_status"]) == 8,
        "Pipeline must contain Blocks 94-101",
    )

    check(
        result["governance"]["status"] == "APPROVED",
        "Governance must be APPROVED",
    )
    check(
        result["governance"]["execution_action"] == "EXECUTE",
        "Governance action must be EXECUTE",
    )

    check(
        result["intent"]["status"] == "AUTHORIZED",
        "Intent must be AUTHORIZED",
    )
    check(
        result["execution"]["status"] == "SIMULATED",
        "Execution must be SIMULATED",
    )
    check(
        result["execution"]["fill_status"] == "FILLED",
        "Execution fill must be FILLED",
    )
    check(
        result["reconciliation"]["status"] == "RECONCILED",
        "Reconciliation must be RECONCILED",
    )

    check(
        result["lineage"]["block98"] == "EROS98-TEST",
        "Block 98 lineage must be preserved",
    )
    check(
        result["lineage"]["block99"] == "EROS99-TEST",
        "Block 99 lineage must be preserved",
    )
    check(
        result["lineage"]["block100"] == "EROS100-TEST",
        "Block 100 lineage must be preserved",
    )
    check(
        result["lineage"]["block101"] == "EROS101-TEST",
        "Block 101 lineage must be preserved",
    )

    safety = result["safety"]

    check(
        safety["portfolio_mutation"] is False,
        "Portfolio mutation must remain false",
    )
    check(
        safety["valuation_mutation"] is False,
        "Valuation mutation must remain false",
    )
    check(
        safety["performance_mutation"] is False,
        "Performance mutation must remain false",
    )
    check(
        safety["risk_mutation"] is False,
        "Risk mutation must remain false",
    )
    check(
        safety["optimization"] is False,
        "Optimization must remain false",
    )
    check(
        safety["order_creation"] is False,
        "Order creation must remain false",
    )
    check(
        safety["broker_submission"] is False,
        "Broker submission must remain false",
    )
    check(
        safety["live_order_submission"] is False,
        "Live execution must remain false",
    )
    check(
        safety["execution_blocked"] is True,
        "Execution blocked invariant must remain true",
    )
    check(
        safety["non_mutation_invariant"] is True,
        "Non-mutation invariant must remain true",
    )

    print("")
    print("STATUS          : PASS")
    print("BLOCK           : 102")
    print("PIPELINE        : 94 -> 101")
    print("GOVERNANCE      : APPROVED")
    print("ACTION          : EXECUTE")
    print("INTENT          : AUTHORIZED")
    print("EXECUTION       : SIMULATED")
    print("FILL            : FILLED")
    print("RECONCILIATION  : RECONCILED")
    print("NON-MUTATION    : True")
    print("BROKER          : False")
    print("LIVE EXEC       : False")
    print("EXECUTION BLOCKED: True")
    print("")
    print("EROS 3.0 Block 102 self-test passed")
    print("=" * 62)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
