import json
import sys
import traceback

from services.eros_frontend_adapter import EROSFrontendAdapter


print("=" * 60)
print("EROS 3.0 - V3.7.2 TRACEABILITY COMPATIBILITY RUNTIME")
print("=" * 60)


print("\nPYTHON VERSION")
print("-" * 60)
print(sys.version)


print("\n1. ADAPTER IMPORT")
print("-" * 60)

adapter = EROSFrontendAdapter()

print("IMPORT : PASS")
print("CLASS  :", adapter.__class__.__name__)


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
]

for name in foundation:
    ok = hasattr(adapter, name)

    print(
        f"{name:35} : "
        f"{'PASS' if ok else 'FAIL'}"
    )

    if not ok:
        raise RuntimeError(
            f"MISSING_API:{name}"
        )


print("\nV3.6 / V3.7 FOUNDATION : VERIFIED")


print("\n3. EXECUTING DECISION TRACEABILITY")
print("-" * 60)

symbol = "RELIANCE.NS"

print("SYMBOL :", symbol)

try:
    result = adapter.decision_traceability(symbol)

except Exception as exc:
    print("TRACEABILITY CALL : FAIL")
    print("ERROR TYPE :", type(exc).__name__)
    print("ERROR      :", str(exc))
    traceback.print_exc()
    raise


print("TRACEABILITY CALL : PASS")
print("RESULT TYPE       :", type(result).__name__)


if not isinstance(result, dict):
    raise RuntimeError(
        "TRACEABILITY_RESULT_NOT_DICT"
    )


print("\n4. RAW TRACEABILITY RESULT")
print("-" * 60)

print(
    json.dumps(
        result,
        indent=2,
        default=str
    )
)


print("\n5. TOP LEVEL SCHEMA")
print("-" * 60)

required_top = [
    "symbol",
    "price",
    "decision",
    "trace",
    "traceability",
    "evidence_chain",
    "scenario_trace",
    "interpretation",
    "conclusion",
    "governance",
    "traceability_status",
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


print("\nTOP LEVEL SCHEMA : PASS")


print("\n6. LEGACY TRACE COMPATIBILITY")
print("-" * 60)

legacy_trace = result.get("trace")

print(
    "legacy 'trace' present :",
    "PASS" if "trace" in result else "FAIL"
)

if "trace" not in result:
    raise RuntimeError(
        "LEGACY_TRACE_REMOVED"
    )

print(
    "legacy 'trace' type    :",
    type(legacy_trace).__name__
)

if not isinstance(legacy_trace, dict):
    raise RuntimeError(
        "LEGACY_TRACE_NOT_DICT"
    )

print("LEGACY TRACE : PRESERVED")


print("\n7. NEW TRACEABILITY SCHEMA")
print("-" * 60)

traceability = result.get("traceability")

print(
    "traceability present :",
    "PASS" if "traceability" in result else "FAIL"
)

print(
    "traceability type    :",
    type(traceability).__name__
)

if not isinstance(traceability, dict):
    raise RuntimeError(
        "TRACEABILITY_NOT_DICT"
    )

print("TRACEABILITY : DICT PASS")


print("\n8. TRACEABILITY LAYERS")
print("-" * 60)

required_layers = [
    "stage_1_evidence",
    "stage_2_intelligence",
    "stage_3_interpretation",
    "stage_4_action_framework",
    "stage_5_action_explanation",
    "stage_6_scenario_engine",
    "stage_7_scenario_explanation",
    "stage_8_convergence",
]

for layer in required_layers:

    ok = layer in traceability

    print(
        f"{layer:35} : "
        f"{'PASS' if ok else 'FAIL'}"
    )

    if not ok:
        raise RuntimeError(
            f"MISSING_TRACEABILITY_LAYER:{layer}"
        )


print("\nTRACEABILITY LAYERS : PASS")


print("\n9. TRACEABILITY STATUS")
print("-" * 60)

status = result.get("traceability_status")

print("STATUS :", status)

if status != "COMPLETE":
    raise RuntimeError(
        f"INVALID_TRACEABILITY_STATUS:{status}"
    )

print("TRACEABILITY STATUS : COMPLETE")


print("\n10. DECISION VALIDATION")
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

    ok = field in decision

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'}"
    )

    if not ok:
        raise RuntimeError(
            f"MISSING_DECISION_FIELD:{field}"
        )

print("DECISION STRUCTURE : PASS")


print("\n11. V3.6 CONVERGENCE VALIDATION")
print("-" * 60)

convergence = result.get("traceability", {}).get(
    "stage_8_convergence"
)

if not isinstance(convergence, dict):
    raise RuntimeError(
        "CONVERGENCE_TRACE_NOT_DICT"
    )

for field in [
    "source",
    "status",
    "primary_scenario",
]:

    ok = field in convergence

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'}"
    )

    if not ok:
        raise RuntimeError(
            f"MISSING_CONVERGENCE_TRACE_FIELD:{field}"
        )

