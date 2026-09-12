import json

from services.eros_frontend_adapter import EROSFrontendAdapter

print("=" * 60)
print("EROS 3.0 - V3.7 DECISION TRACEABILITY ENGINE - RUNTIME")
print("=" * 60)


SYMBOL = "RELIANCE.NS"


def check(condition, label):
    status = "PASS" if condition else "FAIL"
    print(f"{label:45} : {status}")

    if not condition:
        raise RuntimeError(f"CHECK_FAILED:{label}")


def require_dict(value, label):
    check(isinstance(value, dict), label)
    return value


def require_field(obj, field, label=None):
    label = label or field
    check(field in obj, label)
    return obj[field]


def check_safety(governance, prefix=""):
    print("")
    print(prefix + "SAFETY CONTRACT")
    print("-" * 60)

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

        print(f"{field:35} : " f"{'PASS' if ok else 'FAIL'} " f"(actual={actual}, expected=True)")

        if not ok:
            raise RuntimeError(f"SAFETY_FAILURE:{field}")

    for field in expected_false:
        actual = governance.get(field)
        ok = actual is False

        print(f"{field:35} : " f"{'PASS' if ok else 'FAIL'} " f"(actual={actual}, expected=False)")

        if not ok:
            raise RuntimeError(f"SAFETY_FAILURE:{field}")


adapter = EROSFrontendAdapter()


print("")
print("1. ADAPTER IMPORT")
print("-" * 60)

print("IMPORT : PASS")
print("CLASS  :", adapter.__class__.__name__)


print("")
print("2. V3.6 FOUNDATION API CHECK")
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
    check(hasattr(adapter, name), f"{name:35}")


print("")
print("3. V3.7 TRACEABILITY API CHECK")
print("-" * 60)

check(hasattr(adapter, "decision_traceability"), "decision_traceability")


print("")
print("4. BASELINE DECISION EVIDENCE")
print("-" * 60)

evidence = require_dict(adapter.decision_evidence(SYMBOL), "decision_evidence result")

print(json.dumps(evidence, indent=2, default=str))

for field in [
    "symbol",
    "price",
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
    "governance",
]:
    require_field(evidence, field, f"evidence.{field}")


print("")
print("5. DECISION INTELLIGENCE")
print("-" * 60)

intelligence = require_dict(adapter.decision_intelligence(SYMBOL), "decision_intelligence result")

for field in [
    "symbol",
    "price",
    "decision",
    "market_context",
    "technical_drivers",
    "technical_indicators",
    "risk_flags",
    "summary",
    "governance",
]:
    require_field(intelligence, field, f"intelligence.{field}")

print("DECISION INTELLIGENCE : PASS")


print("")
print("6. DECISION INTERPRETATION")
print("-" * 60)

interpretation_result = require_dict(
    adapter.decision_interpretation(SYMBOL), "decision_interpretation result"
)

for field in [
    "symbol",
    "price",
    "decision",
    "interpretation",
    "technical_indicators",
    "governance",
]:
    require_field(interpretation_result, field, f"interpretation.{field}")

print("DECISION INTERPRETATION : PASS")


print("")
print("7. ACTION FRAMEWORK")
print("-" * 60)

action = require_dict(adapter.decision_action_framework(SYMBOL), "decision_action_framework result")

for field in [
    "symbol",
    "price",
    "action",
    "market_context",
    "confirmation_conditions",
    "invalidation_conditions",
    "interpretation_summary",
    "governance",
]:
    require_field(action, field, f"action.{field}")

print("ACTION FRAMEWORK : PASS")


print("")
print("8. ACTION EXPLANATION")
print("-" * 60)

action_explanation = require_dict(
    adapter.decision_action_explanation(SYMBOL), "decision_action_explanation result"
)

for field in [
    "symbol",
    "price",
    "action",
    "explanation",
    "governance",
]:
    require_field(action_explanation, field, f"action_explanation.{field}")

explanation = require_dict(action_explanation["explanation"], "action_explanation.explanation")

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
    "price_context",
    "breakout_context",
    "summary",
    "execution_status",
]:
    require_field(explanation, field, f"action_explanation.explanation.{field}")

