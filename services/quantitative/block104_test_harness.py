from services.quantitative.block104_eros_command_center import (
    EROSBlock104CommandCenter,
)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def main():

    print("")
    print("=" * 62)
    print("EROS 3.0 - BLOCK 104 SELF TEST")
    print("=" * 62)

    b104 = EROSBlock104CommandCenter()

    read_model = {
        "status": "CERTIFIED",
        "block_id": "103",
        "engine_version": "EROS-3.0-BLOCK-103",

        "pipeline": [
            {"block_id": str(i), "status": "CERTIFIED"}
            for i in range(94, 102)
        ],

        "risk": {
            "stress_status": "CERTIFIED",
            "evidence_status": "CERTIFIED",
            "decision_status": "ADMITTED",
            "readiness_status": "READY",
            "scenario_count": 5,
            "downside_pnl": -1500000.0,
            "upside_pnl": 1000000.0,
        },

        "governance": {
            "status": "APPROVED",
            "governance_id": "EROS98-B104-TEST",
            "execution_action": "EXECUTE",
        },

        "intent": {
            "status": "AUTHORIZED",
            "intent_id": "EROS99-B104-TEST",
            "intent_action": "PREPARE",
            "authorization_status": "AUTHORIZED",
            "symbol": "RELIANCE.NS",
            "action": "BUY",
            "quantity": 100.0,
            "reference_price": 2500.0,
        },

        "execution": {
            "status": "SIMULATED",
            "execution_id": "EROS100-B104-TEST",
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
        },

        "reconciliation": {
            "status": "RECONCILED",
            "reconciliation_id": "EROS101-B104-TEST",
            "source_execution_id": "EROS100-B104-TEST",
            "quantity_reconciled": True,
            "price_reconciled": True,
            "value_reconciled": True,
            "cost_reconciled": True,
            "lineage_reconciled": True,
        },

        "lineage": {
            "block94": "EROS94-B104-TEST",
            "block95": "EROS95-B104-TEST",
            "block96": "EROS96-B104-TEST",
            "block97": "EROS97-B104-TEST",
            "block98": "EROS98-B104-TEST",
            "block99": "EROS99-B104-TEST",
            "block100": "EROS100-B104-TEST",
            "block101": "EROS101-B104-TEST",
        },

        "safety": {
            "portfolio_mutation": False,
            "valuation_mutation": False,
            "performance_mutation": False,
            "risk_mutation": False,
            "optimization": False,
            "order_creation": False,
            "broker_submission": False,
            "live_order_submission": False,
            "execution_blocked": True,
            "non_mutation_invariant": True,
        },
    }

    model = b104.render_model(
        read_model=read_model
    )

    check(
        model["status"] == "CERTIFIED",
        "Block 104 must certify",
    )

    check(
        model["block_id"] == "104",
        "Block ID must be 104",
    )

    check(
        model["source_block"] == "103",
        "Source block must be 103",
    )

    check(
        model["header"]["pipeline"] == "94 -> 103",
        "Header pipeline must be 94 -> 103",
    )

    check(
        model["status_cards"]["governance"] == "APPROVED",
        "Governance card must be APPROVED",
    )

    check(
        model["status_cards"]["intent"] == "AUTHORIZED",
        "Intent card must be AUTHORIZED",
    )

    check(
        model["status_cards"]["execution"] == "SIMULATED",
        "Execution card must be SIMULATED",
    )

    check(
        model["status_cards"]["reconciliation"]
        == "RECONCILED",
        "Reconciliation card must be RECONCILED",
    )

    check(
        len(model["pipeline"]) == 8,
        "Pipeline must contain Blocks 94 through 101",
    )

    check(
        model["execution"]["symbol"] == "RELIANCE.NS",
        "Execution symbol must survive",
    )

    check(
        model["execution"]["filled_quantity"] == 100.0,
        "Filled quantity must survive",
    )

    check(
        model["execution"]["fill_status"] == "FILLED",
        "Fill status must survive",
    )

    check(
        model["reconciliation"]["quantity_reconciled"]
        is True,
        "Quantity reconciliation must survive",
    )

    check(
        model["reconciliation"]["price_reconciled"]
        is True,
        "Price reconciliation must survive",
    )

    check(
        model["reconciliation"]["value_reconciled"]
        is True,
        "Value reconciliation must survive",
    )

    check(
        model["reconciliation"]["cost_reconciled"]
        is True,
        "Cost reconciliation must survive",
    )

    check(
        model["reconciliation"]["lineage_reconciled"]
        is True,
        "Lineage reconciliation must survive",
    )

    check(
        model["safety"]["portfolio_mutation"]
        is False,
        "Portfolio mutation must remain false",
    )

    check(
        model["safety"]["valuation_mutation"]
        is False,
        "Valuation mutation must remain false",
    )

    check(
        model["safety"]["performance_mutation"]
        is False,
        "Performance mutation must remain false",
    )

    check(
        model["safety"]["risk_mutation"]
        is False,
        "Risk mutation must remain false",
    )

    check(
        model["safety"]["optimization"]
        is False,
        "Optimization must remain false",
    )

    check(
        model["safety"]["order_creation"]
        is False,
        "Order creation must remain false",
    )

    check(
        model["safety"]["broker_submission"]
        is False,
        "Broker submission must remain false",
    )

    check(
        model["safety"]["live_order_submission"]
        is False,
        "Live execution must remain false",
    )

    check(
        model["safety"]["execution_blocked"]
        is True,
        "Execution blocked must remain true",
    )

    check(
        model["safety"]["non_mutation_invariant"]
        is True,
        "Non-mutation invariant must remain true",
    )

    ui = model["ui_policy"]

    check(
        ui["read_only"] is True,
        "Command center must be read-only",
    )

    check(
        ui["allow_order_creation"] is False,
        "Order creation must be disabled",
    )

    check(
        ui["allow_broker_submission"] is False,
        "Broker submission must be disabled",
    )

    check(
        ui["allow_live_execution"] is False,
        "Live execution must be disabled",
    )

    check(
        ui["allow_portfolio_mutation"] is False,
        "Portfolio mutation must be disabled",
    )

    check(
        ui["allow_valuation_mutation"] is False,
        "Valuation mutation must be disabled",
    )

    check(
        ui["allow_performance_mutation"] is False,
        "Performance mutation must be disabled",
    )

    check(
        ui["allow_risk_mutation"] is False,
        "Risk mutation must be disabled",
    )

    check(
        ui["allow_optimization"] is False,
        "Optimization must be disabled",
    )

    print("")
    print("STATUS              : PASS")
    print("BLOCK               : 104")
    print("SOURCE              : BLOCK 103")
    print("COMMAND CENTER      : CERTIFIED")
    print("GOVERNANCE          : APPROVED")
    print("INTENT              : AUTHORIZED")
    print("EXECUTION           : SIMULATED")
    print("FILL                : FILLED")
    print("RECONCILIATION      : RECONCILED")
    print("LINEAGE             : PRESERVED")
    print("UI READ ONLY        : True")
    print("ORDER CREATION      : False")
    print("BROKER              : False")
    print("LIVE EXEC           : False")
    print("PORTFOLIO MUTATION  : False")
    print("EXECUTION BLOCKED   : True")
    print("NON-MUTATION        : True")
    print("")
    print("EROS 3.0 Block 104 self-test passed")
    print("=" * 62)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
