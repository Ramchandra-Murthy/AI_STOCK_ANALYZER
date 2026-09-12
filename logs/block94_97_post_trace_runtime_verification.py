import importlib
import subprocess

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

results = {}
output = []


def p(text=""):
    print(text)
    output.append(str(text))


p("=" * 100)
p("EROS 3.0 - BLOCK 94-97 POST-RETURN-PATH RUNTIME SAFETY VERIFICATION")
p("=" * 100)

p()
p("SYNTHETIC INPUT")
p(f"Portfolio value : {valuation['portfolio_value']}")
p(f"Positions       : {len(positions)}")
p(f"Scenarios       : {len(scenarios)}")

# ------------------------------------------------------------
# BLOCK 94
# ------------------------------------------------------------

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
except Exception as exc:
    results[94] = {}
    p(f"BLOCK 94 ERROR: {type(exc).__name__}: {exc}")

# ------------------------------------------------------------
# BLOCK 95
# ------------------------------------------------------------

try:
    m95 = importlib.import_module(modules[95])
    c95 = m95.EROSBlock95StressEvidenceGate()

    results[95] = c95.certify(
        stress_certificate=results[94],
        policy=policy,
    )
except Exception as exc:
    results[95] = {}
    p(f"BLOCK 95 ERROR: {type(exc).__name__}: {exc}")

# ------------------------------------------------------------
# BLOCK 96
# ------------------------------------------------------------

try:
    m96 = importlib.import_module(modules[96])
    c96 = m96.EROSBlock96StressDecisionGate()

    results[96] = c96.decide(
        stress_gate=results[95],
        policy=policy,
    )
except Exception as exc:
    results[96] = {}
    p(f"BLOCK 96 ERROR: {type(exc).__name__}: {exc}")

# ------------------------------------------------------------
# BLOCK 97
# ------------------------------------------------------------

try:
    m97 = importlib.import_module(modules[97])
    c97 = m97.EROSBlock97StressReadinessGate()

    results[97] = c97.evaluate(
        decision=results[96],
    )
except Exception as exc:
    results[97] = {}
    p(f"BLOCK 97 ERROR: {type(exc).__name__}: {exc}")

# ------------------------------------------------------------
# COMPLETE SAFETY MATRIX
# ------------------------------------------------------------

fields = [
    "status",
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

p()
p("=" * 100)
p("COMPLETE RUNTIME SAFETY MATRIX")
p("=" * 100)

failures = []

for block_id in [94, 95, 96, 97]:

    result = results[block_id]

    p()
    p(f"BLOCK {block_id}")
    p("-" * 60)

    for field in fields:
        value = result.get(field, "<ABSENT>")
        p(f"{field:28} : {value!r}")

    if result.get("execution_blocked") is not True:
        failures.append(f"Block {block_id}: execution_blocked != True")

    if result.get("non_mutation_invariant") is not True:
        failures.append(f"Block {block_id}: non_mutation_invariant != True")

    if result.get("broker_submission") is not False:
        failures.append(f"Block {block_id}: broker_submission != False")

    if result.get("live_order_submission") is not False:
        failures.append(f"Block {block_id}: live_order_submission != False")

p()
p("=" * 100)
p("FINAL SAFETY RESULT")
p("=" * 100)

if failures:
    p("SAFETY : FAIL")
    p()
    for failure in failures:
        p(" - " + failure)
else:
    p("SAFETY : PASS")
    p()
    p("All Blocks 94-97 expose the required runtime safety contract.")

p()
p("=" * 100)
p("VERIFICATION COMPLETE")
p("=" * 100)
p("NO BROKER")
p("NO LIVE EXECUTION")
p("NO ORDER CREATION")
p("NO PORTFOLIO MUTATION")
p("NO VALUATION MUTATION")
p("=" * 100)

# Copy entire result to clipboard.
clipboard_text = "\n".join(output)

try:
    subprocess.run(
        ["clip.exe"],
        input=clipboard_text,
        text=True,
        check=True,
    )
    print()
    print("=" * 100)
    print("CLIPBOARD : PASS")
    print("Complete runtime verification copied to clipboard.")
    print("Paste directly into ChatGPT with CTRL+V.")
    print("=" * 100)
except Exception as exc:
    print("CLIPBOARD : FAIL")
    print(type(exc).__name__, str(exc))
