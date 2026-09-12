import json
import sys
import traceback

from services.eros_frontend_adapter import EROSFrontendAdapter

print("=" * 60)
print("EROS 3.0 - V3.7.2 TRACEABILITY FAILURE DIAGNOSTIC")
print("=" * 60)


print("\n1. PYTHON")
print("-" * 60)
print(sys.version)


print("\n2. ADAPTER IMPORT")
print("-" * 60)

try:
    adapter = EROSFrontendAdapter()

    print("IMPORT : PASS")
    print("CLASS  :", adapter.__class__.__name__)

except Exception as exc:

    print("IMPORT : FAIL")
    print("ERROR TYPE :", type(exc).__name__)
    print("ERROR      :", str(exc))
    traceback.print_exc()

    raise


print("\n3. API DISCOVERY")
print("-" * 60)

required = [
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

    exists = hasattr(adapter, name)

    print(f"{name:35} : " f"{'PASS' if exists else 'FAIL'}")

    if not exists:
        raise RuntimeError(f"MISSING_API:{name}")


print("\n4. TRACEABILITY METHOD OBJECT")
print("-" * 60)

method = adapter.decision_traceability

print("METHOD :", method)
print("TYPE   :", type(method).__name__)


print("\n5. EXECUTION TARGET")
print("-" * 60)

symbol = "RELIANCE.NS"

print("SYMBOL :", symbol)


print("\n6. EXECUTING TRACEABILITY")
print("-" * 60)

result = None

try:

    result = adapter.decision_traceability(symbol)

    print("TRACEABILITY CALL : PASS")
    print("RESULT TYPE       :", type(result).__name__)

except Exception as exc:

    print("")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("TRACEABILITY CALL : FAIL")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    print("")
    print("EXCEPTION TYPE")
    print("-" * 60)
    print(type(exc).__name__)

    print("")
    print("EXCEPTION MESSAGE")
    print("-" * 60)
    print(str(exc))

    print("")
    print("FULL TRACEBACK")
    print("-" * 60)

    traceback.print_exc()

    print("")
    print("TRACEBACK OBJECT")
    print("-" * 60)

    tb = traceback.format_exc()

    print(tb)

    print("")
    print("TRACEBACK ANALYSIS")
    print("-" * 60)

    lines = tb.splitlines()

    for index, line in enumerate(lines):

        if (
            "eros_frontend_adapter.py" in line
            or "decision_traceability" in line
            or "Traceback" in line
            or "Error" in line
            or "Exception" in line
        ):

            print(f"{index + 1:04d}: {line}")

    print("")
    print("TRACEABILITY EXECUTION FAILED")
    print("NO SOURCE PATCH WILL BE APPLIED")

    raise


print("\n7. RESULT TYPE CHECK")
print("-" * 60)

if not isinstance(result, dict):

    raise RuntimeError("TRACEABILITY_RESULT_NOT_DICT")

print("RESULT DICT : PASS")


print("\n8. TOP LEVEL KEYS")
print("-" * 60)

for key in result.keys():

    print(f"{key:35} : " f"{type(result[key]).__name__}")


print("\n9. CRITICAL SCHEMA CHECK")
print("-" * 60)

for key in [
    "symbol",
    "price",
    "decision",
    "trace",
    "traceability",
    "evidence_chain",
    "scenario_trace",
    "interpretation",
    "conclusion",
    "traceability_status",
    "governance",
]:

    exists = key in result

    print(f"{key:35} : " f"{'PRESENT' if exists else 'ABSENT'}")


print("\n10. LEGACY TRACE")
print("-" * 60)

legacy = result.get("trace")

print("PRESENT :", "YES" if legacy is not None else "NO")

print("TYPE    :", type(legacy).__name__)


print("\n11. NEW TRACEABILITY")
print("-" * 60)

new_trace = result.get("traceability")

print("PRESENT :", "YES" if "traceability" in result else "NO")

print("VALUE   :", repr(new_trace))

print("TYPE    :", type(new_trace).__name__)


print("\n12. GOVERNANCE")
print("-" * 60)

governance = result.get("governance")

if isinstance(governance, dict):

    print(json.dumps(governance, indent=2, default=str))

else:

    print("GOVERNANCE TYPE :", type(governance).__name__)


print("\n13. FINAL DIAGNOSTIC")
print("-" * 60)

print("ADAPTER IMPORT       : PASS")
print("API DISCOVERY        : PASS")
print("TRACEABILITY EXECUTE : PASS")
print("RESULT TYPE          : PASS")

print("")
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
