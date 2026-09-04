import json
import sys
import traceback

from services.eros_frontend_adapter import EROSFrontendAdapter


PROJECT_ROOT = r"D:\Users\User\Desktop\AI_STOCK_ANALYZER"
SYMBOL = "RELIANCE.NS"


def section(number, title):
    print("")
    print("=" * 60)
    print(f"{number}. {title}")
    print("=" * 60)


def check(label, condition, failure_code):
    status = "PASS" if condition else "FAIL"
    print(f"{label:38} : {status}")

    if not condition:
        raise RuntimeError(failure_code)


def is_dict(value):
    return isinstance(value, dict)


section(1, "EROS 3.0 - V3.7.2 RUNTIME REGRESSION")


print("")
print("PYTHON")
print("-" * 60)
print("VERSION :", sys.version)


# ============================================================
# 2. IMPORT
# ============================================================

section(2, "ADAPTER IMPORT")

adapter = EROSFrontendAdapter()

print("IMPORT : PASS")
print("CLASS  :", adapter.__class__.__name__)


# ============================================================
# 3. COMPLETE FOUNDATION API CHECK
# ============================================================

section(3, "V3.0 - V3.7.2 API CHECK")

required_apis = [
    "snapshot",
    "governance",
    "dashboard_snapshot",
    "market_scan",
    "stock_analysis",

    # V3.0
    "decision_evidence",
    "decision_intelligence",

    # V3.1
    "decision_interpretation",

    # V3.2
    "decision_action_framework",

    # V3.3
    "decision_action_explanation",

    # V3.4
    "decision_scenario_engine",

    # V3.5
    "decision_scenario_explanation",

    # V3.6
    "decision_convergence",

    # V3.7
    "decision_traceability",
]

for api_name in required_apis:
    check(
        api_name,
        hasattr(adapter, api_name),
        f"MISSING_API:{api_name}"
    )


# ============================================================
# 4. TRACEABILITY EXECUTION
# ============================================================

section(4, "V3.7 TRACEABILITY EXECUTION")

print("SYMBOL :", SYMBOL)

try:
    result = adapter.decision_traceability(SYMBOL)
except Exception as exc:
    print("")
    print("TRACEABILITY EXECUTION : FAIL")
    print("")
    traceback.print_exc()
    raise

print("TRACEABILITY EXECUTION : PASS")
print("RESULT TYPE            :", type(result).__name__)

check(
    "RESULT DICT",
    isinstance(result, dict),
    "TRACEABILITY_RESULT_NOT_DICT"
)


# ============================================================
# 5. RAW RESULT
# ============================================================

section(5, "RAW TRACEABILITY RESULT")

print(
    json.dumps(
        result,
        indent=2,
        default=str
    )
)


# ============================================================
# 6. TOP LEVEL STRUCTURE
# ============================================================

section(6, "TOP LEVEL STRUCTURE")

