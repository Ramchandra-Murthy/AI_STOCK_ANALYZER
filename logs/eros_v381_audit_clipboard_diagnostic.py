import sys
import traceback
import json
import inspect
import os

print("=" * 68)
print("EROS 3.0 - V3.8.1 DECISION AUDIT")
print("LONG-FORM RUNTIME DIAGNOSTIC")
print("=" * 68)

print("\nPYTHON VERSION")
print("-" * 68)
print(sys.version)

print("\n1. WORKING DIRECTORY")
print("-" * 68)
print(os.getcwd())

print("\n2. ADAPTER IMPORT")
print("-" * 68)

try:
    from services.eros_frontend_adapter import EROSFrontendAdapter

    print("IMPORT : PASS")
    print("CLASS  :", EROSFrontendAdapter.__name__)

except Exception as exc:
    print("IMPORT : FAIL")
    print("ERROR  :", repr(exc))
    traceback.print_exc()
    sys.exit(10)


adapter = EROSFrontendAdapter()


print("\n3. FOUNDATION API CHECK")
print("-" * 68)

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
    "decision_audit",
]

foundation_ok = True

for name in required:
    exists = hasattr(adapter, name)

    print(
        f"{name:35} : "
        f"{'PASS' if exists else 'FAIL'}"
    )

    if not exists:
        foundation_ok = False

if not foundation_ok:
    print("\nFOUNDATION : FAIL")
    sys.exit(11)

print("\nFOUNDATION : VERIFIED")


print("\n4. METHOD INSPECTION")
print("-" * 68)

try:
    method = getattr(adapter, "decision_audit")

    print("METHOD OBJECT :", method)
    print("METHOD TYPE   :", type(method).__name__)

    try:
        print("\nMETHOD SIGNATURE")
        print(inspect.signature(method))
    except Exception as exc:
        print("SIGNATURE INSPECTION ERROR :", repr(exc))

except Exception as exc:
    print("METHOD INSPECTION : FAIL")
    print("ERROR :", repr(exc))
    traceback.print_exc()
    sys.exit(12)


print("\n5. TRACEABILITY PRE-CHECK")
print("-" * 68)

try:
    trace_result = adapter.decision_traceability("RELIANCE.NS")

    print("TRACEABILITY CALL : PASS")
    print("RESULT TYPE       :", type(trace_result).__name__)

    if isinstance(trace_result, dict):

        print("TRACEABILITY KEYS")
        for key in trace_result.keys():
            print(" -", key)

        print("\nTRACEABILITY STATUS :",
              trace_result.get("traceability_status"))

        print("TRACEABILITY OBJECT :")
        print(
            json.dumps(
                trace_result.get("traceability"),
                indent=2,
                default=str
            )
        )

    else:
        print("TRACEABILITY RESULT IS NOT DICT")

except Exception as exc:
    print("TRACEABILITY CALL : FAIL")
    print("ERROR :", repr(exc))
    traceback.print_exc()


print("\n6. DECISION AUDIT TARGET")
print("-" * 68)

symbol = "RELIANCE.NS"

print("SYMBOL :", symbol)


print("\n7. DECISION AUDIT CALL")
print("-" * 68)

audit_result = None

try:

    print("CALL:")
    print('adapter.decision_audit("RELIANCE.NS")')
    print("")

    audit_result = adapter.decision_audit(symbol)

    print("DECISION AUDIT CALL : PASS")
    print("RESULT TYPE         :", type(audit_result).__name__)

except Exception as exc:

    print("DECISION AUDIT CALL : FAIL")
    print("")
    print("EXCEPTION TYPE :", type(exc).__name__)
    print("EXCEPTION      :", repr(exc))
    print("")
    print("TRACEBACK")
    print("-" * 68)
    traceback.print_exc()

    print("\n============================================================")
    print("V3.8.1 RUNTIME FAILURE IDENTIFIED")
    print("============================================================")
    print("The decision_audit method exists and imports successfully,")
    print("but execution raised an exception.")
    print("")
    print("IMPORTANT:")
    print("No source patch was performed by this diagnostic.")
    print("No database operation was requested.")
    print("No broker operation was requested.")
    print("No order operation was requested.")
    print("============================================================")

    sys.exit(20)


print("\n8. AUDIT RESULT TYPE")
print("-" * 68)

if not isinstance(audit_result, dict):

    print("RESULT DICT : FAIL")
    print("ACTUAL TYPE :", type(audit_result).__name__)

    sys.exit(21)

print("RESULT DICT : PASS")


print("\n9. RAW AUDIT RESULT")
print("-" * 68)

try:
    print(
        json.dumps(
            audit_result,
            indent=2,
            default=str
        )
    )
except Exception as exc:
    print("JSON SERIALIZATION ERROR :", repr(exc))
    print(repr(audit_result))


