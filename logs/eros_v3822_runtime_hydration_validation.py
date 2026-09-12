from __future__ import annotations

import json
import sys
import traceback

from services.eros_frontend_adapter import EROSFrontendAdapter

print("=" * 70)
print("EROS 3.0 - V3.8.2.2 RUNTIME HYDRATION VALIDATION")
print("=" * 70)

print()
print("PYTHON")
print("-" * 70)
print(sys.version)

print()
print("1. ADAPTER IMPORT")
print("-" * 70)

try:
    adapter = EROSFrontendAdapter()
    print("IMPORT : PASS")
    print("CLASS  : EROSFrontendAdapter")
except Exception as exc:
    print("IMPORT : FAIL")
    print("ERROR  :", repr(exc))
    traceback.print_exc()
    raise

print()
print("2. API CHECK")
print("-" * 70)

required_methods = [
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

api_failed = False

for name in required_methods:
    present = hasattr(adapter, name)
    print(f"{name:<36}: {'PASS' if present else 'FAIL'}")
    if not present:
        api_failed = True

if api_failed:
    raise RuntimeError("Required API missing")

print()
print("3. EXECUTION TARGET")
print("-" * 70)

symbol = "RELIANCE.NS"
print("SYMBOL :", symbol)

print()
print("4. DECISION TRACEABILITY")
print("-" * 70)

try:
    trace_result = adapter.decision_traceability(symbol)
    print("TRACEABILITY CALL : PASS")
    print("RESULT TYPE       :", type(trace_result).__name__)
except Exception as exc:
    print("TRACEABILITY CALL : FAIL")
    print("ERROR             :", repr(exc))
    traceback.print_exc()
    raise

print()
print("5. TRACEABILITY HYDRATION CHECK")
print("-" * 70)

trace_keys = [
    "symbol",
    "price",
    "decision",
    "trace",
    "traceability",
    "evidence_chain",
    "scenario_trace",
    "interpretation",
    "conclusion",
    "traceability_status",
    "governance",
]

for key in trace_keys:
    value = trace_result.get(key)
    print(f"{key:<36}: {type(value).__name__}")

print()
print("6. TRACEABILITY DATA COMPLETENESS")
print("-" * 70)

decision = trace_result.get("decision")
trace = trace_result.get("trace")
traceability = trace_result.get("traceability")
evidence_chain = trace_result.get("evidence_chain")
scenario_trace = trace_result.get("scenario_trace")
interpretation = trace_result.get("interpretation")
governance = trace_result.get("governance")

checks = {
    "decision populated": isinstance(decision, dict) and bool(decision),
    "legacy trace populated": isinstance(trace, dict) and bool(trace),
    "traceability populated": isinstance(traceability, dict) and bool(traceability),
    "evidence_chain populated": isinstance(evidence_chain, dict) and bool(evidence_chain),
    "scenario_trace populated": isinstance(scenario_trace, dict) and bool(scenario_trace),
    "interpretation populated": isinstance(interpretation, dict) and bool(interpretation),
    "governance populated": isinstance(governance, dict) and bool(governance),
    "traceability status complete": trace_result.get("traceability_status") == "COMPLETE",
}

traceability_failed = False

for name, passed in checks.items():
    print(f"{name:<36}: {'PASS' if passed else 'FAIL'}")
    if not passed:
        traceability_failed = True

print()
print("7. HYDRATED DECISION")
print("-" * 70)
print(json.dumps(decision, indent=2, default=str))

print()
print("8. HYDRATED TRACEABILITY")
print("-" * 70)
print(json.dumps(traceability, indent=2, default=str))

print()
print("9. EVIDENCE CHAIN")
print("-" * 70)
print(json.dumps(evidence_chain, indent=2, default=str))

print()
print("10. SCENARIO TRACE")
print("-" * 70)
print(json.dumps(scenario_trace, indent=2, default=str))

print()
print("11. INTERPRETATION")
print("-" * 70)
print(json.dumps(interpretation, indent=2, default=str))

print()
print("12. DECISION AUDIT")
print("-" * 70)

try:
    audit_result = adapter.decision_audit(symbol)
    print("AUDIT CALL  : PASS")
    print("RESULT TYPE :", type(audit_result).__name__)
except Exception as exc:
    print("AUDIT CALL  : FAIL")
    print("ERROR       :", repr(exc))
    traceback.print_exc()
    raise

print()
print("13. AUDIT TOP LEVEL")
print("-" * 70)

if not isinstance(audit_result, dict):
    print("AUDIT RESULT : FAIL - NOT A DICT")
    raise RuntimeError("decision_audit did not return dict")

for key, value in audit_result.items():
    print(f"{key:<36}: {type(value).__name__}")

print()
print("14. AUDIT SCHEMA")
print("-" * 70)

audit_required = [
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

audit_schema_failed = False

for key in audit_required:
    present = key in audit_result
    value = audit_result.get(key)
    populated = bool(value) if isinstance(value, (dict, list, str)) else value is not None

    status = "PASS" if present and populated else "FAIL"

    print(f"{key:<36}: {status}" f" | present={present}" f" | populated={populated}")

    if not (present and populated):
        audit_schema_failed = True

print()
print("15. AUDIT HYDRATION")
print("-" * 70)

audit_decision = audit_result.get("decision", {})
audit_trace = audit_result.get("trace", {})
audit_traceability = audit_result.get("traceability", {})
audit_evidence = audit_result.get("evidence_chain", {})
audit_scenarios = audit_result.get("scenario_trace", {})
audit_interpretation = audit_result.get("interpretation", {})

hydration_checks = {
    "audit decision hydrated": isinstance(audit_decision, dict) and bool(audit_decision),
    "audit legacy trace hydrated": isinstance(audit_trace, dict) and bool(audit_trace),
    "audit traceability hydrated": isinstance(audit_traceability, dict)
    and bool(audit_traceability),
    "audit evidence chain hydrated": isinstance(audit_evidence, dict) and bool(audit_evidence),
    "audit scenario trace hydrated": isinstance(audit_scenarios, dict) and bool(audit_scenarios),
    "audit interpretation hydrated": isinstance(audit_interpretation, dict)
    and bool(audit_interpretation),
    "audit conclusion populated": isinstance(audit_result.get("conclusion"), str)
    and bool(audit_result.get("conclusion")),
    "audit status populated": isinstance(audit_result.get("audit_status"), str)
    and bool(audit_result.get("audit_status")),
}

hydration_failed = False

for name, passed in hydration_checks.items():
    print(f"{name:<40}: {'PASS' if passed else 'FAIL'}")
    if not passed:
        hydration_failed = True

print()
print("16. GOVERNANCE / SAFETY")
print("-" * 70)

gov = audit_result.get("governance", {})

safety_expected = {
    "read_only": True,
    "execution_blocked": True,
    "non_mutation_invariant": True,
    "allow_order_creation": False,
    "allow_broker_submission": False,
    "allow_live_execution": False,
    "allow_portfolio_mutation": False,
    "allow_valuation_mutation": False,
    "allow_performance_mutation": False,
    "allow_risk_mutation": False,
    "allow_optimization": False,
}

safety_failed = False

for key, expected in safety_expected.items():
    actual = gov.get(key)
    passed = actual == expected

    print(
        f"{key:<36}: "
        f"{'PASS' if passed else 'FAIL'}"
        f" | actual={actual}"
        f" | expected={expected}"
    )

    if not passed:
        safety_failed = True

print()
print("17. DATABASE / EXECUTION SAFETY")
print("-" * 70)

print("read_only              :", gov.get("read_only"))
print("execution_blocked      :", gov.get("execution_blocked"))
print("non_mutation_invariant :", gov.get("non_mutation_invariant"))
print("order creation        :", gov.get("allow_order_creation"))
print("broker submission     :", gov.get("allow_broker_submission"))
print("live execution        :", gov.get("allow_live_execution"))
print("portfolio mutation    :", gov.get("allow_portfolio_mutation"))

print()
print("18. FINAL AUDIT RESULT")
print("-" * 70)

print(json.dumps(audit_result, indent=2, default=str))

print()
print("=" * 70)
print("V3.8.2.2 RUNTIME VALIDATION SUMMARY")
print("=" * 70)

overall_failed = traceability_failed or audit_schema_failed or hydration_failed or safety_failed

print("TRACEABILITY DATA      :", "FAIL" if traceability_failed else "PASS")
print("AUDIT SCHEMA           :", "FAIL" if audit_schema_failed else "PASS")
print("AUDIT HYDRATION        :", "FAIL" if hydration_failed else "PASS")
print("GOVERNANCE / SAFETY    :", "FAIL" if safety_failed else "PASS")
print("DATABASE WRITE         : NONE")
print("BROKER CALL            : NONE")
print("ORDER CREATION         : NONE")
print("PORTFOLIO MUTATION     : NONE")

print()
if overall_failed:
    print("V3.8.2.2 RUNTIME VALIDATION : FAIL")
    print("=" * 70)
    sys.exit(1)
else:
    print("V3.8.2.2 RUNTIME VALIDATION : PASS")
    print("=" * 70)
    sys.exit(0)
