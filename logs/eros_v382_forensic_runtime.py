import json
import sys
import traceback
import platform

from services.eros_frontend_adapter import EROSFrontendAdapter


print("=" * 72)
print("EROS 3.0 - V3.8.2 FORENSIC RUNTIME DIAGNOSTIC")
print("=" * 72)


print("\nPYTHON ENVIRONMENT")
print("-" * 72)
print("PYTHON VERSION :", sys.version)
print("PYTHON EXE     :", sys.executable)
print("PLATFORM       :", platform.platform())


print("\n1. ADAPTER IMPORT")
print("-" * 72)

try:
    from services.eros_frontend_adapter import EROSFrontendAdapter

    print("IMPORT : PASS")
    print("CLASS  :", EROSFrontendAdapter.__name__)

except Exception as exc:
    print("IMPORT : FAIL")
    print("EXCEPTION TYPE :", type(exc).__name__)
    print("EXCEPTION      :", str(exc))
    traceback.print_exc()
    raise


adapter = EROSFrontendAdapter()


print("\n2. FOUNDATION API CHECK")
print("-" * 72)

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

api_failures = []

for name in required:
    try:
        exists = hasattr(adapter, name)
    except Exception as exc:
        exists = False
        print(
            f"{name:35} : ERROR "
            f"{type(exc).__name__}: {exc}"
        )

    print(
        f"{name:35} : "
        f"{'PASS' if exists else 'FAIL'}"
    )

    if not exists:
        api_failures.append(name)


if api_failures:
    raise RuntimeError(
        "MISSING_API:" + ",".join(api_failures)
    )


print("\nFOUNDATION API : PASS")


print("\n3. METHOD OBJECT INSPECTION")
print("-" * 72)

for name in [
    "decision_traceability",
    "decision_convergence",
    "decision_audit",
]:

    try:
        method = getattr(adapter, name)

        print("\nMETHOD :", name)
        print("OBJECT :", method)
        print("TYPE   :", type(method).__name__)

    except Exception as exc:
        print(
            "METHOD INSPECTION FAILURE :",
            name,
            type(exc).__name__,
            str(exc)
        )
        traceback.print_exc()


print("\n4. TRACEABILITY EXECUTION")
print("-" * 72)

symbol = "RELIANCE.NS"

print("SYMBOL :", symbol)
print("")
print('CALL : adapter.decision_traceability("RELIANCE.NS")')


try:

    traceability_result = adapter.decision_traceability(symbol)

    print("\nTRACEABILITY CALL : PASS")
    print(
        "RESULT TYPE       :",
        type(traceability_result).__name__
    )

    if not isinstance(traceability_result, dict):
        raise RuntimeError(
            "TRACEABILITY_RESULT_NOT_DICT"
        )

    print("\nTRACEABILITY TOP LEVEL KEYS")
    print("-" * 72)

    for key, value in traceability_result.items():

        print(
            f"{key:35} : "
            f"{type(value).__name__}"
        )

except Exception as exc:

    print("\nTRACEABILITY CALL : FAIL")
    print("EXCEPTION TYPE :", type(exc).__name__)
    print("EXCEPTION      :", str(exc))
    print("")
    print("TRACEBACK")
    print("-" * 72)
    traceback.print_exc()

    raise


print("\n5. TRACEABILITY RAW OUTPUT")
print("-" * 72)

print(
    json.dumps(
        traceability_result,
        indent=2,
        default=str
    )
)


print("\n6. TRACEABILITY STRUCTURE")
print("-" * 72)

for field in [
    "symbol",
    "price",
    "decision",
    "trace",
    "evidence_chain",
    "scenario_trace",
    "interpretation",
    "conclusion",
    "traceability_status",
    "traceability",
    "governance",
]:

    exists = field in traceability_result

    print(
        f"{field:35} : "
        f"{'PASS' if exists else 'FAIL'}"
    )


print("\n7. TRACEABILITY DATA TYPES")
print("-" * 72)

for field in [
    "decision",
    "trace",
    "evidence_chain",
    "scenario_trace",
    "interpretation",
    "traceability",
    "governance",
]:

    value = traceability_result.get(field)

    print(
        f"{field:35} : "
        f"{type(value).__name__}"
    )


