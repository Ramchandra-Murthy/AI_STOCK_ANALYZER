import inspect
import json
import sys
import traceback

print("=" * 60)
print("EROS 3.0 - V3.8.2 DECISION AUDIT FAILURE CAPTURE")
print("LONG-FORM RUNTIME DIAGNOSTIC")
print("=" * 60)


print("\n1. PYTHON ENVIRONMENT")
print("-" * 60)

print("Python version :", sys.version)
print("Python executable :", sys.executable)
print("Python path:")

for index, item in enumerate(sys.path):
    print(f"  [{index}] {item}")


print("\n2. ADAPTER IMPORT")
print("-" * 60)

try:

    from services.eros_frontend_adapter import EROSFrontendAdapter

    print("IMPORT : PASS")
    print("CLASS  :", EROSFrontendAdapter.__name__)

except Exception as exc:

    print("IMPORT : FAIL")
    print("EXCEPTION TYPE :", type(exc).__name__)
    print("EXCEPTION      :", repr(exc))

    traceback.print_exc()

    raise


print("\n3. ADAPTER INSTANCE")
print("-" * 60)

try:

    adapter = EROSFrontendAdapter()

    print("INSTANCE : PASS")
    print("TYPE     :", type(adapter))

except Exception as exc:

    print("INSTANCE : FAIL")
    print("EXCEPTION TYPE :", type(exc).__name__)
    print("EXCEPTION      :", repr(exc))

    traceback.print_exc()

    raise


print("\n4. FOUNDATION API CHECK")
print("-" * 60)

