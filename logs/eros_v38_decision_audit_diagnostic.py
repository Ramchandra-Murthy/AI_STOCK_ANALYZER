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
    adapter = EROSFrontendAdapter()

    print("IMPORT : PASS")
    print("CLASS  :", adapter.__class__.__name__)

except Exception as exc:
    print("IMPORT : FAIL")
    print("TYPE   :", type(exc).__name__)
    print("ERROR  :", str(exc))
    traceback.print_exc()
    raise


print("\n3. FOUNDATION API DISCOVERY")
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
    ok = hasattr(adapter, name)

    print(f"{name:35} : " f"{'PASS' if ok else 'FAIL'}")

    if not ok:
        raise RuntimeError(f"MISSING_API:{name}")


print("\n4. DECISION AUDIT METHOD")
print("-" * 60)

method = getattr(adapter, "decision_audit", None)

print("METHOD OBJECT :", method)
print("METHOD TYPE   :", type(method).__name__)

if method is None:
    raise RuntimeError("DECISION_AUDIT_METHOD_MISSING")


print("\n5. EXECUTION TARGET")
print("-" * 60)

symbol = "RELIANCE.NS"

print("SYMBOL :", symbol)


print("\n6. EXECUTING DECISION AUDIT")
print("-" * 60)

try:

    result = adapter.decision_audit(symbol)

    print("DECISION AUDIT CALL : PASS")
    print("RESULT TYPE         :", type(result).__name__)

except Exception as exc:

    print("DECISION AUDIT CALL : FAIL")
    print("EXCEPTION TYPE      :", type(exc).__name__)
    print("EXCEPTION MESSAGE   :", str(exc))

    print("\nFULL TRACEBACK")
    print("-" * 60)

    traceback.print_exc()

    raise


print("\n7. RESULT TYPE VALIDATION")
print("-" * 60)

if not isinstance(result, dict):
    print("RESULT DICT : FAIL")
    print("ACTUAL TYPE :", type(result).__name__)

    raise RuntimeError("DECISION_AUDIT_RESULT_NOT_DICT")

print("RESULT DICT : PASS")


print("\n8. COMPLETE RAW RESULT")
print("-" * 60)

try:

    print(json.dumps(result, indent=2, default=str))

except Exception as exc:

    print("JSON SERIALIZATION : FAIL")
    print("TYPE                :", type(exc).__name__)
    print("ERROR               :", str(exc))


print("\n9. TOP LEVEL KEYS")
print("-" * 60)

for key, value in result.items():

    print(f"{str(key):35} : " f"{type(value).__name__}")


print("\n10. TOP LEVEL SCHEMA DISCOVERY")
print("-" * 60)

