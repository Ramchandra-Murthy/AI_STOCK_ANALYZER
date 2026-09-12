import importlib
from pprint import pprint

print("=" * 80)
print("EROS 3.0 - BLOCK 94 -> 101 REAL SAFETY DATA-FLOW TRACE")
print("=" * 80)


def show_result(label, result):
    print()
    print("=" * 80)
    print(label)
    print("=" * 80)

    print("TYPE   :", type(result))

    if isinstance(result, dict):
        print("STATUS :", result.get("status", "<ABSENT>"))
        print("KEYS   :", list(result.keys()))

        print()
        print("SAFETY / EXECUTION FIELDS")

        safety_keys = [
            "execution_blocked",
            "non_mutation_invariant",
            "broker_submission",
            "live_order_submission",
            "portfolio_mutation",
            "valuation_mutation",
            "performance_mutation",
            "risk_mutation",
            "optimization",
            "order_creation",
            "execution_action",
            "intent_action",
            "fill_status",
            "reconciliation_status",
        ]

        for key in safety_keys:
            if key in result:
                print(f"{key:28} : {result[key]!r}")

        if isinstance(result.get("safety"), dict):
            print()
            print("NESTED SAFETY")
            pprint(result["safety"], width=140, sort_dicts=False)

        print()
        print("FULL RESULT")
        pprint(result, width=140, sort_dicts=False)

    else:
        pprint(result, width=140, sort_dicts=False)


try:
    # ==========================================================
    # IMPORTS
    # ==========================================================

    B94 = importlib.import_module(
        "services.quantitative.block94_portfolio_stress_scenario_engine"
    ).EROSBlock94PortfolioStressScenarioEngine

    B95 = importlib.import_module(
        "services.quantitative.block95_stress_evidence_gate"
    ).EROSBlock95StressEvidenceGate

    B96 = importlib.import_module(
        "services.quantitative.block96_stress_decision_gate"
    ).EROSBlock96StressDecisionGate

    B97 = importlib.import_module(
        "services.quantitative.block97_stress_readiness_gate"
    ).EROSBlock97StressReadinessGate

    B98 = importlib.import_module(
        "services.quantitative.block98_execution_governance_bridge"
    ).EROSBlock98ExecutionGovernanceBridge

    B99 = importlib.import_module(
        "services.quantitative.block99_execution_intent_authorization_gate"
    ).EROSBlock99ExecutionIntentAuthorizationGate

    B100 = importlib.import_module(
        "services.quantitative.block100_paper_execution_fill_gate"
    ).EROSBlock100PaperExecutionFillGate

    B101 = importlib.import_module(
        "services.quantitative.block101_execution_evidence_reconciliation"
    ).EROSBlock101ExecutionEvidenceReconciliationGate

    print()
    print("IMPORTS : PASS")

    # ==========================================================
    # SYNTHETIC INPUT
    # ==========================================================

    valuation = {
        "portfolio_value": 1_000_000.0,
        "cash": 250_000.0,
        "currency": "INR",
    }

    performance = {
        "return_pct": 8.5,
        "benchmark_return_pct": 7.0,
    }

    risk = {
        "volatility": 0.18,
        "drawdown": 0.05,
        "risk_score": 32,
    }

    positions = [
        {
            "symbol": "RELIANCE",
            "quantity": 100,
            "price": 2500.0,
            "market_value": 250000.0,
        },
        {
            "symbol": "TCS",
            "quantity": 100,
            "price": 3500.0,
            "market_value": 350000.0,
        },
    ]

    scenarios = [
        {
            "scenario_id": "TEST_STRESS_001",
            "name": "Synthetic Market Stress",
            "shock_pct": -10.0,
        }
    ]

    print()
    print("SYNTHETIC INPUT : CREATED")
    print("Portfolio value :", valuation["portfolio_value"])
    print("Positions       :", len(positions))
    print("Scenarios       :", len(scenarios))

    # ==========================================================
    # BLOCK 94
    # ==========================================================

    b94 = B94()

    result94 = b94.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    show_result("BLOCK 94 RESULT", result94)

    # ==========================================================
    # BLOCK 95
    # ==========================================================

    b95 = B95()

    result95 = b95.certify(stress_certificate=result94)

    show_result("BLOCK 95 RESULT", result95)

    # ==========================================================
    # BLOCK 96
    # ==========================================================

    b96 = B96()

    result96 = b96.certify(stress_gate=result95)

    show_result("BLOCK 96 RESULT", result96)

    # ==========================================================
    # BLOCK 97
    # ==========================================================

    b97 = B97()

    result97 = b97.certify(decision=result96)

    show_result("BLOCK 97 RESULT", result97)

    # ==========================================================
    # BLOCK 98
    # ==========================================================

    b98 = B98()

    result98 = b98.certify(decision=result97)

    show_result("BLOCK 98 RESULT", result98)

    # ==========================================================
    # BLOCK 99
    # ==========================================================

    b99 = B99()

    result99 = b99.certify(governance=result98)

    show_result("BLOCK 99 RESULT", result99)

    # ==========================================================
    # BLOCK 100
    # ==========================================================

    b100 = B100()

    result100 = b100.certify(
        intent=result99,
        fill_ratio=1.0,
    )

    show_result("BLOCK 100 RESULT", result100)

    # ==========================================================
    # BLOCK 101
    # ==========================================================

    b101 = B101()

    result101 = b101.certify(execution=result100)

    show_result("BLOCK 101 RESULT", result101)

    # ==========================================================
    # FINAL SAFETY MATRIX
    # ==========================================================

    print()
    print("=" * 80)
    print("FINAL SAFETY FIELD MATRIX")
    print("=" * 80)

    chain = [
        ("94", result94),
        ("95", result95),
        ("96", result96),
        ("97", result97),
        ("98", result98),
        ("99", result99),
        ("100", result100),
        ("101", result101),
    ]

    safety_keys = [
        "execution_blocked",
        "non_mutation_invariant",
        "broker_submission",
        "live_order_submission",
        "portfolio_mutation",
        "valuation_mutation",
        "performance_mutation",
        "risk_mutation",
        "optimization",
        "order_creation",
    ]

    print()
    print(f"{'BLOCK':8}" + "".join(f"{key:26}" for key in safety_keys))

    for block_id, result in chain:
        print(
            f"{block_id:8}"
            + "".join(f"{repr(result.get(key, '<ABSENT>')):26}" for key in safety_keys)
        )

    print()
    print("=" * 80)
    print("REAL 94 -> 101 DATA-FLOW TRACE COMPLETE")
    print("=" * 80)
    print("NO SOURCE CHANGES")
    print("NO BROKER")
    print("NO LIVE EXECUTION")
    print("NO ORDER CREATION")
    print("NO MUTATION")
    print("=" * 80)

except Exception as exc:

    print()
    print("=" * 80)
    print("TRACE ERROR")
    print("=" * 80)
    print(type(exc).__name__, str(exc))
    import traceback

    traceback.print_exc()
