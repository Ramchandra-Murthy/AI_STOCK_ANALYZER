import json
import sys
import traceback

print("=" * 60)
print("EROS 3.0 - V3.3 DECISION ACTION EXPLANATION ENGINE - RUNTIME")
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
    print("2. EXISTING API CHECK")
    print("-" * 60)

    required = [
        "snapshot",
        "governance",
        "dashboard_snapshot",
        "market_scan",
        "stock_analysis",
        "decision_evidence",
        "decision_intelligence",
        "decision_interpretation",
        "decision_action_framework",
    ]

    for name in required:
        status = hasattr(adapter, name)
        print(f"{name:32} : {'PASS' if status else 'FAIL'}")

        if not status:
            raise RuntimeError(f"Missing API: {name}")

    print("")
    print("3. V3.3 EXPLANATION API DISCOVERY")
    print("-" * 60)

    candidates = [
        name for name in dir(adapter)
        if "explanation" in name.lower()
        or "action_explanation" in name.lower()
    ]

    if not candidates:
        print("EXPLANATION API : NOT FOUND")
        raise RuntimeError("V3.3 explanation API not found")

    print("EXPLANATION API : PASS")

    for name in candidates:
        print(f" - {name}")

    print("")
    print("4. DECISION ACTION FRAMEWORK")
    print("-" * 60)

    action = adapter.decision_action_framework("RELIANCE.NS")

    if not isinstance(action, dict):
        raise RuntimeError("decision_action_framework did not return dict")

    print("ACTION FRAMEWORK : PASS")
    print(json.dumps(action, indent=2, default=str))

    print("")
    print("5. EXECUTING V3.3 EXPLANATION API")
    print("-" * 60)

    explanation_method = candidates[0]

    method = getattr(adapter, explanation_method)

    try:
        explanation = method("RELIANCE.NS")
    except TypeError:
        try:
            explanation = method(action)
        except TypeError:
            explanation = method()

    if not isinstance(explanation, dict):
        raise RuntimeError("V3.3 explanation result is not a dict")

    print("EXPLANATION : PASS")
    print(json.dumps(explanation, indent=2, default=str))

    print("")
    print("6. EXPLANATION FIELD DISCOVERY")
    print("-" * 60)

    for key in explanation.keys():
        print(f" - {key}")

    print("")
    print("7. SAFETY CHECK")
    print("-" * 60)

    governance = explanation.get("governance", {})

    if not governance:
        governance = action.get("governance", {})

    safety_fields = {
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
        "allow_optimization": False,
    }

    for key, expected in safety_fields.items():
        actual = governance.get(key)

        if actual == expected:
            print(f"{key:32} : PASS")
        else:
            print(
                f"{key:32} : FAIL "
                f"(actual={actual!r}, expected={expected!r})"
            )
            raise RuntimeError(f"Safety failure: {key}")

    print("")
    print("=" * 60)
    print("EROS 3.0 - V3.3 DECISION ACTION EXPLANATION ENGINE")
    print("=" * 60)
    print("")
    print("EXPLANATION API        : PASS")
    print("ACTION FRAMEWORK      : PASS")
    print("SAFETY CONTRACT       : PASS")
    print("READ_ONLY             : TRUE")
    print("EXECUTION_BLOCKED     : TRUE")
    print("NON_MUTATION_INVARIANT: TRUE")
    print("")
    print("FINAL RESULT : PASS")
    print("V3.3 DECISION ACTION EXPLANATION : CLEARED")
    print("=" * 60)

except Exception as exc:
    print("")
    print("=" * 60)
    print("V3.3 RUNTIME VERIFICATION : FAIL")
    print("=" * 60)
    print("")
    print(f"{type(exc).__name__}: {exc}")
    print("")
    traceback.print_exc()
    sys.exit(1)