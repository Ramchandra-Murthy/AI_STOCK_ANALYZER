from __future__ import annotations

import json
import sys
import traceback

print("=" * 70)
print("EROS 3.0 - V3.8.2.2 CLEAN TRACE COMPATIBILITY RUNTIME DIAGNOSTIC")
print("=" * 70)

print()
print("PYTHON")
print("-" * 70)
print(sys.version)

print()
print("1. ADAPTER IMPORT")
print("-" * 70)

try:
    from services.eros_frontend_adapter import EROSFrontendAdapter

    print("IMPORT : PASS")
    print("CLASS  : EROSFrontendAdapter")
except Exception as exc:
    print("IMPORT : FAIL")
    print(type(exc).__name__, ":", exc)
    traceback.print_exc()
    raise SystemExit(10)

adapter = EROSFrontendAdapter()

print()
print("2. FOUNDATION API CHECK")
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
    ok = callable(getattr(adapter, name, None))
    print(f"{name:<35} : {'PASS' if ok else 'FAIL'}")
    if not ok:
        api_failed = True

if api_failed:
    raise SystemExit(11)

print()
print("3. EXECUTION TARGET")
print("-" * 70)

symbol = "RELIANCE.NS"
print("SYMBOL :", symbol)

print()
print("4. TRACEABILITY RUNTIME")
print("-" * 70)

try:
    trace_result = adapter.decision_traceability(symbol)

    print("CALL       : PASS")
    print("RESULT     :", type(trace_result).__name__)

    if not isinstance(trace_result, dict):
        print("RESULT DICT : FAIL")
        raise SystemExit(12)

    print("RESULT DICT : PASS")

except Exception as exc:
    print("TRACEABILITY CALL : FAIL")
    print(type(exc).__name__, ":", exc)
    traceback.print_exc()
    raise SystemExit(13)

print()
print("5. AUDIT RUNTIME")
print("-" * 70)

try:
    audit_result = adapter.decision_audit(symbol)

    print("CALL       : PASS")
    print("RESULT     :", type(audit_result).__name__)

    if not isinstance(audit_result, dict):
        print("RESULT DICT : FAIL")
        raise SystemExit(14)

    print("RESULT DICT : PASS")

except Exception as exc:
    print("AUDIT CALL : FAIL")
    print(type(exc).__name__, ":", exc)
    traceback.print_exc()
    raise SystemExit(15)

print()
print("6. TRACEABILITY TOP LEVEL")
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
    print(f"{key:<35} : {type(value).__name__}")

print()
print("7. AUDIT TOP LEVEL")
print("-" * 70)

