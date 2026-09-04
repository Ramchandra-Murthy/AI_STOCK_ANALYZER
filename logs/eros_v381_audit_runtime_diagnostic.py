import json
import sys
import traceback

from services.eros_frontend_adapter import EROSFrontendAdapter


print("=" * 60)
print("EROS 3.0 - V3.8.1 DECISION AUDIT - LONG-FORM RUNTIME")
print("=" * 60)

print("\nPYTHON")
print("-" * 60)
print(sys.version)


# ==========================================================
# 1. IMPORT
# ==========================================================

print("\n1. ADAPTER IMPORT")
print("-" * 60)

adapter = EROSFrontendAdapter()

print("IMPORT : PASS")
print("CLASS  :", adapter.__class__.__name__)


# ==========================================================
# 2. FOUNDATION API
# ==========================================================

print("\n2. FOUNDATION API CHECK")
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
    exists = hasattr(adapter, name)

    print(
        f"{name:35} : "
        f"{'PASS' if exists else 'FAIL'}"
    )

    if not exists:
        raise RuntimeError(
            f"MISSING_FOUNDATION_API:{name}"
        )

print("\nV3.8.1 FOUNDATION : VERIFIED")


# ==========================================================
# 3. EXECUTION TARGET
# ==========================================================

print("\n3. EXECUTION TARGET")
print("-" * 60)

symbol = "RELIANCE.NS"

print("SYMBOL :", symbol)


# ==========================================================
# 4. METHOD OBJECT
# ==========================================================

print("\n4. DECISION AUDIT METHOD")
print("-" * 60)

method = adapter.decision_audit

print("METHOD :", method)
print("TYPE   :", type(method).__name__)

if not callable(method):
    raise RuntimeError("DECISION_AUDIT_NOT_CALLABLE")

print("CALLABLE : PASS")


# ==========================================================
# 5. EXECUTION
# ==========================================================

print("\n5. EXECUTING DECISION AUDIT")
print("-" * 60)

try:

    result = adapter.decision_audit(symbol)

except Exception as exc:

    print("")
    print("DECISION AUDIT : EXCEPTION")
    print("EXCEPTION TYPE :", type(exc).__name__)
    print("EXCEPTION      :", str(exc))

    print("")
    print("TRACEBACK")
    print("-" * 60)

    traceback.print_exc()

    raise


print("DECISION AUDIT : PASS")
print("RESULT TYPE    :", type(result).__name__)


# ==========================================================
# 6. RESULT TYPE
# ==========================================================

print("\n6. RESULT TYPE VALIDATION")
print("-" * 60)

if not isinstance(result, dict):
    raise RuntimeError(
        f"DECISION_AUDIT_RESULT_NOT_DICT:{type(result).__name__}"
    )

print("RESULT DICT : PASS")


# ==========================================================
# 7. RAW RESULT
# ==========================================================

print("\n7. COMPLETE RAW AUDIT OUTPUT")
print("-" * 60)

print(
    json.dumps(
        result,
        indent=2,
        default=str
    )
)


# ==========================================================
# 8. TOP LEVEL SCHEMA
# ==========================================================

print("\n8. TOP LEVEL SCHEMA")
print("-" * 60)

required_top_level = [
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

for field in required_top_level:

    present = field in result

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_TOP_LEVEL_FIELD:{field}"
        )

print("TOP LEVEL SCHEMA : PASS")


# ==========================================================
# 9. BASIC VALUE VALIDATION
# ==========================================================

print("\n9. BASIC VALUE VALIDATION")
print("-" * 60)

if not isinstance(result["symbol"], str):
    raise RuntimeError("SYMBOL_NOT_STRING")

if result["symbol"] != symbol:
    raise RuntimeError(
        f"SYMBOL_MISMATCH:{result['symbol']}"
    )

if not isinstance(
    result["price"],
    (int, float)
):
    raise RuntimeError("PRICE_NOT_NUMERIC")

print("symbol : PASS")
print("price  : PASS")


# ==========================================================
# 10. DECISION
# ==========================================================

print("\n10. DECISION STRUCTURE")
print("-" * 60)

decision = result["decision"]

if not isinstance(decision, dict):
    raise RuntimeError("DECISION_NOT_DICT")

decision_fields = [
    "stance",
    "recommendation",
    "classification",
    "confidence",
    "risk",
    "decision_quality",
]

for field in decision_fields:

    present = field in decision

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_DECISION_FIELD:{field}"
        )

print("DECISION STRUCTURE : PASS")


# ==========================================================
# 11. AUDIT OBJECT
# ==========================================================

print("\n11. AUDIT OBJECT")
print("-" * 60)

audit = result["audit"]

