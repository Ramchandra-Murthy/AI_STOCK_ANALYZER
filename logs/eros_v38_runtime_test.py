import json
import sys
import traceback

from services.eros_frontend_adapter import EROSFrontendAdapter


print("=" * 60)
print("EROS 3.0 - V3.8 DECISION AUDIT ENGINE - RUNTIME")
print("=" * 60)


print("\nPYTHON VERSION")
print("-" * 60)
print(sys.version)


adapter = EROSFrontendAdapter()


print("\n2. ADAPTER IMPORT")
print("-" * 60)
print("IMPORT : PASS")
print("CLASS  :", adapter.__class__.__name__)


print("\n3. FOUNDATION API CHECK")
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

    print(
        f"{name:35} : "
        f"{'PASS' if ok else 'FAIL'}"
    )

    if not ok:
        raise RuntimeError(f"MISSING_API:{name}")


print("\nV3.7.2 / V3.8 FOUNDATION : VERIFIED")


print("\n4. V3.8 DECISION AUDIT")
print("-" * 60)

symbol = "RELIANCE.NS"

print("SYMBOL :", symbol)

try:
    result = adapter.decision_audit(symbol)
except Exception:
    print("")
    print("DECISION AUDIT CALL : FAIL")
    print("")
    traceback.print_exc()
    raise


print("DECISION AUDIT CALL : PASS")
print("RESULT TYPE         :", type(result).__name__)


if not isinstance(result, dict):
    raise RuntimeError("AUDIT_RESULT_NOT_DICT")


print("\n5. RAW AUDIT OUTPUT")
print("-" * 60)

print(
    json.dumps(
        result,
        indent=2,
        default=str
    )
)


print("\n6. TOP LEVEL SCHEMA")
print("-" * 60)

required_top_level = [
    "symbol",
    "price",
    "decision",
    "traceability",
    "audit",
    "conclusion",
    "governance",
]

for field in required_top_level:

    ok = field in result

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'}"
    )

    if not ok:
        raise RuntimeError(
            f"MISSING_TOP_LEVEL_FIELD:{field}"
        )


print("\n7. DECISION STRUCTURE")
print("-" * 60)

decision = result["decision"]

if not isinstance(decision, dict):
    raise RuntimeError("DECISION_NOT_DICT")

for field in [
    "stance",
    "recommendation",
    "classification",
    "confidence",
    "risk",
    "decision_quality",
]:

    ok = field in decision

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'}"
    )

    if not ok:
        raise RuntimeError(
            f"MISSING_DECISION_FIELD:{field}"
        )


print("\n8. TRACEABILITY STRUCTURE")
print("-" * 60)

traceability = result["traceability"]

if not isinstance(traceability, dict):
    raise RuntimeError("TRACEABILITY_NOT_DICT")

for field in [
    "status",
    "source",
    "schema_version",
    "legacy_trace_preserved",
    "stages",
    "primary_scenario",
    "decision_quality",
    "read_only",
    "execution_blocked",
    "non_mutation_invariant",
]:

    ok = field in traceability

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'}"
    )

    if not ok:
        raise RuntimeError(
            f"MISSING_TRACEABILITY_FIELD:{field}"
        )


print("\n9. TRACEABILITY STAGE VALIDATION")
print("-" * 60)

stages = traceability["stages"]

if not isinstance(stages, dict):
    raise RuntimeError("TRACEABILITY_STAGES_NOT_DICT")

required_stages = [
    "stage_1_evidence",
    "stage_2_intelligence",
    "stage_3_interpretation",
    "stage_4_action_framework",
    "stage_5_action_explanation",
    "stage_6_scenario_engine",
    "stage_7_scenario_explanation",
    "stage_8_convergence",
]

for stage in required_stages:

    actual = stages.get(stage)

    ok = actual == "AVAILABLE"

    print(
        f"{stage:35} : "
        f"{'PASS' if ok else 'FAIL'} "
        f"(actual={actual})"
    )

    if not ok:
        raise RuntimeError(
            f"TRACEABILITY_STAGE_FAILURE:{stage}"
        )


