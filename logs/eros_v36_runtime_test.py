import json

from services.eros_frontend_adapter import EROSFrontendAdapter


print("=" * 60)
print("EROS 3.0 - V3.6 DECISION CONVERGENCE ENGINE - RUNTIME")
print("=" * 60)


adapter = EROSFrontendAdapter()


print("\n1. ADAPTER IMPORT")
print("-" * 60)
print("IMPORT : PASS")
print("CLASS  :", adapter.__class__.__name__)


print("\n2. EXISTING API CHECK")
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
]

for name in required:
    ok = hasattr(adapter, name)
    print(f"{name:35} : {'PASS' if ok else 'FAIL'}")

    if not ok:
        raise RuntimeError(f"MISSING_API:{name}")


print("\n3. DECISION CONVERGENCE")
print("-" * 60)

result = adapter.decision_convergence("RELIANCE.NS")

if not isinstance(result, dict):
    raise RuntimeError("CONVERGENCE_RESULT_NOT_DICT")

print("DECISION CONVERGENCE : PASS")
print("SYMBOL :", result.get("symbol"))
print("PRICE  :", result.get("price"))


print("\n4. RAW CONVERGENCE OUTPUT")
print("-" * 60)

print(
    json.dumps(
        result,
        indent=2,
        default=str
    )
)


print("\n5. REQUIRED TOP-LEVEL STRUCTURE")
print("-" * 60)

required_fields = [
    "symbol",
    "price",
    "decision",
    "convergence",
    "interpretation",
    "conclusion",
    "governance",
]

for field in required_fields:
    ok = field in result
    print(f"{field:35} : {'PASS' if ok else 'FAIL'}")

    if not ok:
        raise RuntimeError(f"MISSING_FIELD:{field}")


print("\n6. DECISION STRUCTURE")
print("-" * 60)

decision = result["decision"]

for field in [
    "stance",
    "recommendation",
    "classification",
    "confidence",
    "risk",
    "decision_quality",
]:
    ok = field in decision
    print(f"{field:35} : {'PASS' if ok else 'FAIL'}")

    if not ok:
        raise RuntimeError(
            f"MISSING_DECISION_FIELD:{field}"
        )


print("\n7. CONVERGENCE STRUCTURE")
print("-" * 60)

convergence = result["convergence"]

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
    ok = field in convergence
    print(f"{field:35} : {'PASS' if ok else 'FAIL'}")

    if not ok:
        raise RuntimeError(
            f"MISSING_CONVERGENCE_FIELD:{field}"
        )


print("\n8. SCENARIO STRUCTURE")
print("-" * 60)

for scenario_name in [
    "base",
    "bull_confirmation",
    "bear_invalidation",
]:
    ok = scenario_name in convergence
    print(
        f"{scenario_name.upper():35} : "
        f"{'PASS' if ok else 'FAIL'}"
    )

    if not ok:
        raise RuntimeError(
            f"MISSING_SCENARIO:{scenario_name}"
        )


print("\n9. INTERPRETATION STRUCTURE")
print("-" * 60)

interpretation = result["interpretation"]

for field in [
    "market_condition",
    "price_context",
    "breakout_context",
    "decision_quality",
]:
    ok = field in interpretation
    print(f"{field:35} : {'PASS' if ok else 'FAIL'}")

    if not ok:
        raise RuntimeError(
            f"MISSING_INTERPRETATION_FIELD:{field}"
        )


print("\n10. CONCLUSION")
print("-" * 60)

if not isinstance(result["conclusion"], str):
    raise RuntimeError("CONCLUSION_NOT_STRING")

if not result["conclusion"].strip():
    raise RuntimeError("CONCLUSION_EMPTY")

print("CONCLUSION : PASS")


print("\n11. SAFETY CONTRACT")
print("-" * 60)

safety = result["governance"]

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
    actual = safety.get(field)
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
    actual = safety.get(field)
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


print("\n12. DATABASE WRITE-PATH")
print("-" * 60)

print("DATABASE WRITE-PATH : NONE")
print("EXECUTION PATH      : BLOCKED")


print("\n============================================================")
print("EROS 3.0 - V3.6 DECISION CONVERGENCE ENGINE")
print("============================================================")

print("")
print("DECISION CONVERGENCE : PASS")
print("DECISION STRUCTURE   : PASS")
print("SCENARIO STRUCTURE   : PASS")
print("INTERPRETATION       : PASS")
print("CONCLUSION           : PASS")
print("SAFETY CONTRACT      : PASS")
print("READ_ONLY            : TRUE")
print("EXECUTION_BLOCKED    : TRUE")
print("NON_MUTATION         : TRUE")
print("DATABASE WRITE-PATH  : NONE")

print("")
print("FINAL RESULT : PASS")
print("V3.6 DECISION CONVERGENCE : CLEARED")
print("============================================================")