print(
    "PRIMARY SCENARIO :",
    convergence.get("primary_scenario")
)

print("V3.6 CONVERGENCE : PASS")


print("\n12. EVIDENCE CHAIN")
print("-" * 60)

evidence_chain = result.get(
    "evidence_chain"
)

if not isinstance(evidence_chain, dict):
    raise RuntimeError(
        "EVIDENCE_CHAIN_NOT_DICT"
    )

for field in [
    "primary_drivers",
    "supporting_drivers",
    "conflicting_signals",
    "confirmation_logic",
    "invalidation_logic",
]:

    ok = field in evidence_chain

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'}"
    )

    if not ok:
        raise RuntimeError(
            f"MISSING_EVIDENCE_FIELD:{field}"
        )

print("EVIDENCE CHAIN : PASS")


print("\n13. SCENARIO TRACE")
print("-" * 60)

scenario_trace = result.get(
    "scenario_trace"
)

if not isinstance(scenario_trace, dict):
    raise RuntimeError(
        "SCENARIO_TRACE_NOT_DICT"
    )

for field in [
    "primary_scenario",
    "base",
    "bull_confirmation",
    "bear_invalidation",
]:

    ok = field in scenario_trace

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'}"
    )

    if not ok:
        raise RuntimeError(
            f"MISSING_SCENARIO_TRACE_FIELD:{field}"
        )

print("SCENARIO TRACE : PASS")


print("\n14. INTERPRETATION")
print("-" * 60)

interpretation = result.get(
    "interpretation"
)

if not isinstance(interpretation, dict):
    raise RuntimeError(
        "INTERPRETATION_NOT_DICT"
    )

for field in [
    "market_condition",
    "price_context",
    "breakout_context",
    "decision_quality",
]:

    ok = field in interpretation

    print(
        f"{field:35} : "
        f"{'PASS' if ok else 'FAIL'}"
    )

    if not ok:
        raise RuntimeError(
            f"MISSING_INTERPRETATION_FIELD:{field}"
        )

print("INTERPRETATION : PASS")


print("\n15. CONCLUSION")
print("-" * 60)

conclusion = result.get("conclusion")

if not isinstance(conclusion, str):
    raise RuntimeError(
        "CONCLUSION_NOT_STRING"
    )

if not conclusion.strip():
    raise RuntimeError(
        "CONCLUSION_EMPTY"
    )

print("CONCLUSION : PASS")
print("SUMMARY :")
print(conclusion)


print("\n16. GOVERNANCE")
print("-" * 60)

governance = result.get(
    "governance"
)

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


print("GOVERNANCE : PASS")


print("\n17. DATABASE / EXECUTION SAFETY")
print("-" * 60)

print("DATABASE WRITE-PATH : NONE")
print("EXECUTION PATH      : BLOCKED")
print("ORDER CREATION      : BLOCKED")
print("BROKER SUBMISSION   : BLOCKED")
print("PORTFOLIO MUTATION  : BLOCKED")
print("OPTIMIZATION        : BLOCKED")


print("\n18. COMPATIBILITY ASSERTIONS")
print("-" * 60)

assert "trace" in result
assert isinstance(result["trace"], dict)

assert "traceability" in result
assert isinstance(result["traceability"], dict)

assert result["traceability_status"] == "COMPLETE"

assert result["governance"]["read_only"] is True
assert result["governance"]["execution_blocked"] is True
assert result["governance"]["non_mutation_invariant"] is True

for field in [
    "allow_order_creation",
    "allow_broker_submission",
    "allow_live_execution",
    "allow_portfolio_mutation",
    "allow_valuation_mutation",
    "allow_performance_mutation",
    "allow_risk_mutation",
    "allow_optimization",
]:

    assert result["governance"][field] is False


print("LEGACY TRACE PRESERVED       : PASS")
print("NEW TRACEABILITY PRESENT     : PASS")
print("TRACEABILITY IS DICT         : PASS")
print("TRACEABILITY COMPLETE        : PASS")
print("SAFETY INVARIANTS            : PASS")


print("")
print("=" * 60)
print("EROS 3.0 - V3.7.2 TRACEABILITY COMPATIBILITY")
print("=" * 60)

print("")
print("LEGACY TRACE              : PASS")
print("TRACEABILITY SCHEMA       : PASS")
print("TRACEABILITY LAYERS       : PASS")
print("DECISION STRUCTURE        : PASS")
print("CONVERGENCE               : PASS")
print("EVIDENCE CHAIN            : PASS")
print("SCENARIO TRACE            : PASS")
print("INTERPRETATION            : PASS")
print("CONCLUSION                : PASS")
print("GOVERNANCE                : PASS")
print("DATABASE WRITE-PATH       : NONE")
print("EXECUTION PATH            : BLOCKED")
print("READ_ONLY                 : TRUE")
print("NON_MUTATION              : TRUE")

print("")
print("FINAL RESULT : PASS")
print("V3.7.2 TRACEABILITY COMPATIBILITY : CLEARED")
print("=" * 60)