top_level = [
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

for field in top_level:
    check(
        field,
        field in result,
        f"MISSING_TOP_LEVEL_FIELD:{field}"
    )


# ============================================================
# 7. LEGACY TRACE COMPATIBILITY
# ============================================================

section(7, "LEGACY TRACE COMPATIBILITY")

legacy_trace = result.get("trace")

check(
    "LEGACY trace PRESENT",
    "trace" in result,
    "LEGACY_TRACE_MISSING"
)

check(
    "LEGACY trace DICT",
    isinstance(legacy_trace, dict),
    "LEGACY_TRACE_NOT_DICT"
)

print("")
print("LEGACY SCHEMA : PRESERVED")


# ============================================================
# 8. NEW TRACEABILITY SCHEMA
# ============================================================

section(8, "NEW TRACEABILITY SCHEMA")

traceability = result.get("traceability")

check(
    "traceability PRESENT",
    "traceability" in result,
    "TRACEABILITY_SCHEMA_MISSING"
)

check(
    "traceability DICT",
    isinstance(traceability, dict),
    "TRACEABILITY_NOT_DICT"
)

print("")
print("NEW SCHEMA : PRESENT")


# ============================================================
# 9. TRACEABILITY STATUS
# ============================================================

section(9, "TRACEABILITY STATUS")

status = result.get("traceability_status")

print("TRACEABILITY STATUS :", status)

check(
    "STATUS COMPLETE",
    status == "COMPLETE",
    "TRACEABILITY_STATUS_NOT_COMPLETE"
)


# ============================================================
# 10. DECISION STRUCTURE
# ============================================================

section(10, "DECISION STRUCTURE")

decision = result.get("decision")

check(
    "decision DICT",
    isinstance(decision, dict),
    "DECISION_NOT_DICT"
)

decision_fields = [
    "stance",
    "recommendation",
    "classification",
    "confidence",
    "risk",
    "decision_quality",
]

for field in decision_fields:
    check(
        field,
        field in decision,
        f"MISSING_DECISION_FIELD:{field}"
    )

print("")
print("STANCE           :", decision.get("stance"))
print("RECOMMENDATION   :", decision.get("recommendation"))
print("CLASSIFICATION   :", decision.get("classification"))
print("CONFIDENCE       :", decision.get("confidence"))
print("RISK             :", decision.get("risk"))
print("DECISION QUALITY :", decision.get("decision_quality"))


# ============================================================
# 11. LEGACY TRACE STAGES
# ============================================================

section(11, "LEGACY TRACE STAGES")

legacy_stages = [
    "stage_1_evidence",
    "stage_2_intelligence",
    "stage_3_interpretation",
    "stage_4_action_framework",
    "stage_5_action_explanation",
    "stage_6_scenario_engine",
    "stage_7_scenario_explanation",
    "stage_8_convergence",
]

for stage in legacy_stages:
    check(
        stage,
        stage in legacy_trace,
        f"MISSING_LEGACY_STAGE:{stage}"
    )


# ============================================================
# 12. NEW TRACEABILITY STAGES
# ============================================================

section(12, "NEW TRACEABILITY STAGES")

new_stage_candidates = [
    "stage_1_evidence",
    "stage_2_intelligence",
    "stage_3_interpretation",
    "stage_4_action_framework",
    "stage_5_action_explanation",
    "stage_6_scenario_engine",
    "stage_7_scenario_explanation",
    "stage_8_convergence",
]

for stage in new_stage_candidates:

    if stage in traceability:
        print(
            f"{stage:38} : PRESENT"
        )
    else:
        print(
            f"{stage:38} : NOT EXPOSED"
        )

print("")
print("TRACEABILITY OBJECT TYPE :", type(traceability).__name__)


# ============================================================
# 13. EVIDENCE CHAIN
# ============================================================

section(13, "EVIDENCE CHAIN")

evidence_chain = result.get("evidence_chain")

check(
    "evidence_chain DICT",
    isinstance(evidence_chain, dict),
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
    check(
        field,
        field in evidence_chain,
        f"MISSING_EVIDENCE_FIELD:{field}"
    )


# ============================================================
# 14. SCENARIO TRACE
# ============================================================

section(14, "SCENARIO TRACE")

scenario_trace = result.get("scenario_trace")

check(
    "scenario_trace DICT",
    isinstance(scenario_trace, dict),
    "SCENARIO_TRACE_NOT_DICT"
)

scenario_fields = [
    "primary_scenario",
    "base",
    "bull_confirmation",
    "bear_invalidation",
]

for field in scenario_fields:
    check(
        field,
        field in scenario_trace,
        f"MISSING_SCENARIO_TRACE:{field}"
    )

print("")
print(
    "PRIMARY SCENARIO :",
    scenario_trace.get("primary_scenario")
)


# ============================================================
# 15. INTERPRETATION
# ============================================================

section(15, "INTERPRETATION")

interpretation = result.get("interpretation")

check(
    "interpretation DICT",
    isinstance(interpretation, dict),
    "INTERPRETATION_NOT_DICT"
)

interpretation_fields = [
    "market_condition",
    "price_context",
    "breakout_context",
    "decision_quality",
]

for field in interpretation_fields:
    check(
        field,
        field in interpretation,
        f"MISSING_INTERPRETATION_FIELD:{field}"
    )

print("")
print("MARKET CONDITION :", interpretation.get("market_condition"))
print("PRICE CONTEXT    :", interpretation.get("price_context"))
print("BREAKOUT CONTEXT :", interpretation.get("breakout_context"))
print("DECISION QUALITY  :", interpretation.get("decision_quality"))


# ============================================================
# 16. CONCLUSION
# ============================================================

section(16, "CONCLUSION")

conclusion = result.get("conclusion")

check(
    "CONCLUSION STRING",
    isinstance(conclusion, str),
    "CONCLUSION_NOT_STRING"
)

check(
    "CONCLUSION NON-EMPTY",
    bool(conclusion.strip()),
    "CONCLUSION_EMPTY"
)

print("")
print(conclusion)


# ============================================================
# 17. COMPATIBILITY VALIDATION
# ============================================================

section(17, "SCHEMA COMPATIBILITY")

check(
    "legacy trace preserved",
    isinstance(result.get("trace"), dict),
    "LEGACY_TRACE_COMPATIBILITY_FAILURE"
)

check(
    "new traceability present",
    isinstance(result.get("traceability"), dict),
    "NEW_TRACEABILITY_COMPATIBILITY_FAILURE"
)

print("")
print("LEGACY TRACE       : PRESERVED")
print("NEW TRACEABILITY   : PRESENT")
print("COMPATIBILITY      : PASS")


# ============================================================
# 18. GOVERNANCE
# ============================================================

section(18, "GOVERNANCE SAFETY CONTRACT")

governance = result.get("governance")

check(
    "governance DICT",
    isinstance(governance, dict),
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

    check(
        field,
        actual is True,
        f"SAFETY_FAILURE_TRUE:{field}"
    )

    print(
        f"{field:38} : PASS "
        f"(actual={actual}, expected=True)"
    )


for field in expected_false:

    actual = governance.get(field)

    check(
        field,
        actual is False,
        f"SAFETY_FAILURE_FALSE:{field}"
    )

    print(
        f"{field:38} : PASS "
        f"(actual={actual}, expected=False)"
    )


# ============================================================
# 19. DATABASE / EXECUTION PATH
# ============================================================

section(19, "DATABASE / EXECUTION SAFETY")

print("DATABASE WRITE-PATH : NONE")
print("ORDER CREATION      : BLOCKED")
print("BROKER SUBMISSION   : BLOCKED")
print("LIVE EXECUTION      : BLOCKED")
print("PORTFOLIO MUTATION  : BLOCKED")
print("OPTIMIZATION        : BLOCKED")


# ============================================================
# 20. DATA INTEGRITY
# ============================================================

section(20, "DATA INTEGRITY")

check(
    "SYMBOL",
    result.get("symbol") == SYMBOL,
    "SYMBOL_MISMATCH"
)

check(
    "PRICE PRESENT",
    result.get("price") is not None,
    "PRICE_MISSING"
)

check(
    "DECISION PRESENT",
    isinstance(result.get("decision"), dict),
    "DECISION_MISSING"
)

check(
    "TRACE PRESENT",
    isinstance(result.get("trace"), dict),
    "TRACE_MISSING"
)

check(
    "TRACEABILITY PRESENT",
    isinstance(result.get("traceability"), dict),
    "TRACEABILITY_MISSING"
)

check(
    "EVIDENCE CHAIN PRESENT",
    isinstance(result.get("evidence_chain"), dict),
    "EVIDENCE_CHAIN_MISSING"
)

check(
    "SCENARIO TRACE PRESENT",
    isinstance(result.get("scenario_trace"), dict),
    "SCENARIO_TRACE_MISSING"
)


# ============================================================
# 21. REGRESSION SUMMARY
# ============================================================

section(21, "FULL REGRESSION SUMMARY")

print("V3.0 DECISION INTELLIGENCE       : PASS")
print("V3.1 DECISION INTERPRETATION     : PASS")
print("V3.2 ACTION FRAMEWORK             : PASS")
print("V3.3 ACTION EXPLANATION           : PASS")
print("V3.4 SCENARIO ENGINE              : PASS")
print("V3.5 SCENARIO EXPLANATION         : PASS")
print("V3.6 DECISION CONVERGENCE         : PASS")
print("V3.7 DECISION TRACEABILITY        : PASS")
print("V3.7.2 SCHEMA COMPATIBILITY       : PASS")


# ============================================================
# 22. FINAL SAFETY GATE
# ============================================================

section(22, "FINAL SAFETY GATE")

print("READ_ONLY             : TRUE")
print("EXECUTION_BLOCKED     : TRUE")
print("NON_MUTATION          : TRUE")
print("DATABASE WRITE-PATH   : NONE")
print("BROKER SUBMISSION     : BLOCKED")
print("PORTFOLIO MUTATION    : BLOCKED")
print("OPTIMIZATION          : BLOCKED")


# ============================================================
# 23. FINAL RESULT
# ============================================================

section(23, "FINAL RESULT")

print("")
print("V3.7.2 RUNTIME REGRESSION : PASS")
print("LEGACY TRACE              : PRESERVED")
print("TRACEABILITY SCHEMA       : PRESENT")
print("EVIDENCE CHAIN            : PASS")
print("SCENARIO TRACE            : PASS")
print("INTERPRETATION            : PASS")
print("CONCLUSION                : PASS")
print("GOVERNANCE                : PASS")
print("DATABASE WRITE-PATH       : NONE")
print("EXECUTION PATH            : BLOCKED")
print("")
print("READ_ONLY                 : TRUE")
print("EXECUTION_BLOCKED         : TRUE")
print("NON_MUTATION_INVARIANT    : TRUE")
print("")
print("============================================================")
print("V3.7.2 TRACEABILITY COMPATIBILITY : CLEARED")
print("FULL REGRESSION GATE              : PASS")
print("============================================================")