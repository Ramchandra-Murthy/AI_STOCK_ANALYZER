import importlib
import pprint

modules = {
    94: "services.quantitative.block94_portfolio_stress_scenario_engine",
    95: "services.quantitative.block95_stress_evidence_gate",
    96: "services.quantitative.block96_stress_decision_gate",
    97: "services.quantitative.block97_stress_readiness_gate",
}

print("=" * 100)
print("EROS 3.0 - BLOCK 94-97 CURRENT RUNTIME SAFETY VERIFICATION")
print("=" * 100)

valuation = {
    "valuation_id": "VAL-TEST-001",
    "portfolio_value": 1_000_000.0,
}

performance = {
    "performance_id": "PERF-TEST-001",
    "return_pct": 0.05,
}

risk = {
    "risk_certificate_id": "RISK-TEST-001",
    "risk_status": "PASS",
}

positions = [
    {
        "symbol": "RELIANCE.NS",
        "quantity": 100,
        "price": 2500.0,
        "market_value": 250000.0,
    },
    {
        "symbol": "TCS.NS",
        "quantity": 100,
        "price": 3500.0,
        "market_value": 350000.0,
    },
]

scenarios = [
    {
        "scenario_id": "TEST-STRESS-001",
        "name": "Synthetic Market Stress",
        "shock_pct": -0.10,
    }
]

policy = {}

results = {}

# ================================================================
# BLOCK 94
# ================================================================

print()
print("=" * 80)
print("BLOCK 94")
print("=" * 80)

try:
    m94 = importlib.import_module(modules[94])
    c94 = m94.EROSBlock94PortfolioStressScenarioEngine()

    results[94] = c94.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    pprint.pprint(results[94], width=150, sort_dicts=False)

except Exception as exc:
    results[94] = {}
    print("ERROR:", type(exc).__name__, str(exc))

# ================================================================
# BLOCK 95
# ================================================================

print()
print("=" * 80)
print("BLOCK 95")
print("=" * 80)

try:
    m95 = importlib.import_module(modules[95])
    c95 = m95.EROSBlock95StressEvidenceGate()

    results[95] = c95.certify(
        stress_certificate=results[94],
        policy=policy,
    )

    pprint.pprint(results[95], width=150, sort_dicts=False)

except Exception as exc:
    results[95] = {}
    print("ERROR:", type(exc).__name__, str(exc))

# ================================================================
# BLOCK 96
# ================================================================

print()
print("=" * 80)
print("BLOCK 96")
print("=" * 80)

try:
    m96 = importlib.import_module(modules[96])
    c96 = m96.EROSBlock96StressDecisionGate()

    results[96] = c96.decide(
        stress_gate=results[95],
        policy=policy,
    )

    pprint.pprint(results[96], width=150, sort_dicts=False)

except Exception as exc:
    results[96] = {}
    print("ERROR:", type(exc).__name__, str(exc))

# ================================================================
# BLOCK 97
# ================================================================

print()
print("=" * 80)
print("BLOCK 97")
print("=" * 80)

try:
    m97 = importlib.import_module(modules[97])
    c97 = m97.EROSBlock97StressReadinessGate()

    results[97] = c97.evaluate(
        decision=results[96],
    )

    pprint.pprint(results[97], width=150, sort_dicts=False)

except Exception as exc:
    results[97] = {}
    print("ERROR:", type(exc).__name__, str(exc))

# ================================================================
# SAFETY MATRIX
# ================================================================

print()
print("=" * 100)
print("ACTUAL RUNTIME SAFETY MATRIX")
print("=" * 100)

fields = [
    "execution_blocked",
    "non_mutation_invariant",
    "broker_submission",
    "live_order_submission",
    "portfolio_mutation",
    "valuation_mutation",
    "performance_mutation",
    "risk_mutation",
    "optimization",
    "order_creation",
]

expected = {
    "execution_blocked": True,
    "non_mutation_invariant": True,
    "broker_submission": False,
    "live_order_submission": False,
}

overall = True

for block_id, result in results.items():

    print()
    print(f"BLOCK {block_id}")
    print("-" * 60)

    for field in fields:

        value = result.get(field, "<ABSENT>")

        print(f"{field:28} : {value!r}")

        if field in expected and value != expected[field]:
            overall = False

print()
print("=" * 100)

if overall:
    print("SAFETY : PASS")
    print("All standardized safety fields satisfy the expected contract.")
else:
    print("SAFETY : FAIL")
    print()
    print("Missing or incorrect standardized safety fields remain.")
    print("DO NOT NORMALIZE BLINDLY.")
    print("Use the BLOCKED RETURN TRACE to repair only the actual")
    print("return dictionaries that require normalization.")

print("=" * 100)
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO PORTFOLIO MUTATION")
print("NO VALUATION MUTATION")
print("=" * 100)