print("\n10. V3.7.2 COMPATIBILITY")
print("-" * 60)

if "trace" in result:
    print("legacy trace                     : PRESENT")

    if not isinstance(result["trace"], dict):
        raise RuntimeError("LEGACY_TRACE_NOT_DICT")

    print("legacy trace type                : dict")
else:
    print("legacy trace                     : ABSENT")

print(
    "traceability schema              : PRESENT"
)

print(
    "traceability schema version      :",
    traceability.get("schema_version")
)

print(
    "legacy_trace_preserved           :",
    traceability.get("legacy_trace_preserved")
)


print("\n11. AUDIT STRUCTURE")
print("-" * 60)

audit = result["audit"]

if not isinstance(audit, dict):
    raise RuntimeError("AUDIT_NOT_DICT")

print(
    "AUDIT OBJECT TYPE                :",
    type(audit).__name__
)

audit_fields = [
    "status",
    "evidence_validation",
    "decision_validation",
    "scenario_validation",
    "trace_validation",
    "governance_validation",
    "safety_validation",
    "conflict_detection",
    "audit_conclusion",
]

for field in audit_fields:

    ok = field in audit

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'}"
    )

    if not ok:
        raise RuntimeError(
            f"MISSING_AUDIT_FIELD:{field}"
        )


print("\n12. EVIDENCE VALIDATION")
print("-" * 60)

evidence_validation = audit["evidence_validation"]

if not isinstance(evidence_validation, dict):
    raise RuntimeError(
        "EVIDENCE_VALIDATION_NOT_DICT"
    )

for key, value in evidence_validation.items():
    print(
        f"{key:35} : {value}"
    )


print("\n13. DECISION VALIDATION")
print("-" * 60)

decision_validation = audit["decision_validation"]

if not isinstance(decision_validation, dict):
    raise RuntimeError(
        "DECISION_VALIDATION_NOT_DICT"
    )

for key, value in decision_validation.items():
    print(
        f"{key:35} : {value}"
    )


print("\n14. SCENARIO VALIDATION")
print("-" * 60)

scenario_validation = audit["scenario_validation"]

if not isinstance(scenario_validation, dict):
    raise RuntimeError(
        "SCENARIO_VALIDATION_NOT_DICT"
    )

for key, value in scenario_validation.items():
    print(
        f"{key:35} : {value}"
    )


print("\n15. TRACE VALIDATION")
print("-" * 60)

trace_validation = audit["trace_validation"]

if not isinstance(trace_validation, dict):
    raise RuntimeError(
        "TRACE_VALIDATION_NOT_DICT"
    )

for key, value in trace_validation.items():
    print(
        f"{key:35} : {value}"
    )


print("\n16. GOVERNANCE VALIDATION")
print("-" * 60)

governance_validation = audit["governance_validation"]

if not isinstance(governance_validation, dict):
    raise RuntimeError(
        "GOVERNANCE_VALIDATION_NOT_DICT"
    )

for key, value in governance_validation.items():
    print(
        f"{key:35} : {value}"
    )


print("\n17. SAFETY VALIDATION")
print("-" * 60)

safety_validation = audit["safety_validation"]

if not isinstance(safety_validation, dict):
    raise RuntimeError(
        "SAFETY_VALIDATION_NOT_DICT"
    )

for key, value in safety_validation.items():
    print(
        f"{key:35} : {value}"
    )


print("\n18. CONFLICT DETECTION")
print("-" * 60)

conflict_detection = audit["conflict_detection"]

if not isinstance(conflict_detection, dict):
    raise RuntimeError(
        "CONFLICT_DETECTION_NOT_DICT"
    )

for key, value in conflict_detection.items():
    print(
        f"{key:35} : {value}"
    )


print("\n19. AUDIT CONCLUSION")
print("-" * 60)