audit_keys = [
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

for key in audit_keys:
    value = audit_result.get(key)
    print(f"{key:<35} : {type(value).__name__}")

print()
print("8. CRITICAL HYDRATION CHECK")
print("-" * 70)

critical = {
    "decision": audit_result.get("decision"),
    "audit": audit_result.get("audit"),
    "audit_findings": audit_result.get("audit_findings"),
    "trace": audit_result.get("trace"),
    "traceability": audit_result.get("traceability"),
    "evidence_chain": audit_result.get("evidence_chain"),
    "scenario_trace": audit_result.get("scenario_trace"),
    "interpretation": audit_result.get("interpretation"),
    "conclusion": audit_result.get("conclusion"),
    "traceability_status": audit_result.get("traceability_status"),
    "audit_summary": audit_result.get("audit_summary"),
    "audit_status": audit_result.get("audit_status"),
}

for key, value in critical.items():
    if isinstance(value, dict):
        state = "HYDRATED" if len(value) > 0 else "EMPTY"
    elif isinstance(value, list):
        state = "HYDRATED" if len(value) > 0 else "EMPTY"
    elif isinstance(value, str):
        state = "HYDRATED" if value.strip() else "EMPTY"
    elif value is None:
        state = "EMPTY"
    else:
        state = "HYDRATED"

    print(f"{key:<35} : {state}")

print()
print("9. DECISION CONTENT")
print("-" * 70)

decision = audit_result.get("decision", {})

if isinstance(decision, dict):
    for key in [
        "stance",
        "recommendation",
        "classification",
        "confidence",
        "risk",
        "decision_quality",
    ]:
        print(f"{key:<35} : {decision.get(key)}")
else:
    print("DECISION IS NOT A DICT")

print()
print("10. TRACEABILITY CONTENT")
print("-" * 70)

traceability = audit_result.get("traceability", {})

if isinstance(traceability, dict):
    print("status                :", traceability.get("status"))
    print("source                :", traceability.get("source"))
    print("schema_version        :", traceability.get("schema_version"))
    print("legacy_trace_preserved:", traceability.get("legacy_trace_preserved"))
    print("primary_scenario      :", traceability.get("primary_scenario"))
    print("decision_quality      :", traceability.get("decision_quality"))

    stages = traceability.get("stages", {})

    if isinstance(stages, dict):
        print()
        print("TRACEABILITY STAGES")
        for key, value in stages.items():
            print(f"{key:<35} : {value}")
else:
    print("TRACEABILITY IS NOT A DICT")

print()
print("11. SCENARIO TRACE")
print("-" * 70)

scenario_trace = audit_result.get("scenario_trace", {})

if isinstance(scenario_trace, dict):
    print(json.dumps(scenario_trace, indent=2, default=str))
else:
    print("SCENARIO TRACE IS NOT A DICT")

print()
print("12. EVIDENCE CHAIN")
print("-" * 70)

evidence_chain = audit_result.get("evidence_chain", {})

if isinstance(evidence_chain, dict):
    print(json.dumps(evidence_chain, indent=2, default=str))
else:
    print("EVIDENCE CHAIN IS NOT A DICT")

print()
print("13. AUDIT RESULT")
print("-" * 70)

print("audit_status  :", audit_result.get("audit_status"))
print("audit_summary :", audit_result.get("audit_summary"))

audit_findings = audit_result.get("audit_findings")

if isinstance(audit_findings, list):
    print("audit_findings count :", len(audit_findings))
    for index, finding in enumerate(audit_findings, 1):
        print()
        print(f"FINDING {index}")
        print(json.dumps(finding, indent=2, default=str))
else:
    print("audit_findings is not a list")

print()
print("14. GOVERNANCE / SAFETY")
print("-" * 70)

governance = audit_result.get("governance", {})

if isinstance(governance, dict):
    print(json.dumps(governance, indent=2, default=str))
else:
    print("GOVERNANCE IS NOT A DICT")

print()
print("15. NON-MUTATION ASSERTIONS")
print("-" * 70)

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

print("read_only :", governance.get("read_only"))
print("execution_blocked :", governance.get("execution_blocked"))
print("non_mutation_invariant :", governance.get("non_mutation_invariant"))

if governance.get("read_only") is not True:
    safety_ok = False

if governance.get("execution_blocked") is not True:
    safety_ok = False

if governance.get("non_mutation_invariant") is not True:
    safety_ok = False

for key in expected_false:
    value = governance.get(key)
    print(f"{key:<35} : {value}")
    if value is not False:
        safety_ok = False

print()
print("SAFETY CONTRACT :", "PASS" if safety_ok else "FAIL")

print()
print("16. FULL AUDIT RESULT")
print("-" * 70)

print(json.dumps(audit_result, indent=2, default=str))

print()
print("=" * 70)
print("V3.8.2.2 CLEAN TRACE COMPATIBILITY RUNTIME COMPLETE")
print("=" * 70)

print()
print("FINAL STATUS")
print("-" * 70)

hydration_keys = [
    "decision",
    "audit",
    "trace",
    "traceability",
    "evidence_chain",
    "scenario_trace",
    "interpretation",
]

hydration_ok = True

for key in hydration_keys:
    value = audit_result.get(key)

    if isinstance(value, dict):
        ok = len(value) > 0
    elif isinstance(value, list):
        ok = len(value) > 0
    else:
        ok = value is not None and value != ""

    print(f"{key:<35} : {'HYDRATED' if ok else 'EMPTY'}")

    if not ok:
        hydration_ok = False

print()
print("HYDRATION :", "PASS" if hydration_ok else "FAIL")
print("SAFETY    :", "PASS" if safety_ok else "FAIL")

if hydration_ok and safety_ok:
    print()
    print("V3.8.2.2 RUNTIME : PASS")
    print("NEXT STAGE        : V3.9 READY")
    exit_code = 0
else:
    print()
    print("V3.8.2.2 RUNTIME : FAIL")
    print("NEXT STAGE        : DO NOT PATCH")
    exit_code = 20

raise SystemExit(exit_code)