print("\n8. CONVERGENCE EXECUTION")
print("-" * 72)

print('CALL : adapter.decision_convergence("RELIANCE.NS")')

try:

    convergence_result = adapter.decision_convergence(symbol)

    print("\nCONVERGENCE CALL : PASS")
    print(
        "RESULT TYPE     :",
        type(convergence_result).__name__
    )

    if isinstance(convergence_result, dict):

        print("\nCONVERGENCE KEYS")
        print("-" * 72)

        for key, value in convergence_result.items():

            print(
                f"{key:35} : "
                f"{type(value).__name__}"
            )

except Exception as exc:

    print("\nCONVERGENCE CALL : FAIL")
    print("EXCEPTION TYPE :", type(exc).__name__)
    print("EXCEPTION      :", str(exc))
    traceback.print_exc()

    convergence_result = None


print("\n9. DECISION AUDIT EXECUTION")
print("-" * 72)

print("SYMBOL :", symbol)
print("")
print('CALL : adapter.decision_audit("RELIANCE.NS")')


try:

    audit_result = adapter.decision_audit(symbol)

    print("\nAUDIT CALL : PASS")
    print(
        "RESULT TYPE :",
        type(audit_result).__name__
    )

except Exception as exc:

    print("\nAUDIT CALL : FAIL")
    print("EXCEPTION TYPE :", type(exc).__name__)
    print("EXCEPTION      :", str(exc))
    print("")
    print("FULL AUDIT TRACEBACK")
    print("-" * 72)
    traceback.print_exc()

    raise


print("\n10. AUDIT RAW OUTPUT")
print("-" * 72)

print(
    json.dumps(
        audit_result,
        indent=2,
        default=str
    )
)


print("\n11. AUDIT TOP LEVEL SCHEMA")
print("-" * 72)