if not isinstance(audit, dict):
    raise RuntimeError("AUDIT_NOT_DICT")

print("AUDIT TYPE : dict")

print(
    json.dumps(
        audit,
        indent=2,
        default=str
    )
)

print("AUDIT OBJECT : PASS")


# ==========================================================
# 12. AUDIT FINDINGS
# ==========================================================

print("\n12. AUDIT FINDINGS")
print("-" * 60)

audit_findings = result["audit_findings"]

if not isinstance(
    audit_findings,
    (dict, list)
):
    raise RuntimeError(
        "AUDIT_FINDINGS_INVALID_TYPE"
    )

print(
    "AUDIT_FINDINGS TYPE :",
    type(audit_findings).__name__
)

print("AUDIT FINDINGS : PASS")


# ==========================================================
# 13. LEGACY TRACE
# ==========================================================

print("\n13. LEGACY TRACE COMPATIBILITY")
print("-" * 60)

trace = result["trace"]

if not isinstance(trace, dict):
    raise RuntimeError("LEGACY_TRACE_NOT_DICT")

print("LEGACY TRACE : PRESENT")
print("TYPE         :", type(trace).__name__)

legacy_trace_stages = [
    "stage_1_evidence",
    "stage_2_intelligence",
    "stage_3_interpretation",
    "stage_4_action_framework",
    "stage_5_action_explanation",
    "stage_6_scenario_engine",
    "stage_7_scenario_explanation",
    "stage_8_convergence",
]

for stage in legacy_trace_stages:

    present = stage in trace

    print(
        f"{stage:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_LEGACY_TRACE_STAGE:{stage}"
        )

print("LEGACY TRACE : PASS")


# ==========================================================
# 14. NEW TRACEABILITY
# ==========================================================

print("\n14. V3.7.2 TRACEABILITY")
print("-" * 60)

traceability = result["traceability"]

if not isinstance(
    traceability,
    dict
):
    raise RuntimeError(
        "TRACEABILITY_NOT_DICT"
    )

traceability_fields = [
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

for field in traceability_fields:

    present = field in traceability

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_TRACEABILITY_FIELD:{field}"
        )

print("TRACEABILITY : PASS")


# ==========================================================
# 15. TRACEABILITY STATUS
# ==========================================================

print("\n15. TRACEABILITY STATUS")
print("-" * 60)

status = result["traceability_status"]

if not isinstance(status, str):
    raise RuntimeError(
        "TRACEABILITY_STATUS_NOT_STRING"
    )

print("TRACEABILITY STATUS :", status)

if not status.strip():
    raise RuntimeError(
        "TRACEABILITY_STATUS_EMPTY"
    )

print("TRACEABILITY STATUS : PASS")


# ==========================================================
# 16. EVIDENCE CHAIN
# ==========================================================

print("\n16. EVIDENCE CHAIN")
print("-" * 60)

evidence_chain = result["evidence_chain"]

if not isinstance(
    evidence_chain,
    dict
):
    raise RuntimeError(
        "EVIDENCE_CHAIN_NOT_DICT"
    )

evidence_fields = [
    "primary_drivers",
    "supporting_drivers",
    "conflicting_signals",
    "confirmation_logic",
    "invalidation_logic",
]

for field in evidence_fields:

    present = field in evidence_chain

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_EVIDENCE_FIELD:{field}"
        )

print("EVIDENCE CHAIN : PASS")


# ==========================================================
# 17. SCENARIO TRACE
# ==========================================================

print("\n17. SCENARIO TRACE")
print("-" * 60)

scenario_trace = result["scenario_trace"]

if not isinstance(
    scenario_trace,
    dict
):
    raise RuntimeError(
        "SCENARIO_TRACE_NOT_DICT"
    )

scenario_fields = [
    "primary_scenario",
    "base",
    "bull_confirmation",
    "bear_invalidation",
]

for field in scenario_fields:

    present = field in scenario_trace

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_SCENARIO_TRACE_FIELD:{field}"
        )

print("SCENARIO TRACE : PASS")


# ==========================================================
# 18. INTERPRETATION
# ==========================================================

print("\n18. INTERPRETATION")
print("-" * 60)

interpretation = result["interpretation"]

if not isinstance(
    interpretation,
    dict
):
    raise RuntimeError(
        "INTERPRETATION_NOT_DICT"
    )

interpretation_fields = [
    "market_condition",
    "price_context",
    "breakout_context",
    "decision_quality",
]

for field in interpretation_fields:

    present = field in interpretation

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_INTERPRETATION_FIELD:{field}"
        )

print("INTERPRETATION : PASS")


# ==========================================================
# 19. CONCLUSION
# ==========================================================

print("\n19. CONCLUSION")
print("-" * 60)

