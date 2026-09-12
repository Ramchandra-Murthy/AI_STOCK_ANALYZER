from __future__ import annotations

import os
import sys
import traceback

PROJECT_ROOT = r"D:\Users\User\Desktop\AI_STOCK_ANALYZER"

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print("=" * 70)
print("EROS 3.0 - V3.8.2.7 RUNTIME DECISION DATAFLOW DIAGNOSTIC")
print("=" * 70)

print("\n1. ENVIRONMENT")
print("-" * 70)
print("Python:", sys.version)
print("CWD   :", os.getcwd())
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

print("\n3. RUNTIME DATAFLOW")
print("-" * 70)
print("SYMBOL :", symbol)

apis = [
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
    "decision_audit",
]

results = {}


def describe(name, result):

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    print("TYPE :", type(result).__name__)

    if not isinstance(result, dict):
        print("NOT A DICT")
        print("VALUE:", repr(result)[:3000])
        return

    results[name] = result

    print("KEY COUNT :", len(result))
    print("KEYS      :", list(result.keys()))

    critical = [
        "symbol",
        "price",
        "trend",
        "momentum",
        "score",
        "confidence",
        "recommendation",
        "risk",
        "stance",
        "classification",
        "decision_quality",
        "decision",
        "evidence",
        "evidence_chain",
        "scenario_trace",
        "interpretation",
        "convergence",
        "trace",
        "traceability",
        "conclusion",
        "audit",
        "audit_findings",
        "audit_status",
    ]

    print("\nCRITICAL FIELDS")
    print("-" * 50)

    for key in critical:

        if key not in result:
            continue

        value = result[key]

        if isinstance(value, dict):
            print(f"{key:24} : DICT " f"keys={len(value)} " f"{list(value.keys())[:15]}")

        elif isinstance(value, list):
            print(f"{key:24} : LIST " f"items={len(value)}")

        else:
            print(f"{key:24} : " f"{type(value).__name__} = {value!r}")


for api in apis:

    print("\nCALLING:", api)

    try:
        fn = getattr(adapter, api)
        result = fn(symbol)

        print("CALL : PASS")

        describe(api, result)

    except Exception:
        print("CALL : FAIL")
        traceback.print_exc()


print("\n")
print("=" * 70)
print("4. FIRST-EMPTY-STAGE ANALYSIS")
print("=" * 70)

decision_keys = [
    "decision",
    "evidence",
    "evidence_chain",
    "interpretation",
    "scenario_trace",
    "convergence",
    "trace",
    "traceability",
]

for api in apis:

    result = results.get(api)

    if not isinstance(result, dict):
        print(f"{api:35} : NO DICT")
        continue

    print(f"\n{api}")

    for key in decision_keys:

        if key not in result:
            continue

        value = result[key]

        if isinstance(value, dict):
            state = "EMPTY DICT" if not value else "HYDRATED"

        elif isinstance(value, list):
            state = "EMPTY LIST" if not value else "HYDRATED"

        elif value is None:
            state = "NONE"

        elif value == "":
            state = "EMPTY STRING"

        else:
            state = "VALUE"

        print(f"  {key:25} : {state}")


print("\n")
print("=" * 70)
print("5. DECISION EVIDENCE PAYLOAD")
print("=" * 70)

evidence = results.get("decision_evidence")

if isinstance(evidence, dict):

    for key in [
        "symbol",
        "price",
        "trend",
        "momentum",
        "score",
        "confidence",
        "recommendation",
        "risk",
        "reasons",
        "breakout_signal",
        "breakout_reason",
    ]:

        print(f"{key:25} : " f"{evidence.get(key)!r}")

else:
    print("decision_evidence RESULT UNAVAILABLE")


print("\n")
print("=" * 70)
print("6. DECISION INTELLIGENCE PAYLOAD")
print("=" * 70)

intelligence = results.get("decision_intelligence")

if isinstance(intelligence, dict):

    print(intelligence)

else:
    print("decision_intelligence RESULT UNAVAILABLE")


print("\n")
print("=" * 70)
print("7. DOWNSTREAM HYDRATION SUMMARY")
print("=" * 70)

for api in [
    "decision_interpretation",
    "decision_action_framework",
    "decision_action_explanation",
    "decision_scenario_engine",
    "decision_scenario_explanation",
    "decision_convergence",
    "decision_traceability",
    "decision_audit",
]:

    result = results.get(api)

    if not isinstance(result, dict):
        print(f"{api:35} : UNAVAILABLE")
        continue

    states = []

    for key in [
        "decision",
        "evidence_chain",
        "scenario_trace",
        "interpretation",
        "convergence",
        "traceability",
    ]:

        if key in result:

            value = result[key]

            if isinstance(value, dict):
                states.append(f"{key}={'EMPTY' if not value else 'DATA'}")

            elif isinstance(value, list):
                states.append(f"{key}={'EMPTY' if not value else 'DATA'}")

            elif value is None:
                states.append(f"{key}=NONE")

            else:
                states.append(f"{key}=VALUE")

    print(f"{api:35} : " + ", ".join(states))


print("\n")
print("=" * 70)
print("8. SAFETY VERIFICATION")
print("=" * 70)

audit = results.get("decision_audit")

if isinstance(audit, dict):

    governance = audit.get("governance", {})

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

        print(f"{key:35} : " f"{governance.get(key)!r}")

else:
    print("AUDIT RESULT UNAVAILABLE")


print("\n")
print("=" * 70)
print("9. CONCLUSION")
print("=" * 70)

print("""
NO SOURCE PATCH PERFORMED.
NO DATABASE WRITE.
NO BROKER CALL.
NO ORDER CREATION.
NO PORTFOLIO MUTATION.
NO GIT OPERATION.

This diagnostic identifies the FIRST runtime stage where
decision data becomes empty or changes shape.

V3.8.2.4 GOLDEN CHECKPOINT REMAINS UNMODIFIED.
""")

print("=" * 70)
print("V3.8.2.7 DIAGNOSTIC COMPLETE")
print("=" * 70)
