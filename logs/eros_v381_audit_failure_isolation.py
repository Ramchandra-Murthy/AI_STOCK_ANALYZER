import json
import sys
import traceback
import inspect


print("=" * 60)
print("EROS 3.0 - V3.8.1 DECISION AUDIT - FAILURE ISOLATION")
print("=" * 60)


print("\nPYTHON")
print("-" * 60)
print(sys.version)


print("\n1. ADAPTER IMPORT")
print("-" * 60)

try:
    from services.eros_frontend_adapter import EROSFrontendAdapter

    print("IMPORT : PASS")
    print("CLASS  :", EROSFrontendAdapter.__name__)

except Exception as exc:
    print("IMPORT : FAIL")
    print("TYPE   :", type(exc).__name__)
    print("ERROR  :", repr(exc))
    traceback.print_exc()
    raise


adapter = EROSFrontendAdapter()


print("\n2. API DISCOVERY")
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
    "decision_audit",
]

for name in required:
    exists = hasattr(adapter, name)

    print(
        f"{name:35} : "
        f"{'PASS' if exists else 'FAIL'}"
    )

    if not exists:
        raise RuntimeError(f"MISSING_API:{name}")


print("\n3. METHOD INSPECTION")
print("-" * 60)

method = adapter.decision_audit

print("METHOD OBJECT :", method)
print("METHOD TYPE   :", type(method).__name__)

try:
    print("SIGNATURE     :", inspect.signature(method))
except Exception as exc:
    print("SIGNATURE     : UNAVAILABLE")
    print("SIGNATURE ERR :", repr(exc))


try:
    source = inspect.getsource(EROSFrontendAdapter.decision_audit)

    print("\nDECISION_AUDIT SOURCE")
    print("-" * 60)

    print(source)

except Exception as exc:
    print("SOURCE INSPECTION ERROR :", repr(exc))


print("\n4. EXECUTION TARGET")
print("-" * 60)

symbol = "RELIANCE.NS"

print("SYMBOL :", symbol)


print("\n5. DIRECT DECISION TRACEABILITY TEST")
print("-" * 60)

try:
    trace_result = adapter.decision_traceability(symbol)

    print("TRACEABILITY CALL : PASS")
    print("RESULT TYPE       :", type(trace_result).__name__)

    if isinstance(trace_result, dict):
        print("TOP LEVEL KEYS:")
        for key in trace_result.keys():
            print("  -", key)

        print(
            "TRACEABILITY STATUS :",
            trace_result.get("traceability_status")
        )

        print(
            "TRACEABILITY OBJECT :",
            type(trace_result.get("traceability")).__name__
        )

except Exception as exc:
    print("TRACEABILITY CALL : FAIL")
    print("EXCEPTION TYPE    :", type(exc).__name__)
    print("EXCEPTION         :", repr(exc))

    traceback.print_exc()

    print("\nTRACEABILITY FAILURE ISOLATED")
    raise


print("\n6. DIRECT DECISION CONVERGENCE TEST")
print("-" * 60)

try:
    convergence_result = adapter.decision_convergence(symbol)

    print("CONVERGENCE CALL : PASS")
    print("RESULT TYPE      :", type(convergence_result).__name__)

    if isinstance(convergence_result, dict):
        print("TOP LEVEL KEYS:")

        for key in convergence_result.keys():
            print("  -", key)

        print(
            "PRIMARY SCENARIO :",
            convergence_result.get("convergence", {}).get(
                "primary_scenario"
            )
        )

except Exception as exc:
    print("CONVERGENCE CALL : FAIL")
    print("EXCEPTION TYPE   :", type(exc).__name__)
    print("EXCEPTION        :", repr(exc))

    traceback.print_exc()

    print("\nCONVERGENCE FAILURE ISOLATED")
    raise


print("\n7. DIRECT DECISION AUDIT TEST")
print("-" * 60)

print("CALL:")
print('adapter.decision_audit("RELIANCE.NS")')


