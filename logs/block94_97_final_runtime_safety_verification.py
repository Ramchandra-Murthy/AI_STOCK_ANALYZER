import importlib
import pprint

modules = {
    94: "services.quantitative.block94_portfolio_stress_scenario_engine",
    95: "services.quantitative.block95_stress_evidence_gate",
    96: "services.quantitative.block96_stress_decision_gate",
    97: "services.quantitative.block97_stress_readiness_gate",
}

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

print("=" * 100)
print("EROS 3.0 - BLOCK 94-97 FINAL RUNTIME SAFETY VERIFICATION")
print("=" * 100)

print()
print("SYNTHETIC INPUT")
print("Portfolio value :", valuation["portfolio_value"])
print("Positions       :", len(positions))
print("Scenarios       :", len(scenarios))

results = {}

# ------------------------------------------------------------
# BLOCK 94
# ------------------------------------------------------------

print()
print("=" * 100)
print("BLOCK 94")
print("=" * 100)

try:
    m94 = importlib.import_module(modules[94])
    c94 = m94.EROSBlock94PortfolioStressScenarioEngine()

    r94 = c94.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    results[94] = r94
    pprint.pprint(r94, width=150, sort_dicts=False)

except Exception as exc:
    results[94] = {}
    print("ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------
# BLOCK 95
# ------------------------------------------------------------

print()
print("=" * 100)
print("BLOCK 95")
print("=" * 100)

try:
    m95 = importlib.import_module(modules[95])
    c95 = m95.EROSBlock95StressEvidenceGate()

    r95 = c95.certify(
        stress_certificate=results[94],
        policy=policy,
    )

    results[95] = r95
    pprint.pprint(r95, width=150, sort_dicts=False)

except Exception as exc:
    results[95] = {}
    print("ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------
# BLOCK 96
# ------------------------------------------------------------

print()
print("=" * 100)
print("BLOCK 96")
print("=" * 100)

try:
    m96 = importlib.import_module(modules[96])
    c96 = m96.EROSBlock96StressDecisionGate()

    r96 = c96.decide(
        stress_gate=results[95],
        policy=policy,
    )

    results[96] = r96
    pprint.pprint(r96, width=150, sort_dicts=False)

except Exception as exc:
    results[96] = {}
    print("ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------
# BLOCK 97
# ------------------------------------------------------------

print()
print("=" * 100)
print("BLOCK 97")
print("=" * 100)

try:
    m97 = importlib.import_module(modules[97])
    c97 = m97.EROSBlock97StressReadinessGate()

    r97 = c97.evaluate(
        decision=results[96],
    )

    results[97] = r97
    pprint.pprint(r97, width=150, sort_dicts=False)

except Exception as exc:
    results[97] = {}
    print("ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------
# FINAL SAFETY MATRIX
# ------------------------------------------------------------

fields = [
    "execution_blocked",
    "non_mutation_invariant",
    "broker_submission",
    "live_order_submission",
]

print()
print("=" * 100)
print("FINAL RUNTIME SAFETY MATRIX")
print("=" * 100)

overall_pass = True

for block_id in [94, 95, 96, 97]:

    result = results[block_id]

    print()
    print(f"BLOCK {block_id}")
    print("-" * 60)

    for field in fields:
        value = result.get(field, "<ABSENT>")
        print(f"{field:28} : {value!r}")

    expected = {
        "execution_blocked": True,
        "non_mutation_invariant": True,
        "broker_submission": False,
        "live_order_submission": False,
    }

    for field, expected_value in expected.items():
        if result.get(field) != expected_value:
            overall_pass = False

print()
print("=" * 100)

if overall_pass:
    print("SAFETY : PASS")
    print()
    print("ALL BLOCKS 94-97 SATISFY THE STANDARDIZED SAFETY CONTRACT.")
    print("execution_blocked       = True")
    print("non_mutation_invariant  = True")
    print("broker_submission       = False")
    print("live_order_submission   = False")
else:
    print("SAFETY : FAIL")
    print()
    print("One or more standardized safety fields are still incorrect.")

print("=" * 100)
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO PORTFOLIO MUTATION")
print("NO VALUATION MUTATION")
print("=" * 100)
