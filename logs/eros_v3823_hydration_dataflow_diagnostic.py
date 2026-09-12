from __future__ import annotations

import os
import sys
import traceback

PROJECT_ROOT = r"D:\Users\User\Desktop\AI_STOCK_ANALYZER"

print("=" * 70)
print("EROS 3.0 - V3.8.2.3 HYDRATION DATAFLOW DIAGNOSTIC")
print("=" * 70)

print("\n1. PYTHON / PATH")
print("-" * 70)
print("Python:", sys.version)
print("CWD   :", os.getcwd())

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print("ROOT  :", PROJECT_ROOT)
print("ROOT IN SYS.PATH:", PROJECT_ROOT in sys.path)

print("\n2. ADAPTER IMPORT")
print("-" * 70)

try:
    from services.eros_frontend_adapter import EROSFrontendAdapter

    print("IMPORT : PASS")
    print("CLASS  :", EROSFrontendAdapter.__name__)
except Exception:
    print("IMPORT : FAIL")
    traceback.print_exc()
    raise SystemExit(1)

adapter = EROSFrontendAdapter()
symbol = "RELIANCE.NS"

results = {}

print("\n3. UPSTREAM DATAFLOW")
print("-" * 70)
print("SYMBOL :", symbol)

api_names = [
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

for name in api_names:

    print("\n" + name)
    print("-" * 50)

    try:
        fn = getattr(adapter, name)
        result = fn(symbol)

        results[name] = result

        print("CALL      : PASS")
        print("TYPE      :", type(result).__name__)

        if isinstance(result, dict):

            print("KEY COUNT :", len(result))
            print("KEYS      :", list(result.keys()))

            for key in [
                "symbol",
                "price",
                "decision",
                "evidence",
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
                    print(f"{key:25} : DICT " f"({len(value)} keys)")
                    print(f"{'':25}   " f"keys={list(value.keys())[:20]}")

                elif isinstance(value, list):
                    print(f"{key:25} : LIST " f"({len(value)} items)")

                else:
                    print(f"{key:25} : " f"{type(value).__name__} = {value!r}")

        else:
            print("VALUE     :", repr(result)[:2000])

    except Exception:

        results[name] = None

        print("CALL      : FAIL")
        traceback.print_exc()


print("\n" + "=" * 70)
print("4. CROSS-LAYER DATA PRESENCE MATRIX")
print("=" * 70)

check_keys = [
    "decision",
    "evidence",
    "evidence_chain",
    "interpretation",
    "scenario_trace",
    "convergence",
    "trace",
    "traceability",
    "conclusion",
]

for name, result in results.items():

    print("\n" + name)

    if not isinstance(result, dict):
        print("  RESULT : NOT DICT")
        continue

    for key in check_keys:

        if key not in result:
            print(f"  {key:22} : ABSENT")
            continue

        value = result[key]

        if isinstance(value, dict):
            print(f"  {key:22} : " f"DICT keys={len(value)}")

        elif isinstance(value, list):
            print(f"  {key:22} : " f"LIST items={len(value)}")

        elif value is None:
            print(f"  {key:22} : NONE")

        elif value == "":
            print(f"  {key:22} : EMPTY STRING")

        else:
            print(f"  {key:22} : " f"{type(value).__name__}")


print("\n" + "=" * 70)
print("5. DIRECT TRACEABILITY DETAIL")
print("=" * 70)

trace_result = results.get("decision_traceability")

if isinstance(trace_result, dict):

    print("\nTRACEABILITY:")
    print(trace_result)

    print("\nTRACE:")
    print(trace_result.get("trace"))

    print("\nEVIDENCE CHAIN:")
    print(trace_result.get("evidence_chain"))

    print("\nSCENARIO TRACE:")
    print(trace_result.get("scenario_trace"))

    print("\nINTERPRETATION:")
    print(trace_result.get("interpretation"))

    print("\nCONCLUSION:")
    print(trace_result.get("conclusion"))

else:
    print("TRACEABILITY RESULT NOT AVAILABLE")


print("\n" + "=" * 70)
print("6. DECISION AUDIT DATAFLOW")
print("=" * 70)

audit = None

try:

    audit = adapter.decision_audit(symbol)

    print("AUDIT CALL : PASS")
    print("AUDIT TYPE :", type(audit).__name__)

    if isinstance(audit, dict):

        print("\nAUDIT KEYS:")
        print(list(audit.keys()))

        print("\nDECISION:")
        print(audit.get("decision"))

        print("\nEVIDENCE CHAIN:")
        print(audit.get("evidence_chain"))

        print("\nSCENARIO TRACE:")
        print(audit.get("scenario_trace"))

        print("\nINTERPRETATION:")
        print(audit.get("interpretation"))

        print("\nTRACEABILITY:")
        print(audit.get("traceability"))

        print("\nTRACE:")
        print(audit.get("trace"))

        print("\nCONCLUSION:")
        print(audit.get("conclusion"))

        print("\nAUDIT:")
        print(audit.get("audit"))

        print("\nAUDIT STATUS:")
        print(audit.get("audit_status"))

        print("\nGOVERNANCE:")
        print(audit.get("governance"))

    else:

        print("AUDIT RESULT IS NOT DICT")

except Exception:

    print("AUDIT CALL : FAIL")
    traceback.print_exc()


print("\n" + "=" * 70)
print("7. FINAL DATAFLOW SUMMARY")
print("=" * 70)

if isinstance(trace_result, dict):

    print("TRACEABILITY decision:", bool(trace_result.get("decision")))

    print("TRACEABILITY evidence_chain:", bool(trace_result.get("evidence_chain")))

    print("TRACEABILITY scenario_trace:", bool(trace_result.get("scenario_trace")))

    print("TRACEABILITY interpretation:", bool(trace_result.get("interpretation")))

    print("TRACEABILITY trace:", bool(trace_result.get("trace")))

if isinstance(audit, dict):

    print("AUDIT decision:", bool(audit.get("decision")))

    print("AUDIT evidence_chain:", bool(audit.get("evidence_chain")))

    print("AUDIT scenario_trace:", bool(audit.get("scenario_trace")))

    print("AUDIT interpretation:", bool(audit.get("interpretation")))

    print("AUDIT trace:", bool(audit.get("trace")))

    print("AUDIT status:", audit.get("audit_status"))

print("\n" + "=" * 70)
print("V3.8.2.3 DIAGNOSTIC COMPLETE")
print("=" * 70)

print("\nNO SOURCE PATCH PERFORMED.")