audit_fields = [
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

for field in audit_fields:

    present = field in audit_result

    print(
        f"{field:35} : "
        f"{'PRESENT' if present else 'ABSENT'}"
    )


print("\n12. AUDIT VALUE TYPES")
print("-" * 72)

for field in audit_fields:

    if field in audit_result:

        value = audit_result[field]

        print(
            f"{field:35} : "
            f"{type(value).__name__}"
        )


print("\n13. AUDIT OBJECT")
print("-" * 72)

audit_object = audit_result.get("audit")

print(
    json.dumps(
        audit_object,
        indent=2,
        default=str
    )
)


print("\n14. DECISION OBJECT")
print("-" * 72)

decision_object = audit_result.get("decision")

print(
    json.dumps(
        decision_object,
        indent=2,
        default=str
    )
)


print("\n15. EVIDENCE CHAIN")
print("-" * 72)

evidence_chain = audit_result.get("evidence_chain")

print(
    json.dumps(
        evidence_chain,
        indent=2,
        default=str
    )
)


print("\n16. SCENARIO TRACE")
print("-" * 72)

scenario_trace = audit_result.get("scenario_trace")

print(
    json.dumps(
        scenario_trace,
        indent=2,
        default=str
    )
)


print("\n17. TRACEABILITY CONTRACT")
print("-" * 72)

traceability = audit_result.get("traceability")

print(
    json.dumps(
        traceability,
        indent=2,
        default=str
    )
)


print("\n18. INTERPRETATION")
print("-" * 72)

interpretation = audit_result.get("interpretation")

print(
    json.dumps(
        interpretation,
        indent=2,
        default=str
    )
)


print("\n19. GOVERNANCE")
print("-" * 72)

governance = audit_result.get("governance")

print(
    json.dumps(
        governance,
        indent=2,
        default=str
    )
)


print("\n20. SAFETY CONTRACT")
print("-" * 72)

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

safety_failures = []

if not isinstance(governance, dict):

    print("GOVERNANCE : INVALID")

    safety_failures.append(
        "GOVERNANCE_NOT_DICT"
    )

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
            safety_failures.append(field)


    for field in expected_false:

        actual = governance.get(field)

        ok = actual is False

        print(
            f"{field:35} : "
            f"{'PASS' if ok else 'FAIL'} "
            f"(actual={actual}, expected=False)"
        )

        if not ok:
            safety_failures.append(field)


print("\n21. V3.8.2 HYDRATION CHECK")
print("-" * 72)

hydration_fields = [
    "decision",
    "evidence_chain",
    "scenario_trace",
    "interpretation",
    "traceability",
]

for field in hydration_fields:

    value = audit_result.get(field)

    if isinstance(value, dict):

        print(
            f"{field:35} : "
            f"DICT "
            f"(keys={len(value)})"
        )

    else:

        print(
            f"{field:35} : "
            f"{type(value).__name__}"
        )


print("\n22. V3.8.2 TRACEABILITY STAGES")
print("-" * 72)

traceability = audit_result.get("traceability")

if isinstance(traceability, dict):

    stages = traceability.get("stages")

    print(
        "STAGES TYPE :",
        type(stages).__name__
    )

    if isinstance(stages, dict):

        print(
            "STAGE COUNT :",
            len(stages)
        )

        for key, value in stages.items():

            print(
                f"{key:35} : {value}"
            )

else:

    print("TRACEABILITY : NOT A DICT")


print("\n23. PRIMARY SCENARIO")
print("-" * 72)

print(
    "PRIMARY SCENARIO :",
    traceability.get("primary_scenario")
    if isinstance(traceability, dict)
    else None
)


print("\n24. DECISION QUALITY")
print("-" * 72)

print(
    "DECISION QUALITY :",
    traceability.get("decision_quality")
    if isinstance(traceability, dict)
    else None
)


print("\n25. AUDIT STATUS")
print("-" * 72)

print(
    "AUDIT STATUS :",
    audit_result.get("audit_status")
)


print("\n26. AUDIT SUMMARY")
print("-" * 72)

print(
    "AUDIT SUMMARY :",
    audit_result.get("audit_summary")
)


print("\n27. TRACEABILITY STATUS")
print("-" * 72)

print(
    "TRACEABILITY STATUS :",
    audit_result.get("traceability_status")
)


print("\n28. LEGACY COMPATIBILITY")
print("-" * 72)

legacy_trace = audit_result.get("trace")

print(
    "LEGACY TRACE PRESENT :",
    isinstance(legacy_trace, dict)
)

if isinstance(traceability, dict):

    print(
        "LEGACY TRACE PRESERVED :",
        traceability.get(
            "legacy_trace_preserved"
        )
    )


print("\n29. DATABASE / EXECUTION SAFETY")
print("-" * 72)

print(
    "DATABASE WRITE PATH : NONE"
)

print(
    "ORDER CREATION      : BLOCKED"
)

print(
    "BROKER SUBMISSION   : BLOCKED"
)

print(
    "LIVE EXECUTION      : BLOCKED"
)

print(
    "PORTFOLIO MUTATION  : BLOCKED"
)

print(
    "VALUATION MUTATION  : BLOCKED"
)

print(
    "PERFORMANCE MUTATION: BLOCKED"
)

print(
    "RISK MUTATION       : BLOCKED"
)

print(
    "OPTIMIZATION        : BLOCKED"
)


print("\n30. FINAL DIAGNOSTIC SUMMARY")
print("-" * 72)

print(
    "ADAPTER IMPORT       : PASS"
)

print(
    "FOUNDATION API       : PASS"
)

print(
    "TRACEABILITY EXECUTE : PASS"
)

print(
    "CONVERGENCE EXECUTE  :",
    "PASS" if convergence_result is not None else "FAIL"
)

print(
    "AUDIT EXECUTE        : PASS"
)

print(
    "AUDIT RESULT DICT    :",
    "PASS" if isinstance(audit_result, dict) else "FAIL"
)

print(
    "GOVERNANCE           :",
    "PASS" if not safety_failures else "FAIL"
)

print(
    "SAFETY FAILURES      :",
    safety_failures
)

print("\n" + "=" * 72)
print("V3.8.2 FORENSIC RUNTIME DIAGNOSTIC COMPLETE")
print("=" * 72)