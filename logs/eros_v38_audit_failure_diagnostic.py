import json
import sys
import traceback

from services.eros_frontend_adapter import EROSFrontendAdapter


print("=" * 60)
print("EROS 3.0 - V3.8 DECISION AUDIT FAILURE DIAGNOSTIC")
print("=" * 60)


print("\n1. PYTHON")
print("-" * 60)
print(sys.version)


print("\n2. ADAPTER IMPORT")
print("-" * 60)

try:
    from services.eros_frontend_adapter import EROSFrontendAdapter

    adapter = EROSFrontendAdapter()

    print("IMPORT : PASS")
    print("CLASS  :", adapter.__class__.__name__)

except Exception as exc:
    print("IMPORT : FAIL")
    print("TYPE   :", type(exc).__name__)
    print("ERROR  :", repr(exc))
    traceback.print_exc()
    raise


print("\n3. FOUNDATION API DISCOVERY")
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

for name in foundation:
    ok = hasattr(adapter, name)
    print(f"{name:35} : {'PASS' if ok else 'FAIL'}")

    if not ok:
        raise RuntimeError(f"MISSING_API:{name}")


print("\n4. DECISION AUDIT METHOD")
print("-" * 60)

method = getattr(adapter, "decision_audit")

print("METHOD OBJECT :", method)
print("METHOD TYPE   :", type(method).__name__)


print("\n5. EXECUTION TARGET")
print("-" * 60)

symbol = "RELIANCE.NS"

print("SYMBOL :", symbol)


print("\n6. EXECUTING decision_audit")
print("-" * 60)

try:
    result = adapter.decision_audit(symbol)

    print("DECISION AUDIT CALL : PASS")
    print("RESULT TYPE         :", type(result).__name__)

except Exception as exc:
    print("DECISION AUDIT CALL : FAIL")
    print("EXCEPTION TYPE      :", type(exc).__name__)
    print("EXCEPTION           :", repr(exc))

    traceback.print_exc()

    raise


print("\n7. RESULT TYPE CHECK")
print("-" * 60)

if not isinstance(result, dict):
    print("RESULT DICT : FAIL")
    raise RuntimeError("AUDIT_RESULT_NOT_DICT")

print("RESULT DICT : PASS")


print("\n8. RAW V3.8 AUDIT OUTPUT")
print("-" * 60)

print(
    json.dumps(
        result,
        indent=2,
        default=str
    )
)


print("\n9. TOP LEVEL KEYS")
print("-" * 60)

for key, value in result.items():
    print(
        f"{str(key):35} : "
        f"{type(value).__name__}"
    )


print("\n10. EXPECTED TOP LEVEL SCHEMA")
print("-" * 60)

expected_top = [
    "symbol",
    "price",
    "decision",
    "audit",
    "conclusion",
    "governance",
]

for field in expected_top:
    present = field in result

    print(
        f"{field:35} : "
        f"{'PRESENT' if present else 'ABSENT'}"
    )


print("\n11. LEGACY / TRACEABILITY PRESERVATION")
print("-" * 60)

for field in [
    "trace",
    "traceability",
    "evidence_chain",
    "scenario_trace",
    "interpretation",
    "traceability_status",
]:
    present = field in result

    print(
        f"{field:35} : "
        f"{'PRESENT' if present else 'ABSENT'}"
    )


print("\n12. AUDIT OBJECT")
print("-" * 60)

audit = result.get("audit")

print("AUDIT TYPE :", type(audit).__name__)

if isinstance(audit, dict):

    print(
        json.dumps(
            audit,
            indent=2,
            default=str
        )
    )

else:

    print("AUDIT OBJECT IS NOT A DICT")


print("\n13. AUDIT FIELD INVENTORY")
print("-" * 60)

if isinstance(audit, dict):

    for key, value in audit.items():

        print(
            f"{str(key):35} : "
            f"{type(value).__name__}"
        )

else:

    print("NO AUDIT DICT AVAILABLE")


print("\n14. LIKELY V3.8 AUDIT CONTRACT")
print("-" * 60)

expected_audit_fields = [
    "status",
    "evidence_validation",
    "decision_consistency",
    "scenario_consistency",
    "trace_completeness",
    "governance_validation",
    "safety_validation",
    "conflict_detection",
    "audit_conclusion",
]

if isinstance(audit, dict):

    for field in expected_audit_fields:

        present = field in audit

        print(
            f"{field:35} : "
            f"{'PRESENT' if present else 'ABSENT'}"
        )

else:

    print("AUDIT STRUCTURE : NOT AVAILABLE")


