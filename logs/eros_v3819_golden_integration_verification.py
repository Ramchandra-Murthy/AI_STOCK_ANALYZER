from services.eros_frontend_adapter import EROSFrontendAdapter

print("=" * 70)
print("EROS 3.0 - V3.8.19 GOLDEN INTEGRATION VERIFICATION")
print("=" * 70)

symbol = "RELIANCE.NS"

adapter = EROSFrontendAdapter()

print("")
print("SYMBOL :", symbol)

# ==============================================================
# 1. TRACEABILITY
# ==============================================================

print("")
print("=" * 70)
print("1. TRACEABILITY")
print("=" * 70)

traceability = adapter.decision_traceability(symbol)

if not isinstance(traceability, dict):
    raise RuntimeError("TRACEABILITY_NOT_DICT")

print("TRACEABILITY : PASS")

# ==============================================================
# 2. DECISION
# ==============================================================

decision = traceability.get("decision", {})

required_decision = [
    "stance",
    "recommendation",
    "classification",
    "confidence",
    "risk",
    "decision_quality",
]

for key in required_decision:

    if key not in decision:
        raise RuntimeError(f"DECISION_FIELD_MISSING: {key}")

print("DECISION CONTRACT : PASS")

print("DECISION :", decision)

# ==============================================================
# 3. INTERPRETATION
# ==============================================================

interpretation = traceability.get("interpretation", {})

required_interpretation = [
    "market_condition",
    "price_context",
    "breakout_context",
    "decision_quality",
]

for key in required_interpretation:

    if key not in interpretation:
        raise RuntimeError(f"INTERPRETATION_FIELD_MISSING: {key}")

print("INTERPRETATION CONTRACT : PASS")

# ==============================================================
# 4. TRACEABILITY STAGES
# ==============================================================

trace = traceability.get("trace", {})

stages = [
    "stage_1_evidence",
    "stage_2_intelligence",
    "stage_3_interpretation",
    "stage_4_action_framework",
    "stage_5_action_explanation",
    "stage_6_scenario_engine",
    "stage_7_scenario_explanation",
    "stage_8_convergence",
]

available = 0

for stage in stages:

    block = trace.get(stage)

    if not isinstance(block, dict):
        raise RuntimeError(f"TRACE_STAGE_INVALID: {stage}")

    if block.get("status") != "AVAILABLE":
        raise RuntimeError(f"TRACE_STAGE_UNAVAILABLE: {stage}")

    print(f"{stage} : " f"{block.get('source')} : " f"{block.get('status')}")

    available += 1

if available != 8:
    raise RuntimeError("TRACEABILITY_STAGE_COUNT_FAILURE")

print("")
print("TRACEABILITY : 8 / 8 PASS")

# ==============================================================
# 5. CONCLUSION
# ==============================================================

conclusion = traceability.get("conclusion")

if not conclusion:
    raise RuntimeError("CONCLUSION_NOT_AVAILABLE")

print("")
print("CONCLUSION : PASS")
print(conclusion)

# ==============================================================
# 6. GOVERNANCE
# ==============================================================

governance = traceability.get("governance", {})

required_governance = {
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

for key, expected in required_governance.items():

    actual = governance.get(key)

    if actual != expected:

        raise RuntimeError(f"GOVERNANCE_FAILURE: " f"{key}={actual}, expected={expected}")

print("")
print("GOVERNANCE CONTRACT : PASS")

# ==============================================================
# 7. FINAL STATUS
# ==============================================================

print("")
print("=" * 70)
print("V3.8.19 GOLDEN INTEGRATION STATUS : PASS")
print("=" * 70)

print("")
print("EROS DECISION PIPELINE : PASS")
print("FRONTEND ADAPTER        : PASS")
print("TRACEABILITY            : PASS")
print("TRACE STAGES            : 8 / 8")
print("CONCLUSION              : PASS")
print("GOVERNANCE              : PASS")
print("READ ONLY               : TRUE")
print("EXECUTION BLOCKED       : TRUE")

print("")
print("=" * 70)
print("SAFETY")
print("=" * 70)
print("NO SOURCE PATCH")
print("NO DATABASE WRITE")
print("NO BROKER CALL")
print("NO ORDER CREATION")
print("NO PORTFOLIO MUTATION")
print("NO GIT OPERATION")

print("")
print("=" * 70)
print("V3.8.19 GOLDEN INTEGRATION VERIFICATION COMPLETE")
print("=" * 70)
