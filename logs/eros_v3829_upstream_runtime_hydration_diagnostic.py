from __future__ import annotations

import os
import sys
import traceback

PROJECT_ROOT = r"D:\Users\User\Desktop\AI_STOCK_ANALYZER"

print("=" * 70)
print("EROS 3.0 - V3.8.2.9 UPSTREAM RUNTIME HYDRATION DIAGNOSTIC")
print("=" * 70)

print("\n1. ENVIRONMENT")
print("-" * 70)
print("Python:", sys.version)
print("CWD   :", os.getcwd())

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print("ROOT  :", PROJECT_ROOT)
print("PATH  :", PROJECT_ROOT in sys.path)

print("\n2. ADAPTER IMPORT")
print("-" * 70)

try:
    from services.eros_frontend_adapter import EROSFrontendAdapter
    print("IMPORT : PASS")
except Exception:
    print("IMPORT : FAIL")
    traceback.print_exc()
    raise SystemExit(1)

adapter = EROSFrontendAdapter()
symbol = "RELIANCE.NS"

print("\nSYMBOL :", symbol)

def inspect_result(name, result):

    print("\n" + "=" * 70)
    print("RESULT :", name)
    print("=" * 70)

    print("TYPE :", type(result).__name__)

    if not isinstance(result, dict):
        print("VALUE :", repr(result)[:5000])
        return

    print("KEY COUNT :", len(result))
    print("KEYS :", list(result.keys()))

    important = [
        "symbol",
        "price",
        "decision",
        "recommendation",
        "stance",
        "classification",
        "confidence",
        "risk",
        "evidence",
        "evidence_chain",
        "interpretation",
        "scenario_trace",
        "convergence",
        "trace",
        "traceability",
        "conclusion",
        "governance",
    ]

    print("\nIMPORTANT FIELDS")
    print("-" * 50)

    for key in important:

        if key not in result:
            print(f"{key:25} : ABSENT")
            continue

        value = result[key]

        if value is None:
            print(f"{key:25} : NONE")

        elif isinstance(value, dict):
            print(
                f"{key:25} : DICT "
                f"({len(value)} keys)"
            )
            print(
                f"{'':25}   keys="
                f"{list(value.keys())[:30]}"
            )

        elif isinstance(value, list):
            print(
                f"{key:25} : LIST "
                f"({len(value)} items)"
            )

        elif isinstance(value, str) and not value.strip():
            print(f"{key:25} : EMPTY STRING")

        else:
            print(
                f"{key:25} : "
                f"{type(value).__name__} = {value!r}"
            )

    print("\nFULL RESULT")
    print("-" * 50)
    print(result)


results = {}

methods = [
    "decision_evidence",
    "decision_intelligence",
    "decision_interpretation",
    "decision_action_framework",
    "decision_scenario_engine",
    "decision_convergence",
    "decision_traceability",
]

print("\n3. UPSTREAM-TO-DOWNSTREAM RUNTIME CHAIN")
print("-" * 70)

for name in methods:

    print("\nCALLING :", name)

    try:
        fn = getattr(adapter, name)
        result = fn(symbol)
        results[name] = result

        print("CALL : PASS")
        inspect_result(name, result)

    except Exception:
        print("CALL : FAIL")
        traceback.print_exc()
        results[name] = None


print("\n" + "=" * 70)
print("4. CROSS-LAYER HYDRATION MATRIX")
print("=" * 70)

fields = [
    "price",
    "decision",
    "recommendation",
    "stance",
    "classification",
    "confidence",
    "risk",
    "evidence",
    "evidence_chain",
    "interpretation",
    "scenario_trace",
    "convergence",
    "trace",
    "traceability",
    "conclusion",
]

for method, result in results.items():

    print("\n" + method)

    if not isinstance(result, dict):
        print("  RESULT : NOT DICT")
        continue

    for field in fields:

        if field not in result:
            status = "ABSENT"

        else:
            value = result[field]

            if value is None:
                status = "NONE"

            elif isinstance(value, dict):
                status = f"DICT({len(value)} keys)"

            elif isinstance(value, list):
                status = f"LIST({len(value)} items)"

            elif isinstance(value, str) and not value.strip():
                status = "EMPTY"

            else:
                status = type(value).__name__

        print(f"  {field:22} : {status}")


print("\n" + "=" * 70)
print("5. DECISION PROPAGATION CHECK")
print("=" * 70)

for method in [
    "decision_evidence",
    "decision_intelligence",
    "decision_interpretation",
    "decision_action_framework",
    "decision_scenario_engine",
    "decision_convergence",
    "decision_traceability",
]:

    result = results.get(method)

    print("\n" + method)

    if not isinstance(result, dict):
        print("  NO DICT RESULT")
        continue

    decision = result.get("decision")

    print("  decision :", repr(decision)[:3000])

    if isinstance(decision, dict):
        print("  decision keys :", list(decision.keys()))

        for k in [
            "stance",
            "recommendation",
            "classification",
            "confidence",
            "risk",
        ]:
            print(
                f"  decision.{k:18} : "
                f"{repr(decision.get(k))}"
            )


print("\n" + "=" * 70)
print("6. SAFETY")
print("=" * 70)

print("SOURCE PATCH : NO")
print("DATABASE WRITE : NO")
print("BROKER CALL : NO")
print("ORDER CREATION : NO")
print("PORTFOLIO MUTATION : NO")
print("GIT OPERATION : NO")

print("\n" + "=" * 70)
print("V3.8.2.9 DIAGNOSTIC COMPLETE")
print("=" * 70)