print("\n15. DECISION OBJECT")
print("-" * 60)

decision = result.get("decision")

if isinstance(decision, dict):

    print(
        json.dumps(
            decision,
            indent=2,
            default=str
        )
    )

else:

    print("DECISION OBJECT TYPE :", type(decision).__name__)


print("\n16. TRACEABILITY OBJECT")
print("-" * 60)

traceability = result.get("traceability")

if isinstance(traceability, dict):

    print(
        json.dumps(
            traceability,
            indent=2,
            default=str
        )
    )

else:

    print(
        "TRACEABILITY TYPE :",
        type(traceability).__name__
    )


print("\n17. LEGACY TRACE OBJECT")
print("-" * 60)

legacy_trace = result.get("trace")

if isinstance(legacy_trace, dict):

    print("LEGACY TRACE : PRESENT")
    print(
        json.dumps(
            legacy_trace,
            indent=2,
            default=str
        )
    )

else:

    print(
        "LEGACY TRACE TYPE :",
        type(legacy_trace).__name__
    )


print("\n18. GOVERNANCE")
print("-" * 60)

governance = result.get("governance")

if isinstance(governance, dict):

    print(
        json.dumps(
            governance,
            indent=2,
            default=str
        )
    )

else:

    print(
        "GOVERNANCE TYPE :",
        type(governance).__name__
    )


print("\n19. SAFETY CONTRACT")
print("-" * 60)

if isinstance(governance, dict):

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


print("\n20. CONSISTENCY CHECK")
print("-" * 60)

checks = {}


checks["symbol"] = (
    result.get("symbol") == symbol
)


checks["result_is_dict"] = (
    isinstance(result, dict)
)


checks["audit_is_dict"] = (
    isinstance(result.get("audit"), dict)
)


checks["governance_is_dict"] = (
    isinstance(result.get("governance"), dict)
)


checks["traceability_preserved"] = (
    isinstance(result.get("traceability"), dict)
)


checks["legacy_trace_preserved"] = (
    isinstance(result.get("trace"), dict)
)


for name, value in checks.items():

    print(
        f"{name:35} : "
        f"{'PASS' if value else 'FAIL'}"
    )


print("\n21. AUDIT STRUCTURE DIAGNOSIS")
print("-" * 60)

if not isinstance(audit, dict):

    print(
        "DIAGNOSIS : "
        "V3.8 decision_audit returned a non-dict audit object."
    )

elif not audit:

    print(
        "DIAGNOSIS : "
        "V3.8 audit object is empty."
    )

else:

    missing = [
        field
        for field in expected_audit_fields
        if field not in audit
    ]

    if missing:

        print(
            "DIAGNOSIS : "
            "AUDIT OBJECT EXISTS BUT SCHEMA IS INCOMPLETE."
        )

        print("MISSING FIELDS:")

        for field in missing:
            print(" -", field)

    else:

        print(
            "DIAGNOSIS : "
            "EXPECTED AUDIT SCHEMA IS PRESENT."
        )


print("\n22. TRACEABILITY COMPATIBILITY")
print("-" * 60)

compatibility = {
    "legacy_trace": isinstance(result.get("trace"), dict),
    "traceability": isinstance(result.get("traceability"), dict),
    "evidence_chain": isinstance(result.get("evidence_chain"), dict),
    "scenario_trace": isinstance(result.get("scenario_trace"), dict),
    "traceability_status": isinstance(
        result.get("traceability_status"),
        str
    ),
}

for key, value in compatibility.items():

    print(
        f"{key:35} : "
        f"{'PASS' if value else 'FAIL'}"
    )


print("\n23. FINAL DIAGNOSTIC SUMMARY")
print("-" * 60)

print("ADAPTER IMPORT       : PASS")
print("API DISCOVERY        : PASS")
print("AUDIT EXECUTION      : PASS")
print("RESULT TYPE          : PASS")

if isinstance(audit, dict):
    print("AUDIT OBJECT         : PASS")
else:
    print("AUDIT OBJECT         : FAIL")

print(
    "TRACEABILITY         :",
    "PASS"
    if isinstance(result.get("traceability"), dict)
    else "FAIL"
)

print(
    "LEGACY TRACE         :",
    "PASS"
    if isinstance(result.get("trace"), dict)
    else "FAIL"
)

print(
    "GOVERNANCE           :",
    "PASS"
    if isinstance(result.get("governance"), dict)
    else "FAIL"
)

print("\n============================================================")
print("V3.8 DECISION AUDIT FAILURE DIAGNOSTIC COMPLETE")
print("============================================================")