foundation = [
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

foundation_failures = []

for name in foundation:

    exists = hasattr(adapter, name)

    print(f"{name:35} : " f"{'PASS' if exists else 'FAIL'}")

    if not exists:
        foundation_failures.append(name)


if foundation_failures:

    print("")
    print("FOUNDATION FAILURES:")
    for item in foundation_failures:
        print(" -", item)

    raise RuntimeError("FOUNDATION_API_FAILURE:" + ",".join(foundation_failures))


print("\nFOUNDATION API : VERIFIED")


print("\n5. DECISION AUDIT METHOD INSPECTION")
print("-" * 60)

method = adapter.decision_audit

print("METHOD OBJECT :", method)
print("METHOD TYPE   :", type(method).__name__)

try:
    signature = inspect.signature(method)
    print("SIGNATURE     :", signature)
except Exception as exc:
    print("SIGNATURE     : UNAVAILABLE")
    print("SIGNATURE ERR :", repr(exc))


print("\n6. DECISION TRACEABILITY METHOD INSPECTION")
print("-" * 60)

trace_method = adapter.decision_traceability

print("METHOD OBJECT :", trace_method)
print("METHOD TYPE   :", type(trace_method).__name__)

try:
    trace_signature = inspect.signature(trace_method)
    print("SIGNATURE     :", trace_signature)
except Exception as exc:
    print("SIGNATURE     : UNAVAILABLE")
    print("SIGNATURE ERR :", repr(exc))


print("\n7. EXECUTION TARGET")
print("-" * 60)

symbol = "RELIANCE.NS"

print("SYMBOL :", symbol)


print("\n8. DIRECT TRACEABILITY EXECUTION")
print("-" * 60)

traceability_result = None

try:

    print("CALL:")
    print('adapter.decision_traceability("RELIANCE.NS")')

    traceability_result = adapter.decision_traceability(symbol)

    print("")
    print("TRACEABILITY CALL : PASS")
    print("RESULT TYPE       :", type(traceability_result).__name__)

except Exception as exc:

    print("")
    print("TRACEABILITY CALL : FAIL")
    print("EXCEPTION TYPE    :", type(exc).__name__)
    print("EXCEPTION MESSAGE :", str(exc))
    print("EXCEPTION REPR    :", repr(exc))

    print("")
    print("TRACEBACK")
    print("-" * 60)

    traceback.print_exc()

    print("")
    print("TRACEBACK FORMAT")
    print("-" * 60)

    traceback_text = traceback.format_exc()
    print(traceback_text)


print("\n9. TRACEABILITY RESULT INSPECTION")
print("-" * 60)

if isinstance(traceability_result, dict):

    print("TRACEABILITY RESULT : DICT")

    print("")
    print("TOP LEVEL KEYS:")

    for key in traceability_result.keys():
        print(f"  {str(key):35} " f"{type(traceability_result[key]).__name__}")

    print("")
    print("TRACEABILITY JSON:")

    try:
        print(json.dumps(traceability_result, indent=2, default=str))
    except Exception as exc:
        print("JSON SERIALIZATION ERROR :", repr(exc))

else:

    print("TRACEABILITY RESULT :", type(traceability_result).__name__)


print("\n10. DECISION AUDIT EXECUTION")
print("-" * 60)

audit_result = None
audit_exception = None

try:

    print("")
    print("CALL:")
    print('adapter.decision_audit("RELIANCE.NS")')
    print("")

    audit_result = adapter.decision_audit(symbol)

    print("DECISION AUDIT CALL : PASS")
    print("RESULT TYPE         :", type(audit_result).__name__)

except Exception as exc:

    audit_exception = exc

    print("")
    print("DECISION AUDIT CALL : FAIL")
    print("EXCEPTION TYPE      :", type(exc).__name__)
    print("EXCEPTION MESSAGE   :", str(exc))
    print("EXCEPTION REPR      :", repr(exc))

    print("")
    print("FULL TRACEBACK")
    print("-" * 60)

    traceback.print_exc()

    print("")
    print("FORMATTED TRACEBACK")
    print("-" * 60)

    traceback_text = traceback.format_exc()

    print(traceback_text)


print("\n11. AUDIT RESULT TYPE")
print("-" * 60)

if audit_result is None:

    print("AUDIT RESULT : NONE")

else:

    print("AUDIT RESULT TYPE :", type(audit_result).__name__)


print("\n12. AUDIT TOP LEVEL SCHEMA")
print("-" * 60)

if isinstance(audit_result, dict):

    for key, value in audit_result.items():

        print(f"{str(key):35} : " f"{type(value).__name__}")

else:

    print("AUDIT RESULT IS NOT A DICT")


print("\n13. AUDIT JSON")
print("-" * 60)

if isinstance(audit_result, dict):

    try:

        print(json.dumps(audit_result, indent=2, default=str))

    except Exception as exc:

        print("AUDIT JSON SERIALIZATION FAILURE :", repr(exc))

else:

    print("NO DICT RESULT AVAILABLE")


print("\n14. CRITICAL V3.8.1 CONTRACT CHECK")
print("-" * 60)

if isinstance(audit_result, dict):

    expected = [
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

    for key in expected:

        print(f"{key:35} : " f"{'PRESENT' if key in audit_result else 'ABSENT'}")

else:

    print("CONTRACT CHECK SKIPPED " "(AUDIT RESULT NOT DICT)")


print("\n15. AUDIT OBJECT CHECK")
print("-" * 60)

if isinstance(audit_result, dict):

    audit = audit_result.get("audit")

    print("audit present :", audit is not None)

    print("audit type    :", type(audit).__name__)

    if isinstance(audit, dict):

        print("")
        print("AUDIT KEYS:")

        for key, value in audit.items():

            print(f"  {str(key):35} " f"{type(value).__name__}")

else:

    print("AUDIT RESULT UNAVAILABLE")


print("\n16. LEGACY TRACE CHECK")
print("-" * 60)

if isinstance(audit_result, dict):

    trace = audit_result.get("trace")

    print("trace present :", "trace" in audit_result)

    print("trace type    :", type(trace).__name__)

else:

    print("LEGACY TRACE UNAVAILABLE")


print("\n17. NEW TRACEABILITY CHECK")
print("-" * 60)

if isinstance(audit_result, dict):

    traceability = audit_result.get("traceability")

    print("traceability present :", "traceability" in audit_result)

    print("traceability type    :", type(traceability).__name__)

    if isinstance(traceability, dict):

        print("")
        print("TRACEABILITY OBJECT:")

        print(json.dumps(traceability, indent=2, default=str))

else:

    print("TRACEABILITY UNAVAILABLE")


print("\n18. GOVERNANCE CHECK")
print("-" * 60)

if isinstance(audit_result, dict):

    governance = audit_result.get("governance")

    print("governance present :", "governance" in audit_result)

    print("governance type    :", type(governance).__name__)

    if isinstance(governance, dict):

        print(json.dumps(governance, indent=2, default=str))

else:

    print("GOVERNANCE UNAVAILABLE")


print("\n19. SAFETY CONTRACT")
print("-" * 60)

if isinstance(audit_result, dict):

    governance = audit_result.get("governance", {})

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

    for key in expected_true:

        value = governance.get(key)

        print(f"{key:35} : " f"{'PASS' if value is True else 'FAIL'} " f"(actual={value})")

    for key in expected_false:

        value = governance.get(key)

        print(f"{key:35} : " f"{'PASS' if value is False else 'FAIL'} " f"(actual={value})")

else:

    print("SAFETY CHECK : SKIPPED")


print("\n20. INTERNAL METHOD SOURCE LOCATION")
print("-" * 60)

try:

    print("decision_audit source file :", inspect.getsourcefile(adapter.decision_audit))

    print("decision_audit source lines :", inspect.getsourcelines(adapter.decision_audit)[1])

except Exception as exc:

    print("SOURCE LOCATION ERROR :", repr(exc))


print("\n21. TRACEBACK SUMMARY")
print("-" * 60)

if audit_exception is not None:

    print("AUDIT EXECUTION FAILED")

    print("TYPE    :", type(audit_exception).__name__)

    print("MESSAGE :", str(audit_exception))

else:

    print("AUDIT EXECUTION COMPLETED " "WITHOUT PYTHON EXCEPTION")


print("\n22. FINAL DIAGNOSTIC STATUS")
print("-" * 60)

if audit_exception is not None:

    print("V3.8.1 SOURCE : VALID")
    print("V3.8.1 IMPORT : VALID")
    print("V3.8.1 API    : PRESENT")
    print("AUDIT RUNTIME : FAILED")
    print("")
    print("NEXT ACTION : USE TRACEBACK ABOVE")
    print("NO SOURCE PATCH WAS PERFORMED " "BY THIS DIAGNOSTIC")

elif not isinstance(audit_result, dict):

    print("V3.8.1 SOURCE : VALID")
    print("V3.8.1 IMPORT : VALID")
    print("V3.8.1 API    : PRESENT")
    print("AUDIT RUNTIME : FAILED")
    print("REASON       : RESULT IS NOT DICT")

else:

    print("V3.8.1 SOURCE : VALID")
    print("V3.8.1 IMPORT : VALID")
    print("V3.8.1 API    : PRESENT")
    print("AUDIT RUNTIME : COMPLETED")
    print("RESULT TYPE   : DICT")

print("")
print("=" * 60)
print("V3.8.2 FAILURE CAPTURE COMPLETE")
print("=" * 60)