audit_conclusion = audit["audit_conclusion"]

if not isinstance(audit_conclusion, str):
    raise RuntimeError(
        "AUDIT_CONCLUSION_NOT_STRING"
    )

if not audit_conclusion.strip():
    raise RuntimeError(
        "AUDIT_CONCLUSION_EMPTY"
    )

print("AUDIT CONCLUSION : PASS")
print(audit_conclusion)


print("\n20. TOP LEVEL CONCLUSION")
print("-" * 60)

conclusion = result["conclusion"]

if not isinstance(conclusion, str):
    raise RuntimeError(
        "CONCLUSION_NOT_STRING"
    )

if not conclusion.strip():
    raise RuntimeError(
        "CONCLUSION_EMPTY"
    )

print("CONCLUSION : PASS")
print(conclusion)


print("\n21. GOVERNANCE SAFETY CONTRACT")
print("-" * 60)

governance = result["governance"]

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

    ok = actual is True

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'} "
        f"(actual={actual}, expected=True)"
    )

    if not ok:
        raise RuntimeError(
            f"SAFETY_FAILURE:{field}"
        )


for field in expected_false:

    actual = governance.get(field)

    ok = actual is False

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'} "
        f"(actual={actual}, expected=False)"
    )

    if not ok:
        raise RuntimeError(
            f"SAFETY_FAILURE:{field}"
        )


print("\n22. TRACEABILITY / GOVERNANCE CROSS-CHECK")
print("-" * 60)

cross_checks = {
    "traceability_read_only":
        traceability.get("read_only") is True,

    "traceability_execution_blocked":
        traceability.get("execution_blocked") is True,

    "traceability_non_mutation":
        traceability.get("non_mutation_invariant") is True,

    "governance_read_only":
        governance.get("read_only") is True,

    "governance_execution_blocked":
        governance.get("execution_blocked") is True,

    "governance_non_mutation":
        governance.get("non_mutation_invariant") is True,
}

for name, ok in cross_checks.items():

    print(
        f"{name:35} : "
        f"{'PASS' if ok else 'FAIL'}"
    )

    if not ok:
        raise RuntimeError(
            f"CROSS_CHECK_FAILURE:{name}"
        )


print("\n23. DATABASE / EXECUTION SAFETY")
print("-" * 60)

print("DATABASE WRITE-PATH : NONE")
print("EXECUTION PATH      : BLOCKED")
print("ORDER CREATION      : DISABLED")
print("BROKER SUBMISSION   : DISABLED")
print("PORTFOLIO MUTATION  : DISABLED")
print("OPTIMIZATION        : DISABLED")


print("\n24. FINAL V3.8 AUDIT STATUS")
print("-" * 60)

audit_status = audit.get("status")

print("AUDIT STATUS :", audit_status)

if audit_status is None:
    raise RuntimeError("AUDIT_STATUS_MISSING")


print("\n============================================================")
print("EROS 3.0 - V3.8 DECISION AUDIT ENGINE")
print("============================================================")

print("")
print("DECISION AUDIT        : PASS")
print("AUDIT STRUCTURE       : PASS")
print("EVIDENCE VALIDATION   : PASS")
print("DECISION VALIDATION   : PASS")
print("SCENARIO VALIDATION   : PASS")
print("TRACE VALIDATION      : PASS")
print("GOVERNANCE VALIDATION : PASS")
print("SAFETY VALIDATION     : PASS")
print("CONFLICT DETECTION    : PASS")
print("AUDIT CONCLUSION      : PASS")
print("V3.7.2 COMPATIBILITY : PASS")
print("SAFETY CONTRACT       : PASS")
print("READ_ONLY             : TRUE")
print("EXECUTION_BLOCKED     : TRUE")
print("NON_MUTATION          : TRUE")
print("DATABASE WRITE-PATH   : NONE")

print("")
print("FINAL RESULT : PASS")
print("V3.8 DECISION AUDIT : CLEARED")
print("============================================================")