from __future__ import annotations

import json
import sys

from services.eros_frontend_adapter import EROSFrontendAdapter


print("=" * 78)
print("EROS 3.0 - V3.8.2 DECISION AUDIT")
print("SCHEMA HYDRATION RUNTIME DIAGNOSTIC")
print("=" * 78)

print("\nPYTHON")
print("-" * 78)
print(sys.version)


print("\n1. ADAPTER IMPORT")
print("-" * 78)

adapter = EROSFrontendAdapter()

print("IMPORT : PASS")
print("CLASS  :", adapter.__class__.__name__)


print("\n2. FOUNDATION API")
print("-" * 78)

required = [
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

    print(
        f"{name:35} : "
        f"{'PASS' if ok else 'FAIL'}"
    )

    if not ok:
        raise RuntimeError(
            f"MISSING_API:{name}"
        )


print("\n3. EXECUTION TARGET")
print("-" * 78)

symbol = "RELIANCE.NS"

print("SYMBOL :", symbol)


print("\n4. DIRECT CONVERGENCE BASELINE")
print("-" * 78)

convergence = adapter.decision_convergence(symbol)

if not isinstance(convergence, dict):
    raise RuntimeError(
        "CONVERGENCE_NOT_DICT"
    )

print("CONVERGENCE : PASS")

baseline_decision = convergence.get(
    "decision",
    {}
)

baseline_convergence = convergence.get(
    "convergence",
    {}
)

baseline_interpretation = convergence.get(
    "interpretation",
    {}
)

print(
    "BASELINE STANCE          :",
    baseline_decision.get("stance")
)

print(
    "BASELINE RECOMMENDATION  :",
    baseline_decision.get("recommendation")
)

print(
    "BASELINE CLASSIFICATION  :",
    baseline_decision.get("classification")
)

print(
    "BASELINE CONFIDENCE      :",
    baseline_decision.get("confidence")
)

print(
    "BASELINE RISK            :",
    baseline_decision.get("risk")
)

print(
    "BASELINE DECISION QUALITY:",
    baseline_decision.get("decision_quality")
)


print("\n5. TRACEABILITY BASELINE")
print("-" * 78)

trace_result = adapter.decision_traceability(symbol)

if not isinstance(trace_result, dict):
    raise RuntimeError(
        "TRACEABILITY_NOT_DICT"
    )

print("TRACEABILITY : PASS")

print(
    "TRACEABILITY STATUS :",
    trace_result.get(
        "traceability_status"
    )
)

print(
    "TRACEABILITY SCHEMA :",
    trace_result.get(
        "traceability",
        {}
    ).get(
        "schema_version"
    )
)

print(
    "PRIMARY SCENARIO :",
    trace_result.get(
        "scenario_trace",
        {}
    ).get(
        "primary_scenario"
    )
)


print("\n6. EXECUTING V3.8.2 AUDIT")
print("-" * 78)

result = adapter.decision_audit(symbol)

if not isinstance(result, dict):
    raise RuntimeError(
        "AUDIT_RESULT_NOT_DICT"
    )

print("AUDIT CALL : PASS")
print("RESULT TYPE:", type(result).__name__)


print("\n7. TOP LEVEL SCHEMA")
print("-" * 78)

required_top = [
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

for field in required_top:

    ok = field in result

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'}"
    )

    if not ok:
        raise RuntimeError(
            f"MISSING_TOP_LEVEL_FIELD:{field}"
        )


print("\n8. DECISION CONTRACT")
print("-" * 78)

decision = result["decision"]

decision_fields = [
    "stance",
    "recommendation",
    "classification",
    "confidence",
    "risk",
    "decision_quality",
]

for field in decision_fields:

    value = decision.get(field)

    ok = value is not None and value != ""

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'} "
        f"(value={value})"
    )

    if not ok:
        raise RuntimeError(
            f"DECISION_FIELD_NOT_HYDRATED:{field}"
        )


print("\n9. EVIDENCE CHAIN")
print("-" * 78)

evidence = result["evidence_chain"]

evidence_fields = [
    "primary_drivers",
    "supporting_drivers",
    "conflicting_signals",
    "confirmation_logic",
    "invalidation_logic",
]

for field in evidence_fields:

    value = evidence.get(field)

    ok = isinstance(value, list)

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'} "
        f"(count={len(value) if isinstance(value, list) else 'N/A'})"
    )

    if not ok:
        raise RuntimeError(
            f"EVIDENCE_FIELD_INVALID:{field}"
        )


