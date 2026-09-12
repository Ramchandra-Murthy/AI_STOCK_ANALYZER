import json
import sys
import traceback

from services.eros_frontend_adapter import EROSFrontendAdapter

print("=" * 60)
print("EROS 3.0 - V3.7 TRACEABILITY RUNTIME DIAGNOSTIC")
print("=" * 60)

print("")
print("PYTHON VERSION")
print("-" * 60)
print(sys.version)


print("")
print("1. ADAPTER IMPORT")
print("-" * 60)

try:

    adapter = EROSFrontendAdapter()

    print("IMPORT : PASS")
    print("CLASS  :", adapter.__class__.__name__)

except Exception as exc:

    print("IMPORT : FAIL")
    print("EXCEPTION TYPE :", type(exc).__name__)
    print("EXCEPTION      :", str(exc))
    print("")
    traceback.print_exc()

    raise


print("")
print("2. API CHECK")
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
    "decision_action_explanation",
    "decision_scenario_engine",
    "decision_scenario_explanation",
    "decision_convergence",
    "decision_traceability",
]

for name in required:

    present = hasattr(adapter, name)

    print(f"{name:35} : " f"{'PASS' if present else 'FAIL'}")

    if not present:
        raise RuntimeError(f"MISSING_API:{name}")


print("")
print("3. TRACEABILITY METHOD")
print("-" * 60)

method = getattr(adapter, "decision_traceability", None)

print("METHOD OBJECT :", method)
print("METHOD TYPE   :", type(method).__name__)

if method is None:
    raise RuntimeError("TRACEABILITY_METHOD_NOT_FOUND")


print("")
print("4. EXECUTING TRACEABILITY")
print("-" * 60)

symbol = "RELIANCE.NS"

print("SYMBOL :", symbol)
print("")
print("CALL:")
print('adapter.decision_traceability("RELIANCE.NS")')
print("")


try:

    result = adapter.decision_traceability(symbol)

    print("TRACEABILITY CALL : PASS")
    print("RESULT TYPE       :", type(result).__name__)

except Exception as exc:

    print("")
    print("=" * 60)
    print("TRACEABILITY CALL : FAIL")
    print("=" * 60)

    print("")
    print("EXCEPTION TYPE")
    print("-" * 60)
    print(type(exc).__name__)

    print("")
    print("EXCEPTION MESSAGE")
    print("-" * 60)
    print(str(exc))

    print("")
    print("EXCEPTION REPR")
    print("-" * 60)
    print(repr(exc))

    print("")
    print("FULL TRACEBACK")
    print("-" * 60)

    traceback.print_exc()

    print("")
    print("=" * 60)
    print("END TRACEABILITY DIAGNOSTIC")
    print("=" * 60)

    sys.exit(10)


print("")
print("5. RESULT VALIDATION")
print("-" * 60)

if not isinstance(result, dict):

    print("RESULT DICT : FAIL")

    raise RuntimeError("TRACEABILITY_RESULT_NOT_DICT")

print("RESULT DICT : PASS")


print("")
print("6. RESULT TOP LEVEL")
print("-" * 60)

print(json.dumps(result, indent=2, default=str))


print("")
print("7. TOP LEVEL FIELDS")
print("-" * 60)

for field in [
    "symbol",
    "price",
    "decision",
    "traceability",
    "conclusion",
    "governance",
]:

    present = field in result

    print(f"{field:35} : " f"{'PASS' if present else 'FAIL'}")


print("")
print("8. TRACEABILITY OBJECT")
print("-" * 60)

traceability = result.get("traceability")

print(json.dumps(traceability, indent=2, default=str))


print("")
print("9. TRACEABILITY LAYERS")
print("-" * 60)

if isinstance(traceability, dict):

    layers = [
        "decision",
        "evidence",
        "intelligence",
        "interpretation",
        "action",
        "action_explanation",
        "scenario",
        "scenario_explanation",
        "convergence",
    ]

    for layer in layers:

        present = layer in traceability

        print(f"{layer:35} : " f"{'PRESENT' if present else 'ABSENT'}")

else:

    print("TRACEABILITY IS NOT A DICT")


print("")
print("10. GOVERNANCE")
print("-" * 60)

governance = result.get("governance", {})

print(json.dumps(governance, indent=2, default=str))


print("")
print("11. DATABASE / EXECUTION SAFETY")
print("-" * 60)

expected_true = [
    "read_only",
    "execution_blocked",
    "non_mutation_invariant",
]

expected_false = [
    "allow_order_creation",
    "allow_broker_submission",
    "allow_live_execution",
    "allow_portfolio_mutation",
    "allow_valuation_mutation",
    "allow_performance_mutation",
    "allow_risk_mutation",
    "allow_optimization",
]

for field in expected_true:

    value = governance.get(field)

    print(f"{field:35} : " f"{value}")


for field in expected_false:

    value = governance.get(field)

    print(f"{field:35} : " f"{value}")


print("")
print("=" * 60)
print("V3.7 TRACEABILITY DIAGNOSTIC COMPLETE")
print("=" * 60)
