from services.quantitative.block94_portfolio_stress_scenario_engine import (
    EROSBlock94PortfolioStressScenarioEngine,
)
from services.quantitative.block95_stress_evidence_gate import EROSBlock95StressEvidenceGate
from services.quantitative.block96_stress_decision_gate import EROSBlock96StressDecisionGate
from services.quantitative.block97_stress_readiness_gate import EROSBlock97StressReadinessGate
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
print("EROS 3.0 - BLOCK 94-101 RETURN VALUE SAFETY TEST")
print("=" * 80)

valuation = {"status": "CERTIFIED", "portfolio_value": 1_000_000.0}

performance = {"status": "CERTIFIED", "return_pct": 8.5}

risk = {"status": "CERTIFIED", "risk_score": 20}

positions = [
    {"symbol": "RELIANCE", "quantity": 100, "price": 2800},
    {"symbol": "TCS", "quantity": 50, "price": 3500},
]

scenarios = [{"name": "market_shock", "price_shock_pct": -10}]

print()
print("SYNTHETIC INPUT CREATED")
print("Portfolio:", valuation["portfolio_value"])
print("Positions :", len(positions))
print("Scenarios :", len(scenarios))

results = {}

print()
print("BLOCK 94")

b94 = EROSBlock94PortfolioStressScenarioEngine()
r94 = b94.certify(
    valuation=valuation,
    performance=performance,
    risk=risk,
    positions=positions,
    scenarios=scenarios,
)
results[94] = r94
print(r94)

print()
print("BLOCK 95")

b95 = EROSBlock95StressEvidenceGate()
r95 = b95.certify(stress_certificate=r94)
results[95] = r95
print(r95)

print()
print("BLOCK 96")

b96 = EROSBlock96StressDecisionGate()
r96 = b96.certify(stress_gate=r95)
results[96] = r96
print(r96)

print()
print("BLOCK 97")

b97 = EROSBlock97StressReadinessGate()
r97 = b97.certify(decision=r96)
results[97] = r97
print(r97)

print()
print("BLOCK 98")

b98 = EROSBlock98ExecutionGovernanceBridge()
r98 = b98.certify(decision=r97)
results[98] = r98
print(r98)

print()
print("BLOCK 99")

b99 = EROSBlock99ExecutionIntentAuthorizationGate()
r99 = b99.certify(governance=r98)
results[99] = r99
print(r99)

print()
print("BLOCK 100")

b100 = EROSBlock100PaperExecutionFillGate()
r100 = b100.certify(intent=r99, fill_ratio=0.0)
results[100] = r100
print(r100)

print()
print("BLOCK 101")

b101 = EROSBlock101ExecutionEvidenceReconciliationGate()
r101 = b101.certify(execution=r100)
results[101] = r101
print(r101)

print()
print("=" * 80)
print("STANDARD SAFETY FIELD CHECK")
print("=" * 80)

required = [
    "execution_blocked",
    "non_mutation_invariant",
    "broker_submission",
    "live_order_submission",
]

for block, result in results.items():

    print()
    print(f"BLOCK {block}")

    for key in required:
        value = result.get(key, "<ABSENT>")
        print(f"{key:28}: {value!r}")

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print("=" * 80)
