import json
import sys
from pprint import pprint

from services.eros_frontend_adapter import EROSFrontendAdapter

print("=" * 70)
print("EROS 3.0 - V3.8.2 DECISION AUDIT INTEGRITY RUNTIME")
print("=" * 70)


print("\nPYTHON VERSION")
print("-" * 70)
print(sys.version)


adapter = EROSFrontendAdapter()


print("\n1. ADAPTER IMPORT")
print("-" * 70)
print("IMPORT : PASS")
print("CLASS  :", adapter.__class__.__name__)


print("\n2. FOUNDATION API CHECK")
print("-" * 70)

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


print("\nFOUNDATION : VERIFIED")


symbol = "RELIANCE.NS"


print("\n3. TRACEABILITY BASELINE")
print("-" * 70)

trace = adapter.decision_traceability(symbol)

if not isinstance(trace, dict):
    raise RuntimeError("TRACEABILITY_NOT_DICT")

print("TRACEABILITY CALL : PASS")
print("TRACEABILITY TYPE : dict")


print("\nTRACEABILITY DECISION")
print("-" * 70)
pprint(trace.get("decision"))


print("\nTRACEABILITY EVIDENCE CHAIN")
print("-" * 70)
pprint(trace.get("evidence_chain"))


print("\nTRACEABILITY SCENARIO TRACE")
print("-" * 70)
pprint(trace.get("scenario_trace"))


print("\nTRACEABILITY INTERPRETATION")
print("-" * 70)
pprint(trace.get("interpretation"))


print("\nTRACEABILITY CONTRACT")
print("-" * 70)
pprint(trace.get("traceability"))


print("\n4. DECISION AUDIT")
print("-" * 70)

audit_result = adapter.decision_audit(symbol)

if not isinstance(audit_result, dict):
    raise RuntimeError("AUDIT_RESULT_NOT_DICT")

print("DECISION AUDIT CALL : PASS")
print("RESULT TYPE         : dict")


print("\n5. AUDIT RESULT TOP LEVEL")
print("-" * 70)

for key, value in audit_result.items():
    print(f"{key:35} : " f"{type(value).__name__}")


print("\n6. AUDIT STATUS")
print("-" * 70)

print("audit_status    :", audit_result.get("audit_status"))
print("audit_summary   :", audit_result.get("audit_summary"))
print("traceability_status :", audit_result.get("traceability_status"))


print("\n7. DECISION INTEGRITY")
print("-" * 70)

audit_decision = audit_result.get("decision")

print("AUDIT DECISION :")
pprint(audit_decision)


if not isinstance(audit_decision, dict):
    raise RuntimeError("AUDIT_DECISION_NOT_DICT")

decision_fields = [
    "stance",
    "recommendation",
    "classification",
    "confidence",
    "risk",
    "decision_quality",
]

for field in decision_fields:
    value = audit_decision.get(field)

    print(f"{field:35} : " f"{value!r}")


print("\n8. DECISION INTEGRITY CHECK")
print("-" * 70)

source_decision = trace.get("decision")

if not isinstance(source_decision, dict):
    raise RuntimeError("SOURCE_DECISION_NOT_DICT")

for field in decision_fields:

    source_value = source_decision.get(field)
    audit_value = audit_decision.get(field)

    ok = source_value == audit_value

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'} "
        f"(source={source_value!r}, audit={audit_value!r})"
    )

    if not ok:
        raise RuntimeError(f"DECISION_FIELD_LOST:{field}")


print("\nDECISION INTEGRITY : PASS")


print("\n9. EVIDENCE CHAIN INTEGRITY")
print("-" * 70)

source_evidence = trace.get("evidence_chain")
audit_evidence = audit_result.get("evidence_chain")

if not isinstance(source_evidence, dict):
    raise RuntimeError("SOURCE_EVIDENCE_NOT_DICT")

if not isinstance(audit_evidence, dict):
    raise RuntimeError("AUDIT_EVIDENCE_NOT_DICT")

print("SOURCE EVIDENCE KEYS :")
for key in source_evidence.keys():
    print(" -", key)

print("\nAUDIT EVIDENCE KEYS :")
for key in audit_evidence.keys():
    print(" -", key)

if source_evidence != audit_evidence:
    raise RuntimeError("EVIDENCE_CHAIN_LOST_OR_CHANGED")

print("\nEVIDENCE CHAIN : PASS")


print("\n10. SCENARIO TRACE INTEGRITY")
print("-" * 70)

source_scenario = trace.get("scenario_trace")
audit_scenario = audit_result.get("scenario_trace")

if not isinstance(source_scenario, dict):
    raise RuntimeError("SOURCE_SCENARIO_NOT_DICT")

if not isinstance(audit_scenario, dict):
    raise RuntimeError("AUDIT_SCENARIO_NOT_DICT")

print("SOURCE SCENARIO KEYS :")
for key in source_scenario.keys():
    print(" -", key)

print("\nAUDIT SCENARIO KEYS :")
for key in audit_scenario.keys():
    print(" -", key)

if source_scenario != audit_scenario:
    raise RuntimeError("SCENARIO_TRACE_LOST_OR_CHANGED")

