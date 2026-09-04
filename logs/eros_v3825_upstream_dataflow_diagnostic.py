from __future__ import annotations

import os
import sys
import traceback
import json

PROJECT_ROOT = r"D:\Users\User\Desktop\AI_STOCK_ANALYZER"
SYMBOL = "RELIANCE.NS"

print("=" * 78)
print("EROS 3.0 - V3.8.2.5 UPSTREAM DECISION DATAFLOW DIAGNOSTIC")
print("=" * 78)

print("\n1. ENVIRONMENT")
print("-" * 78)
print("Python :", sys.version)
print("CWD    :", os.getcwd())

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print("ROOT   :", PROJECT_ROOT)
print("PATH   :", PROJECT_ROOT in sys.path)

print("\n2. ADAPTER IMPORT")
print("-" * 78)

try:
    from services.eros_frontend_adapter import EROSFrontendAdapter
    print("IMPORT : PASS")
    print("CLASS  :", EROSFrontendAdapter.__name__)
except Exception:
    print("IMPORT : FAIL")
    traceback.print_exc()
    raise SystemExit(1)

adapter = EROSFrontendAdapter()

print("\n3. EXECUTION TARGET")
print("-" * 78)
print("SYMBOL :", SYMBOL)

API_NAMES = [
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

results = {}

def describe_value(label, value, indent="  "):
    if value is None:
        print(f"{indent}{label:28} : NONE")
        return

    if isinstance(value, dict):
        print(f"{indent}{label:28} : DICT ({len(value)} keys)")
        if value:
            print(
                f"{indent}{'':28}   KEYS: "
                f"{list(value.keys())[:30]}"
            )
        else:
            print(f"{indent}{'':28}   *** EMPTY DICT ***")
        return

    if isinstance(value, list):
        print(f"{indent}{label:28} : LIST ({len(value)} items)")
        if len(value) == 0:
            print(f"{indent}{'':28}   *** EMPTY LIST ***")
        return

    if isinstance(value, str):
        if value == "":
            print(f"{indent}{label:28} : EMPTY STRING")
        else:
            print(
                f"{indent}{label:28} : STRING "
                f"{value[:300]!r}"
            )
        return

    print(
        f"{indent}{label:28} : "
        f"{type(value).__name__} = {repr(value)[:500]}"
    )


def run_api(name):
    print("\n" + "=" * 78)
    print(f"API: {name}")
    print("=" * 78)

    try:
        fn = getattr(adapter, name)
    except Exception as exc:
        print("FUNCTION : NOT FOUND")
        print("ERROR    :", repr(exc))
        return None

    try:
        result = fn(SYMBOL)
    except Exception:
        print("CALL     : FAIL")
        traceback.print_exc()
        return None

    print("CALL     : PASS")
    print("TYPE     :", type(result).__name__)

    if not isinstance(result, dict):
        print("VALUE    :", repr(result)[:3000])
        return result

    print("KEY COUNT:", len(result))
    print("KEYS     :", list(result.keys()))

    important_keys = [
        "symbol",
        "price",
        "decision",
        "evidence",
        "evidence_chain",
        "intelligence",
        "interpretation",
        "action",
        "action_framework",
        "action_explanation",
        "scenario",
        "scenario_trace",
        "convergence",
        "trace",
        "traceability",
        "conclusion",
        "confidence",
        "risk",
        "recommendation",
        "classification",
        "stance",
        "decision_quality",
    ]

    for key in important_keys:
        if key in result:
            describe_value(key, result[key])

    return result


print("\n4. RUNNING UPSTREAM APIs")
print("-" * 78)

for api_name in API_NAMES:
    results[api_name] = run_api(api_name)


print("\n")
print("=" * 78)
print("5. FIRST-FAILURE ANALYSIS")
print("=" * 78)

tracked = [
    ("decision_evidence", "decision"),
    ("decision_evidence", "evidence_chain"),
    ("decision_intelligence", "decision"),
    ("decision_interpretation", "interpretation"),
    ("decision_scenario_engine", "scenario_trace"),
    ("decision_convergence", "decision"),
    ("decision_convergence", "trace"),
    ("decision_traceability", "traceability"),
]

first_failure = None

for api_name, key in tracked:

    result = results.get(api_name)

    if not isinstance(result, dict):
        print(
            f"{api_name:30} -> "
            f"{key:22} : API RESULT NOT DICT"
        )

        if first_failure is None:
            first_failure = (
                api_name,
                key,
                "API RESULT NOT DICT"
            )
        continue

    if key not in result:
        print(
            f"{api_name:30} -> "
            f"{key:22} : ABSENT"
        )

        if first_failure is None:
            first_failure = (
                api_name,
                key,
                "KEY ABSENT"
            )
        continue

    value = result[key]

    empty = (
        value is None
        or value == ""
        or value == {}
        or value == []
    )

    if empty:
        print(
            f"{api_name:30} -> "
            f"{key:22} : *** EMPTY ***"
        )

        if first_failure is None:
            first_failure = (
                api_name,
                key,
                "EMPTY"
            )
    else:
        print(
            f"{api_name:30} -> "
            f"{key:22} : HYDRATED"
        )


print("\n")
print("=" * 78)
print("6. DATAFLOW SUMMARY")
print("=" * 78)

for api_name in API_NAMES:

    result = results.get(api_name)

    print("\n" + api_name)
    print("-" * 60)

    if not isinstance(result, dict):
        print("RESULT : INVALID / NONE")
        continue

    for key in [
        "decision",
        "evidence_chain",
        "interpretation",
        "scenario_trace",
        "convergence",
        "trace",
        "traceability",
        "conclusion",
    ]:

        if key not in result:
            continue

        value = result[key]

        if isinstance(value, dict):
            status = (
                "EMPTY"
                if len(value) == 0
                else f"HYDRATED ({len(value)} keys)"
            )

        elif isinstance(value, list):
            status = (
                "EMPTY"
                if len(value) == 0
                else f"HYDRATED ({len(value)} items)"
            )

        elif value is None or value == "":
            status = "EMPTY"

        else:
            status = f"HYDRATED ({type(value).__name__})"

        print(f"{key:25} : {status}")


print("\n")
print("=" * 78)
print("7. FIRST FAILURE")
print("=" * 78)

if first_failure is None:
    print("FIRST FAILURE : NONE DETECTED")
    print("ALL TRACKED DATAFLOW ELEMENTS ARE HYDRATED")
else:
    api_name, key, reason = first_failure

    print("FIRST FAILURE API   :", api_name)
    print("FIRST FAILURE FIELD :", key)
    print("REASON              :", reason)

    print("\nTHIS IS THE LAYER TO INVESTIGATE.")
    print("NO PATCH SHOULD BE APPLIED BY THIS DIAGNOSTIC.")


print("\n")
print("=" * 78)
print("8. DECISION AUDIT OBSERVATION")
print("=" * 78)

try:
    audit = adapter.decision_audit(SYMBOL)

    print("AUDIT CALL :", "PASS")
    print("AUDIT TYPE :", type(audit).__name__)

    if isinstance(audit, dict):

        for key in [
            "decision",
            "audit",
            "audit_findings",
            "trace",
            "traceability",
            "evidence_chain",
            "scenario_trace",
            "interpretation",
            "conclusion",
            "audit_status",
            "governance",
        ]:
            if key in audit:
                describe_value(key, audit[key])

except Exception:
    print("AUDIT CALL : FAIL")
    traceback.print_exc()


print("\n")
print("=" * 78)
print("9. SAFETY OBSERVATION")
print("=" * 78)

try:
    audit = adapter.decision_audit(SYMBOL)

    governance = (
        audit.get("governance", {})
        if isinstance(audit, dict)
        else {}
    )

    for key in [
        "read_only",
        "execution_blocked",
        "non_mutation_invariant",
        "allow_order_creation",
        "allow_broker_submission",
        "allow_live_execution",
        "allow_portfolio_mutation",
        "allow_valuation_mutation",
        "allow_performance_mutation",
        "allow_risk_mutation",
        "allow_optimization",
    ]:
        print(
            f"{key:35} : "
            f"{governance.get(key, 'NOT PRESENT')}"
        )

except Exception:
    print("SAFETY OBSERVATION FAILED")
    traceback.print_exc()


print("\n")
print("=" * 78)
print("10. V3.8.2.5 CONCLUSION")
print("=" * 78)

print(
    """
READ-ONLY DIAGNOSTIC
NO SOURCE PATCH
NO DATABASE WRITE
NO BROKER CALL
NO ORDER CREATION
NO PORTFOLIO MUTATION
NO GIT OPERATION

The purpose of this diagnostic is to identify the FIRST upstream
decision-data layer that returns empty or incomplete data.

Do not patch until the first failure is identified.
"""
)

print("=" * 78)
print("V3.8.2.5 DIAGNOSTIC COMPLETE")
print("=" * 78)