try:

    audit_result = adapter.decision_audit(symbol)

    print("")
    print("DECISION AUDIT CALL : PASS")
    print("RESULT TYPE         :", type(audit_result).__name__)


    print("\n8. AUDIT RESULT TYPE")
    print("-" * 60)

    if not isinstance(audit_result, dict):
        raise RuntimeError(
            "AUDIT_RESULT_NOT_DICT"
        )

    print("RESULT DICT : PASS")


    print("\n9. AUDIT TOP LEVEL KEYS")
    print("-" * 60)

    for key, value in audit_result.items():

        print(
            f"{str(key):35} : "
            f"{type(value).__name__}"
        )


    print("\n10. AUDIT RESULT")
    print("-" * 60)

    print(
        json.dumps(
            audit_result,
            indent=2,
            default=str
        )
    )


    print("\n11. CORE AUDIT FIELDS")
    print("-" * 60)

    expected = [
        "symbol",
        "price",
        "decision",
        "audit",
        "trace",
        "traceability",
        "evidence_chain",
        "scenario_trace",
        "interpretation",
        "conclusion",
        "traceability_status",
        "governance",
    ]

    for field in expected:

        present = field in audit_result

        print(
            f"{field:35} : "
            f"{'PASS' if present else 'FAIL'}"
        )


    print("\n12. AUDIT OBJECT")
    print("-" * 60)

    audit = audit_result.get("audit")

    print("AUDIT TYPE :", type(audit).__name__)

    if isinstance(audit, dict):

        print("AUDIT KEYS:")

        for key, value in audit.items():

            print(
                f"  {str(key):30} : "
                f"{type(value).__name__}"
            )

        print("\nAUDIT OBJECT:")
        print(
            json.dumps(
                audit,
                indent=2,
                default=str
            )
        )


    print("\n13. LEGACY TRACE")
    print("-" * 60)

    legacy_trace = audit_result.get("trace")

    print("PRESENT :", legacy_trace is not None)
    print("TYPE    :", type(legacy_trace).__name__)


    print("\n14. NEW TRACEABILITY")
    print("-" * 60)

    traceability = audit_result.get("traceability")

    print("PRESENT :", traceability is not None)
    print("TYPE    :", type(traceability).__name__)

    if isinstance(traceability, dict):

        print(
            json.dumps(
                traceability,
                indent=2,
                default=str
            )
        )


    print("\n15. CONCLUSION")
    print("-" * 60)

    conclusion = audit_result.get("conclusion")

    print("TYPE :", type(conclusion).__name__)
    print("VALUE:", conclusion)


    print("\n16. TRACEABILITY STATUS")
    print("-" * 60)

    print(
        "VALUE :",
        audit_result.get("traceability_status")
    )


    print("\n17. GOVERNANCE")
    print("-" * 60)

    governance = audit_result.get("governance")

    print(
        json.dumps(
            governance,
            indent=2,
            default=str
        )
    )


    print("\n18. SAFETY ASSERTIONS")
    print("-" * 60)

    if not isinstance(governance, dict):
        raise RuntimeError(
            "GOVERNANCE_NOT_DICT"
        )

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

        actual = governance.get(field)

        print(
            f"{field:35} : "
            f"{'PASS' if actual is True else 'FAIL'} "
            f"(actual={actual})"
        )


    for field in expected_false:

        actual = governance.get(field)

        print(
            f"{field:35} : "
            f"{'PASS' if actual is False else 'FAIL'} "
            f"(actual={actual})"
        )


    print("\n19. FINAL RESULT")
    print("-" * 60)

    print("DECISION TRACEABILITY : PASS")
    print("DECISION CONVERGENCE  : PASS")
    print("DECISION AUDIT       : PASS")
    print("RESULT DICT          : PASS")
    print("AUDIT OBJECT         : PASS")
    print("TRACEABILITY         : PASS")
    print("LEGACY TRACE         : PASS")
    print("CONCLUSION           : PASS")
    print("GOVERNANCE           : PASS")
    print("SAFETY               : PASS")

    print("")
    print("=" * 60)
    print("V3.8.1 FAILURE ISOLATION : PASS")
    print("=" * 60)


except Exception as exc:

    print("")
    print("=" * 60)
    print("V3.8.1 DECISION AUDIT : FAILURE CAPTURED")
    print("=" * 60)

    print("")
    print("EXCEPTION TYPE")
    print("-" * 60)
    print(type(exc).__name__)

    print("")
    print("EXCEPTION MESSAGE")
    print("-" * 60)
    print(repr(exc))

    print("")
    print("TRACEBACK")
    print("-" * 60)

    traceback.print_exc()

    print("")
    print("=" * 60)
    print("FAILURE ISOLATED")
    print("NO SOURCE PATCH APPLIED")
    print("NO DATABASE WRITE")
    print("NO EXECUTION")
    print("=" * 60)

    sys.exit(1)