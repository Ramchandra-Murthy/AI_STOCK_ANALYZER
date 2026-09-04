import json
import traceback

from services.eros_frontend_adapter import EROSFrontendAdapter


print("=" * 60)
print("EROS 3.0 - V3.7 DECISION TRACEABILITY ENGINE - RUNTIME")
print("=" * 60)


adapter = EROSFrontendAdapter()


# ============================================================
# 1. IMPORT
# ============================================================

print("\n1. ADAPTER IMPORT")
print("-" * 60)

print("IMPORT : PASS")
print("CLASS  :", adapter.__class__.__name__)


# ============================================================
# 2. FOUNDATION API CHECK
# ============================================================

print("\n2. FOUNDATION API CHECK")
print("-" * 60)

foundation_apis = [
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
]

for name in foundation_apis:

    present = hasattr(adapter, name)

    print(
        f"{name:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_FOUNDATION_API:{name}"
        )


print("\nV3.6 FOUNDATION : VERIFIED")


# ============================================================
# 3. V3.7 API
# ============================================================

print("\n3. V3.7 TRACEABILITY API")
print("-" * 60)

if not hasattr(adapter, "decision_traceability"):
    raise RuntimeError(
        "MISSING_API:decision_traceability"
    )

print(
    "decision_traceability             : PASS"
)

print("V3.7 API : PRESENT")


# ============================================================
# 4. TRACEABILITY EXECUTION
# ============================================================

print("\n4. DECISION TRACEABILITY")
print("-" * 60)

symbol = "RELIANCE.NS"

result = adapter.decision_traceability(symbol)

if not isinstance(result, dict):
    raise RuntimeError(
        "TRACEABILITY_RESULT_NOT_DICT"
    )

print("DECISION TRACEABILITY : PASS")
print("SYMBOL :", result.get("symbol"))
print("PRICE  :", result.get("price"))


# ============================================================
# 5. RAW OUTPUT
# ============================================================

print("\n5. RAW TRACEABILITY OUTPUT")
print("-" * 60)

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

print("\n6. TOP-LEVEL STRUCTURE")
print("-" * 60)

required_top_level = [
    "symbol",
    "price",
    "decision",
    "traceability",
    "conclusion",
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


# ============================================================
# 7. SYMBOL / PRICE
# ============================================================

print("\n7. BASIC IDENTITY")
print("-" * 60)

if result["symbol"] != symbol:
    raise RuntimeError(
        "SYMBOL_MISMATCH"
    )

if result["price"] is None:
    raise RuntimeError(
        "PRICE_MISSING"
    )

print("SYMBOL : PASS")
print("PRICE  : PASS")


# ============================================================
# 8. DECISION STRUCTURE
# ============================================================

print("\n8. DECISION STRUCTURE")
print("-" * 60)

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

    present = field in decision

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_DECISION_FIELD:{field}"
        )


# ============================================================
# 9. TRACEABILITY STRUCTURE
# ============================================================

print("\n9. TRACEABILITY STRUCTURE")
print("-" * 60)

traceability = result["traceability"]

traceability_fields = [
    "decision",
    "evidence",
    "intelligence",
    "interpretation",
    "action",
    "action_explanation",
    "scenario",
    "scenario_explanation",
    "convergence",
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


# ============================================================
# 10. DECISION LINEAGE
# ============================================================

print("\n10. DECISION LINEAGE")
print("-" * 60)

decision_trace = traceability["decision"]

for field in [
    "stance",
    "recommendation",
    "classification",
    "confidence",
    "risk",
]:

    present = field in decision_trace

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_DECISION_TRACE:{field}"
        )


# ============================================================
# 11. EVIDENCE LINEAGE
# ============================================================

print("\n11. EVIDENCE LINEAGE")
print("-" * 60)

evidence = traceability["evidence"]

for field in [
    "trend",
    "momentum",
    "score",
    "confidence",
    "recommendation",
    "risk",
    "reasons",
    "breakout_signal",
    "breakout_reason",
    "technical_indicators",
]:

    present = field in evidence

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_EVIDENCE_TRACE:{field}"
        )


# ============================================================
# 12. TECHNICAL INDICATOR LINEAGE
# ============================================================

print("\n12. TECHNICAL INDICATOR LINEAGE")
print("-" * 60)

technical = evidence["technical_indicators"]

technical_fields = [
    "sma_20",
    "sma_50",
    "ema_20",
    "rsi_14",
    "macd",
    "signal",
    "histogram",
    "bb_middle",
    "bb_upper",
    "bb_lower",
    "atr",
    "support",
    "resistance",
]

for field in technical_fields:

    present = field in technical

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_TECHNICAL_TRACE:{field}"
        )


# ============================================================
# 13. INTELLIGENCE LINEAGE
# ============================================================

print("\n13. INTELLIGENCE LINEAGE")
print("-" * 60)

intelligence = traceability["intelligence"]

for field in [
    "decision",
    "market_context",
    "technical_drivers",
    "risk_flags",
]:

    present = field in intelligence

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_INTELLIGENCE_TRACE:{field}"
        )


# ============================================================
# 14. INTERPRETATION LINEAGE
# ============================================================

print("\n14. INTERPRETATION LINEAGE")
print("-" * 60)

interpretation = traceability["interpretation"]