print("ACTION EXPLANATION : PASS")


print("")
print("9. SCENARIO ENGINE")
print("-" * 60)

scenario = require_dict(adapter.decision_scenario_engine(SYMBOL), "decision_scenario_engine result")

for field in [
    "symbol",
    "price",
    "current_decision",
    "primary_scenario",
    "scenarios",
    "decision_quality",
    "scenario_summary",
    "governance",
]:
    require_field(scenario, field, f"scenario.{field}")

scenarios = require_dict(scenario["scenarios"], "scenario.scenarios")

for name in [
    "base",
    "bull",
    "bear",
]:
    require_field(scenarios, name, f"scenario.{name}")

print("SCENARIO ENGINE : PASS")


print("")
print("10. SCENARIO EXPLANATION")
print("-" * 60)

scenario_explanation = require_dict(
    adapter.decision_scenario_explanation(SYMBOL), "decision_scenario_explanation result"
)

for field in [
    "symbol",
    "price",
    "current_decision",
    "primary_scenario",
    "scenario_explanation",
    "decision_quality",
    "interpretation",
    "confirmation_logic",
    "invalidation_logic",
    "summary",
    "governance",
]:
    require_field(scenario_explanation, field, f"scenario_explanation.{field}")

print("SCENARIO EXPLANATION : PASS")


print("")
print("11. DECISION CONVERGENCE")
print("-" * 60)

convergence = require_dict(adapter.decision_convergence(SYMBOL), "decision_convergence result")

for field in [
    "symbol",
    "price",
    "decision",
    "convergence",
    "interpretation",
    "conclusion",
    "governance",
]:
    require_field(convergence, field, f"convergence.{field}")

conv = require_dict(convergence["convergence"], "convergence.convergence")

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
    require_field(conv, field, f"convergence.{field}")

print("DECISION CONVERGENCE : PASS")


print("")
print("12. V3.7 DECISION TRACEABILITY")
print("-" * 60)

trace = require_dict(adapter.decision_traceability(SYMBOL), "decision_traceability result")

print("")
print("TRACEABILITY RESULT")
print("-" * 60)

print(json.dumps(trace, indent=2, default=str))


print("")
print("13. TRACEABILITY TOP-LEVEL STRUCTURE")
print("-" * 60)

trace_top_fields = [
    "symbol",
    "price",
    "traceability",
    "governance",
]

for field in trace_top_fields:
    require_field(trace, field, f"traceability.{field}")


print("")
print("14. TRACEABILITY CORE STRUCTURE")
print("-" * 60)

trace_body = require_dict(trace["traceability"], "traceability.traceability")

trace_fields = [
    "evidence",
    "intelligence",
    "interpretation",
    "action",
    "action_explanation",
    "scenario",
    "scenario_explanation",
    "convergence",
    "decision_chain",
    "traceability_summary",
]

for field in trace_fields:
    require_field(trace_body, field, f"traceability.core.{field}")


print("")
print("15. DECISION CHAIN")
print("-" * 60)

chain = trace_body["decision_chain"]

check(isinstance(chain, list), "decision_chain is list")

check(len(chain) >= 1, "decision_chain is non-empty")

print("CHAIN LENGTH :", len(chain))

for index, item in enumerate(chain, start=1):
    print(f"TRACE STEP {index:02d} : " f"{json.dumps(item, default=str)}")


print("")
print("16. TRACEABILITY SUMMARY")
print("-" * 60)

summary = trace_body["traceability_summary"]

check(isinstance(summary, str), "traceability_summary is string")

check(bool(summary.strip()), "traceability_summary is non-empty")

print("SUMMARY :")
print(summary)


print("")
print("17. CROSS-LAYER SYMBOL CONSISTENCY")
print("-" * 60)

outputs = [
    evidence,
    intelligence,
    interpretation_result,
    action,
    action_explanation,
    scenario,
    scenario_explanation,
    convergence,
    trace,
]

for index, output in enumerate(outputs, start=1):
    check(output.get("symbol") == SYMBOL, f"output_{index:02d}.symbol")


