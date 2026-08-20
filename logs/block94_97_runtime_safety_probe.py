import importlib
import inspect
import pprint

modules = {
    94: "services.quantitative.block94_portfolio_stress_scenario_engine",
    95: "services.quantitative.block95_stress_evidence_gate",
    96: "services.quantitative.block96_stress_decision_gate",
    97: "services.quantitative.block97_stress_readiness_gate",
}

print("=" * 90)
print("EROS 3.0 - BLOCK 94-97 RUNTIME SAFETY RETURN PROBE")
print("=" * 90)

# Synthetic data deliberately kept simple.
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

print()
print("SYNTHETIC INPUT CREATED")
print("Portfolio value:", valuation["portfolio_value"])
print("Positions:", len(positions))
print("Scenarios:", len(scenarios))

# ------------------------------------------------------------------
# BLOCK 94
# ------------------------------------------------------------------

print()
print("=" * 90)
print("BLOCK 94 RUNTIME RETURN")
print("=" * 90)

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

    print("TYPE:", type(r94))
    print("KEYS:", list(r94.keys()))
    pprint.pprint(r94, width=150, sort_dicts=False)

except Exception as exc:
    r94 = {}
    print("ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------------
# BLOCK 95
# ------------------------------------------------------------------

print()
print("=" * 90)
print("BLOCK 95 RUNTIME RETURN")
print("=" * 90)

try:
    m95 = importlib.import_module(modules[95])
    c95 = m95.EROSBlock95StressEvidenceGate()

    r95 = c95.certify(
        stress_certificate=r94,
        policy=policy,
    )

    print("TYPE:", type(r95))
    print("KEYS:", list(r95.keys()))
    pprint.pprint(r95, width=150, sort_dicts=False)

except Exception as exc:
    r95 = {}
    print("ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------------
# BLOCK 96
# ------------------------------------------------------------------

print()
print("=" * 90)
print("BLOCK 96 RUNTIME RETURN")
print("=" * 90)

try:
    m96 = importlib.import_module(modules[96])
    c96 = m96.EROSBlock96StressDecisionGate()

    r96 = c96.decide(
        stress_gate=r95,
        policy=policy,
    )

    print("TYPE:", type(r96))
    print("KEYS:", list(r96.keys()))
    pprint.pprint(r96, width=150, sort_dicts=False)

except Exception as exc:
    r96 = {}
    print("ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------------
# BLOCK 97
# ------------------------------------------------------------------

print()
print("=" * 90)
print("BLOCK 97 RUNTIME RETURN")
print("=" * 90)

try:
    m97 = importlib.import_module(modules[97])
    c97 = m97.EROSBlock97StressReadinessGate()

    r97 = c97.evaluate(
        decision=r96,
    )

    print("TYPE:", type(r97))
    print("KEYS:", list(r97.keys()))
    pprint.pprint(r97, width=150, sort_dicts=False)

except Exception as exc:
    r97 = {}
    print("ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------------
# SAFETY MATRIX
# ------------------------------------------------------------------

print()
print("=" * 90)
print("ACTUAL RUNTIME SAFETY MATRIX")
print("=" * 90)

results = {
    94: r94,
    95: r95,
    96: r96,
    97: r97,
}

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

for block_id, result in results.items():

    print()
    print(f"BLOCK {block_id}")

    for field in fields:
        print(
            f"  {field:28} : "
            f"{result.get(field, '<ABSENT>')!r}"
        )

print()
print("=" * 90)
print("RUNTIME SAFETY PROBE COMPLETE")
print("=" * 90)
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print("=" * 90)
