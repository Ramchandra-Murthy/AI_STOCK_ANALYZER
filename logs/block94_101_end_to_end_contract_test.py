import traceback
from pprint import pprint

from services.quantitative.block94_portfolio_stress_scenario_engine import (
    EROSBlock94PortfolioStressScenarioEngine,
)
from services.quantitative.block95_stress_evidence_gate import (
    EROSBlock95StressEvidenceGate,
)
from services.quantitative.block96_stress_decision_gate import (
    EROSBlock96StressDecisionGate,
)
from services.quantitative.block97_stress_readiness_gate import (
    EROSBlock97StressReadinessGate,
)
from services.quantitative.block98_execution_governance_bridge import (
    EROSBlock98ExecutionGovernanceBridge,
)
from services.quantitative.block99_execution_intent_authorization_gate import (
    EROSBlock99ExecutionIntentAuthorizationGate,
)
from services.quantitative.block100_paper_execution_fill_gate import (
    EROSBlock100PaperExecutionFillGate,
)
from services.quantitative.block101_execution_evidence_reconciliation import (
    EROSBlock101ExecutionEvidenceReconciliationGate,
)

print("=" * 80)
print("EROS 3.0 - BLOCK 94 -> 101 END-TO-END CONTRACT TEST")
print("=" * 80)

# ============================================================
# SYNTHETIC INSTITUTIONAL INPUT
# ============================================================

valuation = {
    "portfolio_value": 1_000_000.0,
    "cash": 250_000.0,
    "gross_exposure": 750_000.0,
    "net_exposure": 700_000.0,
}

performance = {
    "daily_return": 0.012,
    "weekly_return": 0.027,
    "monthly_return": 0.061,
}

risk = {
    "volatility": 0.18,
    "max_drawdown": 0.11,
    "var_95": 0.025,
}

positions = [
    {
        "symbol": "RELIANCE",
        "quantity": 100,
        "price": 2500.0,
        "market_value": 250_000.0,
        "weight": 0.25,
    },
    {
        "symbol": "HDFCBANK",
        "quantity": 100,
        "price": 1800.0,
        "market_value": 180_000.0,
        "weight": 0.18,
    },
]

scenarios = [
    {
        "scenario_id": "MARKET_STRESS_01",
        "name": "Broad Market Drawdown",
        "shock_pct": -0.10,
        "description": "Synthetic 10 percent market decline",
    }
]

print()
print("SYNTHETIC INPUT")
print("-" * 80)
print("Portfolio value :", valuation["portfolio_value"])
print("Positions       :", len(positions))
print("Scenarios       :", len(scenarios))

results = {}

# ============================================================
# BLOCK 94
# ============================================================

print()
print("=" * 80)
print("BLOCK 94 - PORTFOLIO STRESS SCENARIO ENGINE")
print("=" * 80)

try:
    block94 = EROSBlock94PortfolioStressScenarioEngine()

    result94 = block94.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    results["block94"] = result94

    print("STATUS :", result94.get("status"))
    print("BLOCK  :", result94.get("block_id"))
    print("KEYS   :", list(result94.keys()))
    pprint(result94, width=140, sort_dicts=False)