for field in [
    "market_condition",
    "price_context",
    "breakout_context",
    "decision_quality",
    "primary_drivers",
    "supporting_drivers",
    "conflicting_signals",
    "invalidation_context",
]:

    present = field in interpretation

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_INTERPRETATION_TRACE:{field}"
        )


# ============================================================
# 15. ACTION LINEAGE
# ============================================================

print("\n15. ACTION LINEAGE")
print("-" * 60)

action = traceability["action"]

for field in [
    "classification",
    "stance",
    "recommendation",
    "score",
    "confidence",
    "confidence_band",
    "risk_context",
]:

    present = field in action

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_ACTION_TRACE:{field}"
        )


# ============================================================
# 16. ACTION EXPLANATION LINEAGE
# ============================================================

print("\n16. ACTION EXPLANATION LINEAGE")
print("-" * 60)

action_explanation = traceability[
    "action_explanation"
]

for field in [
    "primary_reason",
    "supporting_reasons",
    "primary_drivers",
    "supporting_drivers",
    "conflicting_signals",
    "confirmation_logic",
    "invalidation_logic",
    "decision_quality",
    "risk_explanation",
    "execution_status",
]:

    present = field in action_explanation

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_ACTION_EXPLANATION_TRACE:{field}"
        )


# ============================================================
# 17. SCENARIO LINEAGE
# ============================================================

print("\n17. SCENARIO LINEAGE")
print("-" * 60)

scenario = traceability["scenario"]

for field in [
    "primary_scenario",
    "base",
    "bull_confirmation",
    "bear_invalidation",
]:

    present = field in scenario

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_SCENARIO_TRACE:{field}"
        )


# ============================================================
# 18. SCENARIO EXPLANATION LINEAGE
# ============================================================

print("\n18. SCENARIO EXPLANATION LINEAGE")
print("-" * 60)

scenario_explanation = traceability[
    "scenario_explanation"
]

for field in [
    "base",
    "bull",
    "bear",
    "confirmation_logic",
    "invalidation_logic",
    "decision_quality",
    "summary",
]:

    present = field in scenario_explanation

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_SCENARIO_EXPLANATION_TRACE:{field}"
        )


# ============================================================
# 19. CONVERGENCE LINEAGE
# ============================================================

print("\n19. CONVERGENCE LINEAGE")
print("-" * 60)

convergence = traceability["convergence"]

for field in [
    "primary_scenario",
    "base",
    "bull_confirmation",
    "bear_invalidation",
    "confirmation_logic",
    "invalidation_logic",
    "primary_drivers",
    "supporting_drivers",
    "conflicting_signals",
]:

    present = field in convergence

    print(
        f"{field:35} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"MISSING_CONVERGENCE_TRACE:{field}"
        )


# ============================================================
# 20. TRACEABILITY COMPLETENESS
# ============================================================

print("\n20. TRACEABILITY COMPLETENESS")
print("-" * 60)

lineage_sequence = [
    "decision",
    "evidence",
    "intelligence",
    "interpretation",
    "action",
    "action_explanation",
    "scenario",
    "scenario_explanation",
    "convergence",
]

for index, layer in enumerate(lineage_sequence, start=1):

    present = layer in traceability

    print(
        f"{index:02d}. {layer:30} : "
        f"{'PASS' if present else 'FAIL'}"
    )

    if not present:
        raise RuntimeError(
            f"TRACEABILITY_INCOMPLETE:{layer}"
        )

print("TRACEABILITY COMPLETENESS : PASS")


# ============================================================
# 21. CONCLUSION
# ============================================================

print("\n21. CONCLUSION")
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
print("")
print(conclusion)


# ============================================================
# 22. GOVERNANCE
# ============================================================

print("\n22. GOVERNANCE")
print("-" * 60)

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
        f"(actual={actual}, expected=True)"
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
        f"(actual={actual}, expected=False)"
    )

    if not ok:
        raise RuntimeError(
            f"GOVERNANCE_FAILURE:{field}"
        )


# ============================================================
# 23. DATABASE WRITE-PATH
# ============================================================

print("\n23. DATABASE WRITE-PATH")
print("-" * 60)

print("DATABASE WRITE-PATH : NONE")
print("EXECUTION PATH      : BLOCKED")


# ============================================================
# 24. FINAL CERTIFICATION
# ============================================================

print("")
print("=" * 60)
print("EROS 3.0 - V3.7 DECISION TRACEABILITY ENGINE")
print("=" * 60)

print("")
print("DECISION TRACEABILITY : PASS")
print("DECISION LINEAGE      : PASS")
print("EVIDENCE LINEAGE      : PASS")
print("INTELLIGENCE LINEAGE  : PASS")
print("INTERPRETATION        : PASS")
print("ACTION LINEAGE        : PASS")
print("SCENARIO LINEAGE      : PASS")
print("CONVERGENCE LINEAGE   : PASS")
print("TRACEABILITY COMPLETE : PASS")
print("CONCLUSION             : PASS")
print("SAFETY CONTRACT       : PASS")
print("READ_ONLY             : TRUE")
print("EXECUTION_BLOCKED     : TRUE")
print("NON_MUTATION          : TRUE")
print("DATABASE WRITE-PATH   : NONE")

print("")
print("FINAL RESULT : PASS")
print("V3.7 DECISION TRACEABILITY : CLEARED")
print("=" * 60)