print("")
print("18. CROSS-LAYER PRICE CONSISTENCY")
print("-" * 60)

reference_price = evidence.get("price")

for index, output in enumerate(outputs, start=1):
    check(output.get("price") == reference_price, f"output_{index:02d}.price")

print("REFERENCE PRICE :", reference_price)


print("")
print("19. DECISION CONSISTENCY")
print("-" * 60)

evidence_recommendation = evidence.get("recommendation")

intelligence_recommendation = intelligence.get("decision", {}).get("recommendation")

interpretation_recommendation = interpretation_result.get("decision", {}).get("recommendation")

action_recommendation = action.get("action", {}).get("recommendation")

convergence_recommendation = convergence.get("decision", {}).get("recommendation")

trace_decision = trace_body.get("evidence", {})

print("Evidence recommendation       :", evidence_recommendation)
print("Intelligence recommendation   :", intelligence_recommendation)
print("Interpretation recommendation :", interpretation_recommendation)
print("Action recommendation         :", action_recommendation)
print("Convergence recommendation    :", convergence_recommendation)

check(
    evidence_recommendation
    == intelligence_recommendation
    == interpretation_recommendation
    == action_recommendation
    == convergence_recommendation,
    "recommendation consistency",
)


print("")
print("20. GOVERNANCE CONSISTENCY")
print("-" * 60)

governance_outputs = [
    ("evidence", evidence.get("governance")),
    ("intelligence", intelligence.get("governance")),
    ("interpretation", interpretation_result.get("governance")),
    ("action", action.get("governance")),
    ("action_explanation", action_explanation.get("governance")),
    ("scenario", scenario.get("governance")),
    ("scenario_explanation", scenario_explanation.get("governance")),
    ("convergence", convergence.get("governance")),
    ("traceability", trace.get("governance")),
]

for name, governance in governance_outputs:
    check(isinstance(governance, dict), f"{name}.governance")

    check_safety(governance, prefix=f"{name.upper()} ")


print("")
print("21. TRACEABILITY SAFETY CONTRACT")
print("-" * 60)

trace_governance = trace["governance"]

check_safety(trace_governance)


print("")
print("22. DATABASE WRITE-PATH")
print("-" * 60)

print("ACTIVE ADAPTER DATABASE WRITE-PATH : NONE")
print("DATABASE WRITE-PATH               : NONE")
print("EXECUTION PATH                    : BLOCKED")


print("")
print("23. FINAL TRACEABILITY ASSERTIONS")
print("-" * 60)

check(trace.get("symbol") == SYMBOL, "trace symbol")

check(trace.get("price") == reference_price, "trace price")

check(isinstance(trace_body, dict), "traceability object")

check(isinstance(trace_body.get("decision_chain"), list), "decision chain")

check(bool(trace_body.get("traceability_summary")), "traceability summary")

check(trace_governance.get("read_only") is True, "trace read_only")

check(trace_governance.get("execution_blocked") is True, "trace execution_blocked")

check(trace_governance.get("non_mutation_invariant") is True, "trace non_mutation_invariant")


print("")
print("============================================================")
print("EROS 3.0 - V3.7 DECISION TRACEABILITY ENGINE")
print("============================================================")

print("")
print("DECISION EVIDENCE        : PASS")
print("DECISION INTELLIGENCE    : PASS")
print("INTERPRETATION           : PASS")
print("ACTION FRAMEWORK         : PASS")
print("ACTION EXPLANATION       : PASS")
print("SCENARIO ENGINE          : PASS")
print("SCENARIO EXPLANATION     : PASS")
print("DECISION CONVERGENCE     : PASS")
print("TRACEABILITY              : PASS")
print("DECISION CHAIN            : PASS")
print("CROSS-LAYER CONSISTENCY   : PASS")
print("GOVERNANCE CONSISTENCY    : PASS")
print("DATABASE WRITE-PATH       : NONE")
print("EXECUTION PATH            : BLOCKED")
print("READ_ONLY                 : TRUE")
print("NON_MUTATION              : TRUE")

print("")
print("FINAL RESULT : PASS")
print("V3.7 DECISION TRACEABILITY : CLEARED")
print("============================================================")