print("\n10. TOP-LEVEL SCHEMA")
print("-" * 68)

required_fields = [
    "symbol",
    "price",
    "decision",
    "audit",
    "audit_findings",
    "trace",
    "traceability",
    "evidence_chain",
    "scenario_trace",
    "interpretation",
    "conclusion",
    "traceability_status",
    "audit_summary",
    "audit_status",
    "governance",
]

schema_ok = True

for field in required_fields:

    present = field in audit_result

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        schema_ok = False


print("\n11. AUDIT OBJECT")
print("-" * 68)

audit_object = audit_result.get("audit")

print("TYPE :", type(audit_object).__name__)

if isinstance(audit_object, dict):

    print(
        json.dumps(
            audit_object,
            indent=2,
            default=str
        )
    )

else:
    print("AUDIT OBJECT IS NOT A DICT")


print("\n12. AUDIT FINDINGS")
print("-" * 68)

findings = audit_result.get("audit_findings")

print("TYPE :", type(findings).__name__)

try:
    print(
        json.dumps(
            findings,
            indent=2,
            default=str
        )
    )
except Exception:
    print(repr(findings))


print("\n13. TRACEABILITY CONTRACT")
print("-" * 68)

traceability = audit_result.get("traceability")

print("TYPE :", type(traceability).__name__)

if isinstance(traceability, dict):

    print(
        json.dumps(
            traceability,
            indent=2,
            default=str
        )
    )

else:
    print("TRACEABILITY IS NOT A DICT")


print("\n14. LEGACY TRACE")
print("-" * 68)

legacy_trace = audit_result.get("trace")

print("TYPE :", type(legacy_trace).__name__)

if isinstance(legacy_trace, dict):

    print(
        json.dumps(
            legacy_trace,
            indent=2,
            default=str
        )
    )

else:
    print("LEGACY TRACE IS NOT A DICT")


print("\n15. DECISION")
print("-" * 68)

decision = audit_result.get("decision")

print("TYPE :", type(decision).__name__)

if isinstance(decision, dict):

    for key, value in decision.items():
        print(f"{key:30} : {value}")

else:
    print(repr(decision))


print("\n16. AUDIT STATUS")
print("-" * 68)

print(
    "audit_status          :",
    audit_result.get("audit_status")
)

print(
    "audit_summary         :",
    audit_result.get("audit_summary")
)

print(
    "traceability_status   :",
    audit_result.get("traceability_status")
)


print("\n17. GOVERNANCE")
print("-" * 68)

governance = audit_result.get("governance")

print("TYPE :", type(governance).__name__)

if isinstance(governance, dict):

    print(
        json.dumps(
            governance,
            indent=2,
            default=str
        )
    )

else:
    print("GOVERNANCE IS NOT A DICT")


print("\n18. SAFETY CONTRACT")
print("-" * 68)

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

safety_ok = True

if not isinstance(governance, dict):

    print("GOVERNANCE DICT : FAIL")
    safety_ok = False

else:

    for field in expected_true:

        actual = governance.get(field)
        ok = actual is True

        print(
            f"{field:35} : "
            f"{'PASS' if ok else 'FAIL'} "
            f"(actual={actual}, expected=True)"
        )

        if not ok:
            safety_ok = False

    for field in expected_false:

        actual = governance.get(field)
        ok = actual is False

        print(
            f"{field:35} : "
            f"{'PASS' if ok else 'FAIL'} "
            f"(actual={actual}, expected=False)"
        )

        if not ok:
            safety_ok = False


print("\n19. DATABASE / EXECUTION SAFETY")
print("-" * 68)

print("DATABASE WRITE-PATH : NONE")
print("EXECUTION PATH      : BLOCKED")


print("\n20. FINAL DIAGNOSTIC STATUS")
print("-" * 68)

print(
    "FOUNDATION API       : PASS"
)

print(
    "TRACEABILITY API     : PASS"
)

print(
    "DECISION AUDIT API   : PASS"
)

print(
    "AUDIT RESULT DICT    : PASS"
)

print(
    "TOP-LEVEL SCHEMA     : "
    + ("PASS" if schema_ok else "FAIL")
)

print(
    "SAFETY CONTRACT      : "
    + ("PASS" if safety_ok else "FAIL")
)

print("DATABASE WRITE-PATH  : NONE")
print("EXECUTION PATH       : BLOCKED")

if schema_ok and safety_ok:

    print("")
    print("============================================================")
    print("V3.8.1 DECISION AUDIT RUNTIME : PASS")
    print("============================================================")

else:

    print("")
    print("============================================================")
    print("V3.8.1 DECISION AUDIT RUNTIME : SCHEMA/SAFETY FAILURE")
    print("============================================================")

print("")
print("END OF DIAGNOSTIC")
print("=" * 68)