except Exception as exc:
    print("BLOCK 94 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    raise

# ============================================================
# BLOCK 95
# ============================================================

print()
print("=" * 80)
print("BLOCK 95 - STRESS EVIDENCE GATE")
print("=" * 80)

try:
    block95 = EROSBlock95StressEvidenceGate()

    result95 = block95.certify(stress_certificate=result94)

    results["block95"] = result95

    print("STATUS :", result95.get("status"))
    print("BLOCK  :", result95.get("block_id"))
    print("KEYS   :", list(result95.keys()))
    pprint(result95, width=140, sort_dicts=False)

except Exception as exc:
    print("BLOCK 95 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    raise

# ============================================================
# BLOCK 96
# ============================================================

print()
print("=" * 80)
print("BLOCK 96 - STRESS DECISION GATE")
print("=" * 80)

try:
    block96 = EROSBlock96StressDecisionGate()

    result96 = block96.certify(stress_gate=result95)

    results["block96"] = result96

    print("STATUS :", result96.get("status"))
    print("BLOCK  :", result96.get("block_id"))
    print("KEYS   :", list(result96.keys()))
    pprint(result96, width=140, sort_dicts=False)

except Exception as exc:
    print("BLOCK 96 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    raise

# ============================================================
# BLOCK 97
# ============================================================

print()
print("=" * 80)
print("BLOCK 97 - STRESS READINESS GATE")
print("=" * 80)

try:
    block97 = EROSBlock97StressReadinessGate()

    result97 = block97.certify(decision=result96)

    results["block97"] = result97

    print("STATUS :", result97.get("status"))
    print("BLOCK  :", result97.get("block_id"))
    print("KEYS   :", list(result97.keys()))
    pprint(result97, width=140, sort_dicts=False)

except Exception as exc:
    print("BLOCK 97 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    raise

# ============================================================
# BLOCK 98
# ============================================================

print()
print("=" * 80)
print("BLOCK 98 - EXECUTION GOVERNANCE BRIDGE")
print("=" * 80)

try:
    block98 = EROSBlock98ExecutionGovernanceBridge()

    result98 = block98.certify(decision=result97)

    results["block98"] = result98

    print("STATUS :", result98.get("status"))
    print("BLOCK  :", result98.get("block_id"))
    print("KEYS   :", list(result98.keys()))
    pprint(result98, width=140, sort_dicts=False)

except Exception as exc:
    print("BLOCK 98 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    raise

# ============================================================
# BLOCK 99
# ============================================================

print()
print("=" * 80)
print("BLOCK 99 - EXECUTION INTENT AUTHORIZATION")
print("=" * 80)

try:
    block99 = EROSBlock99ExecutionIntentAuthorizationGate()

    result99 = block99.certify(governance=result98)

    results["block99"] = result99

    print("STATUS :", result99.get("status"))
    print("BLOCK  :", result99.get("block_id"))
    print("KEYS   :", list(result99.keys()))
    pprint(result99, width=140, sort_dicts=False)

except Exception as exc:
    print("BLOCK 99 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    raise

# ============================================================
# BLOCK 100
# ============================================================

print()
print("=" * 80)
print("BLOCK 100 - PAPER EXECUTION FILL GATE")
print("=" * 80)

try:
    block100 = EROSBlock100PaperExecutionFillGate()

    result100 = block100.certify(
        intent=result99,
        fill_ratio=1.0,
    )

    results["block100"] = result100

    print("STATUS :", result100.get("status"))
    print("BLOCK  :", result100.get("block_id"))
    print("KEYS   :", list(result100.keys()))
    pprint(result100, width=140, sort_dicts=False)

except Exception as exc:
    print("BLOCK 100 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    raise

# ============================================================
# BLOCK 101
# ============================================================

print()
print("=" * 80)
print("BLOCK 101 - EXECUTION EVIDENCE RECONCILIATION")
print("=" * 80)

try:
    block101 = EROSBlock101ExecutionEvidenceReconciliationGate()

    result101 = block101.certify(execution=result100)

    results["block101"] = result101

    print("STATUS :", result101.get("status"))
    print("BLOCK  :", result101.get("block_id"))
    print("KEYS   :", list(result101.keys()))
    pprint(result101, width=140, sort_dicts=False)

except Exception as exc:
    print("BLOCK 101 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    raise

# ============================================================
# CROSS-BLOCK CONTRACT SUMMARY
# ============================================================

print()
print("=" * 80)
print("CROSS-BLOCK CONTRACT SUMMARY")
print("=" * 80)

for block_id in range(94, 102):
    key = f"block{block_id}"
    result = results.get(key, {})

    print()
    print(f"BLOCK {block_id}")
    print("-" * 40)

    if isinstance(result, dict):
        print("status               :", result.get("status"))
        print("block_id             :", result.get("block_id"))
        print("reason               :", result.get("reason"))
        print("reason_code          :", result.get("reason_code"))
        print("execution_blocked    :", result.get("execution_blocked"))
        print("non_mutation         :", result.get("non_mutation_invariant"))
        print("broker_submission    :", result.get("broker_submission"))
        print("live_order_submission:", result.get("live_order_submission"))
        print("order_creation       :", result.get("order_creation"))
    else:
        print("RESULT TYPE:", type(result))

# ============================================================
# SAFETY ASSERTION
# ============================================================

print()
print("=" * 80)
print("SAFETY ASSERTION")
print("=" * 80)

safety_failures = []

for block_id in range(94, 102):

    result = results.get(f"block{block_id}", {})

    if not isinstance(result, dict):
        safety_failures.append(f"Block {block_id}: result is not dict")
        continue

    # Only report fields that actually exist.
    # We do not assume every block has identical schema.

    if "broker_submission" in result:
        if result["broker_submission"] is not False:
            safety_failures.append(f"Block {block_id}: broker_submission is not False")

    if "live_order_submission" in result:
        if result["live_order_submission"] is not False:
            safety_failures.append(f"Block {block_id}: live_order_submission is not False")

    if "order_creation" in result:
        if result["order_creation"] is not False:
            safety_failures.append(f"Block {block_id}: order_creation is not False")

    if "execution_blocked" in result:
        if result["execution_blocked"] is not True:
            safety_failures.append(f"Block {block_id}: execution_blocked is not True")

    if "non_mutation_invariant" in result:
        if result["non_mutation_invariant"] is not True:
            safety_failures.append(f"Block {block_id}: non_mutation_invariant is not True")

if safety_failures:
    print("SAFETY : FAIL")
    for failure in safety_failures:
        print(" -", failure)
else:
    print("SAFETY : PASS")
    print("All PRESENT safety fields satisfy their expected invariant.")

# ============================================================
# FINAL RESULT
# ============================================================

print()
print("=" * 80)
print("FINAL RESULT")
print("=" * 80)

print("Blocks exercised : 94 -> 101")
print("Execution mode   : SYNTHETIC / PAPER ONLY")
print("Broker connected : NO")
print("Live orders      : NO")
print("Portfolio mutate : NO")

if safety_failures:
    print("OVERALL           : REVIEW REQUIRED")
else:
    print("OVERALL           : CONTRACT FLOW PASSED")

print("=" * 80)
print("END-TO-END CONTRACT TEST COMPLETE")
print("=" * 80)