print("\n10. SCENARIO TRACE")
print("-" * 78)

scenario = result["scenario_trace"]

scenario_fields = [
    "primary_scenario",
    "base",
    "bull_confirmation",
    "bear_invalidation",
]

for field in scenario_fields:

    value = scenario.get(field)

    ok = (
        value is not None
        and value != {}
        and value != ""
    )

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'}"
    )

    if not ok:
        raise RuntimeError(
            f"SCENARIO_FIELD_NOT_HYDRATED:{field}"
        )


print("\n11. INTERPRETATION")
print("-" * 78)

interpretation = result["interpretation"]

interpretation_fields = [
    "market_condition",
    "price_context",
    "breakout_context",
    "decision_quality",
]

for field in interpretation_fields:

    value = interpretation.get(field)

    ok = value is not None and value != ""

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'} "
        f"(value={value})"
    )

    if not ok:
        raise RuntimeError(
            f"INTERPRETATION_FIELD_NOT_HYDRATED:{field}"
        )


print("\n12. TRACEABILITY")
print("-" * 78)

traceability = result["traceability"]

print(
    "status                :",
    traceability.get("status")
)

print(
    "source                :",
    traceability.get("source")
)

print(
    "schema_version        :",
    traceability.get("schema_version")
)

print(
    "legacy_trace_preserved:",
    traceability.get(
        "legacy_trace_preserved"
    )
)

print(
    "primary_scenario      :",
    traceability.get(
        "primary_scenario"
    )
)

print(
    "decision_quality      :",
    traceability.get(
        "decision_quality"
    )
)

if not traceability.get("status"):
    raise RuntimeError(
        "TRACEABILITY_STATUS_MISSING"
    )


print("\n13. AUDIT")
print("-" * 78)

audit = result["audit"]

print(
    json.dumps(
        audit,
        indent=2,
        default=str
    )
)

if audit.get("overall_status") != "PASS":
    raise RuntimeError(
        "AUDIT_STATUS_NOT_PASS"
    )


print("\n14. CONCLUSION")
print("-" * 78)

conclusion = result["conclusion"]

print(conclusion)

if not isinstance(conclusion, str):
    raise RuntimeError(
        "CONCLUSION_NOT_STRING"
    )

if not conclusion.strip():
    raise RuntimeError(
        "CONCLUSION_EMPTY"
    )

if "UNKNOWN stance" in conclusion:
    raise RuntimeError(
        "CONCLUSION_STILL_UNKNOWN"
    )

if "UNSPECIFIED recommendation" in conclusion:
    raise RuntimeError(
        "CONCLUSION_STILL_UNSPECIFIED"
    )


print("\n15. GOVERNANCE")
print("-" * 78)

governance = result["governance"]

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
        f"(actual={actual})"
    )

    if not ok:
        raise RuntimeError(
            f"GOVERNANCE_FAILURE:{field}"
        )


for field in expected_false:

    actual = governance.get(field)

    ok = actual is False

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'} "
        f"(actual={actual})"
    )

    if not ok:
        raise RuntimeError(
            f"GOVERNANCE_FAILURE:{field}"
        )


print("\n16. DATABASE / EXECUTION SAFETY")
print("-" * 78)

print("DATABASE WRITE-PATH : NONE")
print("BROKER EXECUTION    : BLOCKED")
print("ORDER CREATION      : BLOCKED")
print("PORTFOLIO MUTATION  : BLOCKED")


print("\n17. COMPLETE RESULT")
print("-" * 78)

print(
    json.dumps(
        result,
        indent=2,
        default=str
    )
)


print("\n======================================================================")
print("V3.8.2 DECISION AUDIT SCHEMA HYDRATION")
print("======================================================================")

print("ADAPTER IMPORT       : PASS")
print("FOUNDATION API       : PASS")
print("CONVERGENCE BASELINE : PASS")
print("TRACEABILITY BASELINE: PASS")
print("AUDIT EXECUTION      : PASS")
print("DECISION CONTRACT    : PASS")
print("EVIDENCE CHAIN       : PASS")
print("SCENARIO TRACE       : PASS")
print("INTERPRETATION       : PASS")
print("TRACEABILITY         : PASS")
print("AUDIT                : PASS")
print("CONCLUSION           : PASS")
print("GOVERNANCE           : PASS")
print("DATABASE WRITE       : NONE")
print("EXECUTION            : BLOCKED")
print("")
print("FINAL RESULT : PASS")
print("V3.8.2 DECISION AUDIT SCHEMA : CLEARED")
print("======================================================================")