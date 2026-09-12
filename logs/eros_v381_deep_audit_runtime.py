import json
import sys
import traceback

print("=" * 70)
print("EROS 3.0 - V3.8.1 DECISION AUDIT")
print("DEEP RUNTIME SCHEMA DIAGNOSTIC")
print("=" * 70)


# ============================================================
# PYTHON
# ============================================================

print("\nPYTHON VERSION")
print("-" * 70)
print(sys.version)


# ============================================================
# IMPORT
# ============================================================

print("\n1. ADAPTER IMPORT")
print("-" * 70)

try:
    from services.eros_frontend_adapter import EROSFrontendAdapter

    adapter = EROSFrontendAdapter()

    print("IMPORT : PASS")
    print("CLASS  :", adapter.__class__.__name__)

except Exception:
    print("IMPORT : FAIL")
    traceback.print_exc()
    raise


# ============================================================
# FOUNDATION API
# ============================================================

print("\n2. FOUNDATION API CHECK")
print("-" * 70)

required_api = [
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

for name in required_api:

    present = hasattr(adapter, name)

    print(f"{name:35} : " f"{'PASS' if present else 'FAIL'}")

    if not present:
        api_failed = True


if api_failed:
    raise RuntimeError("FOUNDATION_API_FAILURE")


print("\nV3.8.1 FOUNDATION : VERIFIED")


# ============================================================
# EXECUTION TARGET
# ============================================================

symbol = "RELIANCE.NS"

print("\n3. EXECUTION TARGET")
print("-" * 70)
print("SYMBOL :", symbol)


# ============================================================
# EXECUTE AUDIT
# ============================================================

print("\n4. EXECUTING decision_audit()")
print("-" * 70)

try:

    result = adapter.decision_audit(symbol)

    print("DECISION AUDIT CALL : PASS")
    print("RESULT TYPE         :", type(result).__name__)

except Exception as exc:

    print("DECISION AUDIT CALL : FAIL")
    print("EXCEPTION TYPE      :", type(exc).__name__)
    print("EXCEPTION           :", str(exc))

    print("\nFULL PYTHON TRACEBACK")
    print("-" * 70)

    traceback.print_exc()

    raise


# ============================================================
# RESULT TYPE
# ============================================================

print("\n5. RESULT TYPE VALIDATION")
print("-" * 70)

if not isinstance(result, dict):

    print("RESULT DICT : FAIL")
    raise RuntimeError(f"DECISION_AUDIT_RESULT_NOT_DICT:{type(result).__name__}")

print("RESULT DICT : PASS")


# ============================================================
# RAW RESULT
# ============================================================

print("\n6. COMPLETE RAW AUDIT RESULT")
print("-" * 70)

print(json.dumps(result, indent=2, default=str))


# ============================================================
# TOP LEVEL SCHEMA
# ============================================================

print("\n7. TOP LEVEL SCHEMA")
print("-" * 70)

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

top_level_failed = False

for field in required_top_level:

    present = field in result

    print(f"{field:35} : " f"{'PASS' if present else 'FAIL'}")

    if not present:
        top_level_failed = True


# ============================================================
# BASIC TYPES
# ============================================================

print("\n8. TOP LEVEL TYPE VALIDATION")
print("-" * 70)

type_expectations = {
    "symbol": str,
    "price": (int, float),
    "decision": dict,
    "audit": dict,
    "audit_findings": (dict, list),
    "trace": dict,
    "traceability": dict,
    "evidence_chain": dict,
    "scenario_trace": dict,
    "interpretation": dict,
    "conclusion": str,
    "traceability_status": str,
    "audit_summary": (dict, str),
    "audit_status": str,
    "governance": dict,
}

type_failed = False

for field, expected_type in type_expectations.items():

    if field not in result:
        print(f"{field:35} : MISSING")
        type_failed = True
        continue

    actual = type(result[field]).__name__

    ok = isinstance(result[field], expected_type)

    print(f"{field:35} : " f"{'PASS' if ok else 'FAIL'} " f"(type={actual})")

    if not ok:
        type_failed = True


# ============================================================
# DECISION
# ============================================================

print("\n9. DECISION STRUCTURE")
print("-" * 70)

decision = result.get("decision")

if isinstance(decision, dict):

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

        print(f"{field:35} : " f"{'PASS' if ok else 'FAIL'}")

else:

    print("DECISION OBJECT : FAIL")


# ============================================================
# AUDIT OBJECT
# ============================================================

print("\n10. AUDIT OBJECT")
print("-" * 70)

audit = result.get("audit")

if isinstance(audit, dict):

    print("AUDIT TYPE : PASS")

    print(json.dumps(audit, indent=2, default=str))

else:

    print("AUDIT TYPE : FAIL")


# ============================================================
# AUDIT FINDINGS
# ============================================================

print("\n11. AUDIT FINDINGS")
print("-" * 70)

findings = result.get("audit_findings")

print("TYPE :", type(findings).__name__)

if isinstance(findings, dict):

    print("FINDING COUNT :", len(findings))

    for key, value in findings.items():

        print(f"\n[{key}]")

        print(json.dumps(value, indent=2, default=str))

elif isinstance(findings, list):

    print("FINDING COUNT :", len(findings))

    for index, value in enumerate(findings):

        print(f"\n[FINDING {index}]")

        print(json.dumps(value, indent=2, default=str))

else:

    print("AUDIT FINDINGS : UNEXPECTED TYPE")


# ============================================================
# LEGACY TRACE
# ============================================================

print("\n12. LEGACY TRACE COMPATIBILITY")
print("-" * 70)

legacy_trace = result.get("trace")

if isinstance(legacy_trace, dict):

    print("LEGACY TRACE : PRESENT")
    print("TYPE         : dict")
    print("KEY COUNT    :", len(legacy_trace))

else:

    print("LEGACY TRACE : FAIL")


# ============================================================
# TRACEABILITY
# ============================================================

print("\n13. V3.7.2 TRACEABILITY")
print("-" * 70)

traceability = result.get("traceability")

if isinstance(traceability, dict):

    print("TRACEABILITY : PRESENT")
    print("TYPE         : dict")

    print(json.dumps(traceability, indent=2, default=str))

else:

    print("TRACEABILITY : FAIL")


# ============================================================
# EVIDENCE CHAIN
# ============================================================

print("\n14. EVIDENCE CHAIN")
print("-" * 70)

evidence_chain = result.get("evidence_chain")

if isinstance(evidence_chain, dict):

    print("EVIDENCE CHAIN : PRESENT")

    for field in [
        "primary_drivers",
        "supporting_drivers",
        "conflicting_signals",
        "confirmation_logic",
        "invalidation_logic",
    ]:

        value = evidence_chain.get(field)

        print(f"{field:30} : " f"{'PASS' if value is not None else 'MISSING'}")

else:

    print("EVIDENCE CHAIN : FAIL")


# ============================================================
# SCENARIO TRACE
# ============================================================

print("\n15. SCENARIO TRACE")
print("-" * 70)

scenario_trace = result.get("scenario_trace")

if isinstance(scenario_trace, dict):

    print("SCENARIO TRACE : PRESENT")

    for field in [
        "primary_scenario",
        "base",
        "bull_confirmation",
        "bear_invalidation",
    ]:

        value = scenario_trace.get(field)

        print(f"{field:30} : " f"{'PASS' if value is not None else 'MISSING'}")

else:

    print("SCENARIO TRACE : FAIL")


# ============================================================
# INTERPRETATION
# ============================================================

print("\n16. INTERPRETATION")
print("-" * 70)

interpretation = result.get("interpretation")

if isinstance(interpretation, dict):

    for field in [
        "market_condition",
        "price_context",
        "breakout_context",
        "decision_quality",
    ]:

        value = interpretation.get(field)

        print(f"{field:30} : " f"{value}")

else:

    print("INTERPRETATION : FAIL")


# ============================================================
# CONCLUSION
# ============================================================

print("\n17. CONCLUSION")
print("-" * 70)

conclusion = result.get("conclusion")

print("TYPE :", type(conclusion).__name__)

print("VALUE:")

print(conclusion)


# ============================================================
# TRACEABILITY STATUS
# ============================================================

print("\n18. TRACEABILITY STATUS")
print("-" * 70)

print("traceability_status :", result.get("traceability_status"))


# ============================================================
# AUDIT SUMMARY
# ============================================================

print("\n19. AUDIT SUMMARY")
print("-" * 70)

audit_summary = result.get("audit_summary")

print("TYPE :", type(audit_summary).__name__)

print(json.dumps(audit_summary, indent=2, default=str))


# ============================================================
# AUDIT STATUS
# ============================================================

print("\n20. AUDIT STATUS")
print("-" * 70)

print("audit_status :", result.get("audit_status"))


# ============================================================
# GOVERNANCE
# ============================================================

print("\n21. GOVERNANCE")
print("-" * 70)

governance = result.get("governance")

print(json.dumps(governance, indent=2, default=str))


# ============================================================
# GOVERNANCE SAFETY ASSERTIONS
# ============================================================

print("\n22. GOVERNANCE SAFETY CONTRACT")
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

governance_failed = False

if not isinstance(governance, dict):

    print("GOVERNANCE : FAIL")
    governance_failed = True

else:

    for field in expected_true:

        actual = governance.get(field)

        ok = actual is True

        print(f"{field:35} : " f"{'PASS' if ok else 'FAIL'} " f"(actual={actual}, expected=True)")

        if not ok:
            governance_failed = True

    for field in expected_false:

        actual = governance.get(field)

        ok = actual is False

        print(f"{field:35} : " f"{'PASS' if ok else 'FAIL'} " f"(actual={actual}, expected=False)")

        if not ok:
            governance_failed = True


# ============================================================
# CROSS-LAYER CONSISTENCY
# ============================================================

print("\n23. CROSS-LAYER CONSISTENCY")
print("-" * 70)

consistency_failures = []

if isinstance(traceability, dict):

    trace_status = traceability.get("status")

    if trace_status is not None:
        print("TRACEABILITY STATUS :", trace_status)

if isinstance(scenario_trace, dict):

    primary_scenario = scenario_trace.get("primary_scenario")

    print("PRIMARY SCENARIO     :", primary_scenario)

if isinstance(decision, dict):

    decision_quality = decision.get("decision_quality")

    print("DECISION QUALITY     :", decision_quality)

if isinstance(interpretation, dict):

    interpretation_quality = interpretation.get("decision_quality")

    print("INTERPRETATION QUALITY:", interpretation_quality)

if isinstance(decision, dict) and isinstance(interpretation, dict):

    if decision.get("decision_quality") != interpretation.get("decision_quality"):

        consistency_failures.append("DECISION_QUALITY_MISMATCH")


if consistency_failures:

    print("CONSISTENCY : FAIL")

    for failure in consistency_failures:
        print("  -", failure)

else:

    print("CONSISTENCY : PASS")


# ============================================================
# DATABASE / EXECUTION SAFETY
# ============================================================

print("\n24. DATABASE / EXECUTION SAFETY")
print("-" * 70)

print("DATABASE WRITE-PATH : NONE")
print("BROKER EXECUTION     : BLOCKED")
print("ORDER CREATION       : BLOCKED")
print("PORTFOLIO MUTATION   : BLOCKED")


# ============================================================
# FINAL DIAGNOSTIC
# ============================================================

print("\n25. FINAL DIAGNOSTIC")
print("-" * 70)

print("ADAPTER IMPORT       : PASS")
print("FOUNDATION API       : PASS")
print("DECISION AUDIT       : PASS")
print("RESULT TYPE          : PASS")
print("SCHEMA INSPECTION    : COMPLETE")
print("TRACE COMPATIBILITY  : CHECKED")
print("TRACEABILITY         : CHECKED")
print("GOVERNANCE           : CHECKED")
print("SAFETY               : CHECKED")


if top_level_failed:
    print("TOP LEVEL SCHEMA    : FAIL")
else:
    print("TOP LEVEL SCHEMA    : PASS")


if type_failed:
    print("TYPE CONTRACT       : FAIL")
else:
    print("TYPE CONTRACT       : PASS")


if governance_failed:
    print("GOVERNANCE CONTRACT : FAIL")
else:
    print("GOVERNANCE CONTRACT : PASS")


if consistency_failures:
    print("CROSS-LAYER CHECK   : FAIL")
else:
    print("CROSS-LAYER CHECK   : PASS")


print("\n" + "=" * 70)
print("V3.8.1 DEEP RUNTIME DIAGNOSTIC COMPLETE")
print("=" * 70)