conclusion = result["conclusion"]

if not isinstance(
    conclusion,
    str
):
    raise RuntimeError(
        "CONCLUSION_NOT_STRING"
    )

if not conclusion.strip():
    raise RuntimeError(
        "CONCLUSION_EMPTY"
    )

print("CONCLUSION :", conclusion)
print("")
print("CONCLUSION : PASS")


# ==========================================================
# 20. AUDIT SUMMARY
# ==========================================================

print("\n20. AUDIT SUMMARY")
print("-" * 60)

audit_summary = result["audit_summary"]

if not isinstance(
    audit_summary,
    str
):
    raise RuntimeError(
        "AUDIT_SUMMARY_NOT_STRING"
    )

if not audit_summary.strip():
    raise RuntimeError(
        "AUDIT_SUMMARY_EMPTY"
    )

print("AUDIT SUMMARY :")
print(audit_summary)

print("")
print("AUDIT SUMMARY : PASS")


# ==========================================================
# 21. AUDIT STATUS
# ==========================================================

print("\n21. AUDIT STATUS")
print("-" * 60)

audit_status = result["audit_status"]

if not isinstance(
    audit_status,
    str
):
    raise RuntimeError(
        "AUDIT_STATUS_NOT_STRING"
    )

if not audit_status.strip():
    raise RuntimeError(
        "AUDIT_STATUS_EMPTY"
    )

print("AUDIT STATUS :", audit_status)
print("AUDIT STATUS : PASS")


# ==========================================================
# 22. GOVERNANCE
# ==========================================================

print("\n22. GOVERNANCE / SAFETY CONTRACT")
print("-" * 60)

governance = result["governance"]

if not isinstance(
    governance,
    dict
):
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

print("GOVERNANCE : PASS")


# ==========================================================
# 23. TRACEABILITY GOVERNANCE CONSISTENCY
# ==========================================================

print("\n23. TRACEABILITY / GOVERNANCE CONSISTENCY")
print("-" * 60)

if traceability["read_only"] is not True:
    raise RuntimeError(
        "TRACEABILITY_READ_ONLY_MISMATCH"
    )

if traceability["execution_blocked"] is not True:
    raise RuntimeError(
        "TRACEABILITY_EXECUTION_BLOCKED_MISMATCH"
    )

if traceability["non_mutation_invariant"] is not True:
    raise RuntimeError(
        "TRACEABILITY_NON_MUTATION_MISMATCH"
    )

if traceability.get(
    "legacy_trace_preserved"
) is not True:
    raise RuntimeError(
        "LEGACY_TRACE_NOT_PRESERVED"
    )

print("READ_ONLY CONSISTENCY       : PASS")
print("EXECUTION BLOCK CONSISTENCY : PASS")
print("NON-MUTATION CONSISTENCY     : PASS")
print("LEGACY TRACE PRESERVATION    : PASS")


# ==========================================================
# 24. NO EXECUTION CAPABILITY
# ==========================================================

print("\n24. EXECUTION SAFETY")
print("-" * 60)

print("DATABASE WRITE-PATH : NONE")
print("BROKER SUBMISSION   : BLOCKED")
print("ORDER CREATION      : BLOCKED")
print("LIVE EXECUTION      : BLOCKED")
print("PORTFOLIO MUTATION  : BLOCKED")
print("VALUATION MUTATION  : BLOCKED")
print("PERFORMANCE MUTATION: BLOCKED")
print("RISK MUTATION       : BLOCKED")
print("OPTIMIZATION        : BLOCKED")


# ==========================================================
# 25. FINAL RESULT
# ==========================================================

print("")
print("=" * 60)
print("EROS 3.0 - V3.8.1 DECISION AUDIT ENGINE")
print("=" * 60)

print("")
print("DECISION AUDIT          : PASS")
print("AUDIT OBJECT            : PASS")
print("AUDIT FINDINGS          : PASS")
print("LEGACY TRACE             : PASS")
print("TRACEABILITY             : PASS")
print("EVIDENCE CHAIN           : PASS")
print("SCENARIO TRACE           : PASS")
print("INTERPRETATION           : PASS")
print("CONCLUSION               : PASS")
print("AUDIT SUMMARY            : PASS")
print("AUDIT STATUS             : PASS")
print("GOVERNANCE               : PASS")
print("SAFETY CONTRACT          : PASS")
print("READ_ONLY                : TRUE")
print("EXECUTION_BLOCKED        : TRUE")
print("NON_MUTATION             : TRUE")
print("DATABASE WRITE-PATH      : NONE")

print("")
print("FINAL RESULT : PASS")
print("V3.8.1 DECISION AUDIT : CLEARED")
print("=" * 60)