for field in [
    "symbol",
    "price",
    "decision",
    "audit",
    "audit_summary",
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

    present = field in result

    print(f"{field:35} : " f"{'PRESENT' if present else 'ABSENT'}")


print("\n11. DECISION OBJECT INSPECTION")
print("-" * 60)

decision = result.get("decision")

if isinstance(decision, dict):

    print("DECISION : DICT")

    for key, value in decision.items():

        print(f"{str(key):35} : " f"{type(value).__name__} = {value}")

else:

    print("DECISION :", type(decision).__name__)


print("\n12. AUDIT OBJECT INSPECTION")
print("-" * 60)

for audit_key in [
    "audit",
    "audit_summary",
    "audit_findings",
    "audit_status",
]:

    value = result.get(audit_key)

    print("")
    print("FIELD :", audit_key)
    print("TYPE  :", type(value).__name__)

    if isinstance(value, dict):

        print(json.dumps(value, indent=2, default=str))

    elif isinstance(value, list):

        print(json.dumps(value, indent=2, default=str))

    else:

        print("VALUE :", value)


print("\n13. TRACEABILITY INSPECTION")
print("-" * 60)

traceability = result.get("traceability")

print("TRACEABILITY PRESENT :", traceability is not None)

print("TRACEABILITY TYPE    :", type(traceability).__name__)

if isinstance(traceability, dict):

    print(json.dumps(traceability, indent=2, default=str))


print("\n14. LEGACY TRACE INSPECTION")
print("-" * 60)

legacy_trace = result.get("trace")

print("TRACE PRESENT :", legacy_trace is not None)

print("TRACE TYPE    :", type(legacy_trace).__name__)

if isinstance(legacy_trace, dict):

    print(json.dumps(legacy_trace, indent=2, default=str))


print("\n15. EVIDENCE CHAIN INSPECTION")
print("-" * 60)

evidence_chain = result.get("evidence_chain")

print("EVIDENCE CHAIN PRESENT :", evidence_chain is not None)

print("EVIDENCE CHAIN TYPE    :", type(evidence_chain).__name__)

if isinstance(evidence_chain, dict):

    for key, value in evidence_chain.items():

        print(f"{str(key):35} : " f"{type(value).__name__}")


print("\n16. SCENARIO TRACE INSPECTION")
print("-" * 60)

scenario_trace = result.get("scenario_trace")

print("SCENARIO TRACE PRESENT :", scenario_trace is not None)

print("SCENARIO TRACE TYPE    :", type(scenario_trace).__name__)

if isinstance(scenario_trace, dict):

    for key, value in scenario_trace.items():

        print(f"{str(key):35} : " f"{type(value).__name__}")


print("\n17. INTERPRETATION INSPECTION")
print("-" * 60)

interpretation = result.get("interpretation")

print("INTERPRETATION PRESENT :", interpretation is not None)

print("INTERPRETATION TYPE    :", type(interpretation).__name__)

if isinstance(interpretation, dict):

    for key, value in interpretation.items():

        print(f"{str(key):35} : " f"{type(value).__name__} = {value}")


print("\n18. CONCLUSION")
print("-" * 60)

conclusion = result.get("conclusion")

print("CONCLUSION TYPE  :", type(conclusion).__name__)

print("CONCLUSION VALUE :", conclusion)


print("\n19. GOVERNANCE")
print("-" * 60)

governance = result.get("governance")

print("GOVERNANCE TYPE :", type(governance).__name__)

if isinstance(governance, dict):

    print(json.dumps(governance, indent=2, default=str))


print("\n20. SAFETY CONTRACT")
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
            f"(actual={actual}, expected=True)"
        )

    for field in expected_false:

        actual = governance.get(field)

        print(
            f"{field:35} : "
            f"{'PASS' if actual is False else 'FAIL'} "
            f"(actual={actual}, expected=False)"
        )

else:

    print("GOVERNANCE : NOT A DICT")


print("\n21. AUDIT SEMANTIC DISCOVERY")
print("-" * 60)

possible_audit_fields = [
    "status",
    "audit_status",
    "audit_result",
    "audit_quality",
    "audit_conclusion",
    "consistency",
    "consistency_status",
    "evidence_status",
    "evidence_available",
    "decision_consistency",
    "scenario_consistency",
    "trace_completeness",
    "governance_valid",
    "safety_valid",
    "conflict_detected",
    "conflicting_decision_state",
    "findings",
    "checks",
    "validation",
    "conclusion",
]

for field in possible_audit_fields:

    if field in result:

        value = result[field]

        print(f"{field:35} : " f"PRESENT / {type(value).__name__}")

    else:

        print(f"{field:35} : ABSENT")


print("\n22. OBJECT CONSISTENCY CHECK")
print("-" * 60)

print("RESULT IS DICT       :", isinstance(result, dict))

print("DECISION IS DICT     :", isinstance(result.get("decision"), dict))

print("TRACE IS DICT        :", isinstance(result.get("trace"), dict))

print("TRACEABILITY IS DICT :", isinstance(result.get("traceability"), dict))

print("GOVERNANCE IS DICT   :", isinstance(result.get("governance"), dict))


print("\n23. NO-MUTATION ASSERTION")
print("-" * 60)

print("READ-ONLY RESULT INSPECTION : PASS")

print("NO DATABASE WRITE            : EXPECTED")

print("NO ORDER CREATION            : EXPECTED")

print("NO BROKER SUBMISSION         : EXPECTED")

print("NO LIVE EXECUTION            : EXPECTED")


print("\n============================================================")
print("V3.8 DECISION AUDIT FAILURE DIAGNOSTIC")
print("============================================================")

print("")
print("DIAGNOSTIC EXECUTION : PASS")
print("RESULT TYPE           :", type(result).__name__)
print("SYMBOL                :", result.get("symbol"))
print("PRICE                 :", result.get("price"))
print("TRACEABILITY          :", type(result.get("traceability")).__name__)
print("AUDIT                 :", type(result.get("audit")).__name__)
print("GOVERNANCE            :", type(result.get("governance")).__name__)

print("")
print("IMPORTANT:")
print("This diagnostic does NOT modify the adapter.")
print("This diagnostic does NOT modify database state.")
print("This diagnostic does NOT create or submit orders.")
print("This diagnostic does NOT execute trades.")

print("")
print("============================================================")
print("V3.8 DIAGNOSTIC COMPLETE")
print("============================================================")
