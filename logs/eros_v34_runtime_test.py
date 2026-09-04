import json
import sys
import traceback

print("=" * 60)
print("EROS 3.0 - V3.4 DECISION SCENARIO ENGINE - RUNTIME")
print("=" * 60)

try:
    from services.eros_frontend_adapter import EROSFrontendAdapter

    print("")
    print("1. ADAPTER IMPORT")
    print("-" * 60)
    print("IMPORT : PASS")
    print("CLASS  : EROSFrontendAdapter")

    adapter = EROSFrontendAdapter()

    print("")
    print("2. V3.4 API")
    print("-" * 60)

    if not hasattr(adapter, "decision_scenario_engine"):
        raise RuntimeError("decision_scenario_engine missing")

    print("decision_scenario_engine : PASS")

    print("")
    print("3. V3.4 SCENARIO ENGINE")
    print("-" * 60)

    result = adapter.decision_scenario_engine("RELIANCE.NS")

    if not isinstance(result, dict):
        raise RuntimeError("Scenario result is not a dict")

    print("SCENARIO ENGINE : PASS")
    print(json.dumps(result, indent=2, default=str))

    print("")
    print("4. REQUIRED STRUCTURE")
    print("-" * 60)

    required = [
        "symbol",
        "price",
        "current_decision",
        "primary_scenario",
        "scenarios",
        "decision_quality",
        "scenario_summary",
        "governance"
    ]

    for field in required:
        if field in result:
            print(f"{field:28} : PASS")
        else:
            raise RuntimeError(f"Missing field: {field}")

    print("")
    print("5. SCENARIOS")
    print("-" * 60)

    scenarios = result["scenarios"]

    for name in ["base", "bull", "bear"]:
        if name not in scenarios:
            raise RuntimeError(f"Missing scenario: {name}")

        print(f"{name.upper():28} : PASS")

    print("")
    print("6. SAFETY CONTRACT")
    print("-" * 60)

    governance = result["governance"]

    expected = {
        "read_only": True,
        "execution_blocked": True,
        "non_mutation_invariant": True,
        "allow_order_creation": False,
        "allow_broker_submission": False,
        "allow_live_execution": False,
        "allow_portfolio_mutation": False,
        "allow_valuation_mutation": False,
        "allow_performance_mutation": False,
        "allow_risk_mutation": False,
        "allow_optimization": False
    }

    for key, expected_value in expected.items():

        actual = governance.get(key)

        if actual != expected_value:
            raise RuntimeError(
                f"Safety failure: {key}: "
                f"actual={actual}, expected={expected_value}"
            )

        print(f"{key:32} : PASS")

    print("")
    print("=" * 60)
    print("EROS 3.0 - V3.4 DECISION SCENARIO ENGINE")
    print("=" * 60)
    print("")
    print("SCENARIO ENGINE       : PASS")
    print("BASE SCENARIO         : PASS")
    print("BULL SCENARIO         : PASS")
    print("BEAR SCENARIO         : PASS")
    print("SAFETY CONTRACT       : PASS")
    print("READ_ONLY             : TRUE")
    print("EXECUTION_BLOCKED     : TRUE")
    print("NON_MUTATION_INVARIANT: TRUE")
    print("")
    print("FINAL RESULT : PASS")
    print("V3.4 DECISION SCENARIO ENGINE : CLEARED")
    print("=" * 60)

except Exception as exc:
    print("")
    print("=" * 60)
    print("V3.4 RUNTIME : FAIL")
    print("=" * 60)
    print("")
    print(f"{type(exc).__name__}: {exc}")
    print("")
    traceback.print_exc()
    sys.exit(1)