print("\nSCENARIO TRACE : PASS")


print("\n11. INTERPRETATION INTEGRITY")
print("-" * 70)

source_interpretation = trace.get("interpretation")
audit_interpretation = audit_result.get("interpretation")

if not isinstance(source_interpretation, dict):
    raise RuntimeError("SOURCE_INTERPRETATION_NOT_DICT")

if not isinstance(audit_interpretation, dict):
    raise RuntimeError("AUDIT_INTERPRETATION_NOT_DICT")

if source_interpretation != audit_interpretation:
    raise RuntimeError("INTERPRETATION_LOST_OR_CHANGED")

print("INTERPRETATION : PASS")


print("\n12. TRACEABILITY INTEGRITY")
print("-" * 70)

source_traceability = trace.get("traceability")
audit_traceability = audit_result.get("traceability")

if not isinstance(source_traceability, dict):
    raise RuntimeError("SOURCE_TRACEABILITY_NOT_DICT")

if not isinstance(audit_traceability, dict):
    raise RuntimeError("AUDIT_TRACEABILITY_NOT_DICT")

critical_trace_fields = [
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
]

for field in critical_trace_fields:

    source_value = source_traceability.get(field)
    audit_value = audit_traceability.get(field)

    ok = source_value == audit_value

    print(f"{field:35} : " f"{'PASS' if ok else 'FAIL'}")

    if not ok:
        raise RuntimeError(f"TRACEABILITY_FIELD_LOST:{field}")


print("\nTRACEABILITY INTEGRITY : PASS")


print("\n13. LEGACY TRACE")
print("-" * 70)

legacy_trace = audit_result.get("trace")

if not isinstance(legacy_trace, dict):
    raise RuntimeError("LEGACY_TRACE_NOT_DICT")

print("LEGACY TRACE : PASS")
pprint(legacy_trace)


print("\n14. CONCLUSION INTEGRITY")
print("-" * 70)

source_conclusion = trace.get("conclusion")
audit_conclusion = audit_result.get("conclusion")

print("SOURCE CONCLUSION :")
print(source_conclusion)

print("\nAUDIT CONCLUSION :")
print(audit_conclusion)

if not isinstance(audit_conclusion, str):
    raise RuntimeError("AUDIT_CONCLUSION_NOT_STRING")

if not audit_conclusion.strip():
    raise RuntimeError("AUDIT_CONCLUSION_EMPTY")

print("\nCONCLUSION : PASS")


print("\n15. AUDIT OBJECT")
print("-" * 70)

audit = audit_result.get("audit")

if not isinstance(audit, dict):
    raise RuntimeError("AUDIT_OBJECT_NOT_DICT")

print(json.dumps(audit, indent=2, default=str))


print("\n16. AUDIT FINDINGS")
print("-" * 70)

findings = audit_result.get("audit_findings")

if not isinstance(findings, list):
    raise RuntimeError("AUDIT_FINDINGS_NOT_LIST")

print("FINDINGS COUNT :", len(findings))

for finding in findings:
    print(" -", finding)


print("\n17. GOVERNANCE")
print("-" * 70)

governance = audit_result.get("governance")

if not isinstance(governance, dict):
    raise RuntimeError("GOVERNANCE_NOT_DICT")

print(json.dumps(governance, indent=2, default=str))


print("\n18. SAFETY CONTRACT")
print("-" * 70)

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

    print(f"{field:35} : " f"{'PASS' if ok else 'FAIL'} " f"(actual={actual!r})")

    if not ok:
        raise RuntimeError(f"SAFETY_FAILURE:{field}")


for field in expected_false:

    actual = governance.get(field)

    ok = actual is False

    print(f"{field:35} : " f"{'PASS' if ok else 'FAIL'} " f"(actual={actual!r})")

    if not ok:
        raise RuntimeError(f"SAFETY_FAILURE:{field}")


print("\nSAFETY CONTRACT : PASS")


print("\n19. DATABASE / EXECUTION SAFETY")
print("-" * 70)

print("DATABASE WRITE-PATH : NONE")
print("EXECUTION PATH      : BLOCKED")


print("\n20. FINAL INTEGRITY STATUS")
print("-" * 70)

print("FOUNDATION API        : PASS")
print("TRACEABILITY API      : PASS")
print("DECISION AUDIT API    : PASS")
print("DECISION INTEGRITY    : PASS")
print("EVIDENCE CHAIN        : PASS")
print("SCENARIO TRACE        : PASS")
print("INTERPRETATION        : PASS")
print("TRACEABILITY CONTRACT : PASS")
print("LEGACY TRACE          : PASS")
print("CONCLUSION            : PASS")
print("AUDIT OBJECT          : PASS")
print("AUDIT FINDINGS        : PASS")
print("SAFETY CONTRACT       : PASS")
print("DATABASE WRITE-PATH   : NONE")
print("EXECUTION PATH        : BLOCKED")


print("")
print("=" * 70)
print("V3.8.2 DECISION AUDIT INTEGRITY RUNTIME : PASS")
print("=" * 70)
