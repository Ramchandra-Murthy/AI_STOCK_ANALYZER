import traceback

print("=" * 70)
print("EROS 3.0 - BLOCK 94 -> 101 REAL CONTRACT FLOW TEST")
print("=" * 70)

# ------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------

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

print("IMPORTS : PASS")

# ------------------------------------------------------------
# SYNTHETIC READ-ONLY TEST INPUT
# ------------------------------------------------------------

valuation = {
    "portfolio_value": 1_000_000.0,
    "gross_exposure": 1_000_000.0,
}

performance = {
    "pnl": 25_000.0,
    "return_pct": 2.5,
}

risk = {
    "volatility": 0.18,
    "var": 35_000.0,
}

positions = [
    {
        "symbol": "RELIANCE",
        "quantity": 100,
        "price": 2500.0,
        "market_value": 250_000.0,
    },
    {
        "symbol": "TCS",
        "quantity": 100,
        "price": 3500.0,
        "market_value": 350_000.0,
    },
]

scenarios = [
    {
        "scenario_id": "TEST_DOWNSIDE_01",
        "name": "Synthetic Downside",
        "shock_pct": -0.10,
    }
]

print()
print("SYNTHETIC INPUT : CREATED")
print("Portfolio value :", valuation["portfolio_value"])
print("Positions       :", len(positions))
print("Scenarios       :", len(scenarios))

# ------------------------------------------------------------
# BLOCK 94
# ------------------------------------------------------------

print()
print("=" * 70)
print("BLOCK 94")
print("=" * 70)

b94 = EROSBlock94PortfolioStressScenarioEngine()

try:
    out94 = b94.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    print("BUILD/CERTIFY : PASS")
    print("TYPE          :", type(out94))
    print("STATUS        :", out94.get("status"))
    print("KEYS          :", list(out94.keys()))

except Exception as exc:
    print("BLOCK 94 : FAIL")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    raise SystemExit(1)

# ------------------------------------------------------------
# BLOCK 95
# ------------------------------------------------------------

print()
print("=" * 70)
print("BLOCK 95")
print("=" * 70)

b95 = EROSBlock95StressEvidenceGate()

try:
    out95 = b95.certify(stress_certificate=out94)

    print("CERTIFY : PASS")
    print("TYPE    :", type(out95))
    print("STATUS  :", out95.get("status"))
    print("KEYS    :", list(out95.keys()))

except Exception as exc:
    print("BLOCK 95 : FAIL")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    raise SystemExit(1)

# ------------------------------------------------------------
# BLOCK 96
# ------------------------------------------------------------

print()
print("=" * 70)
print("BLOCK 96")
print("=" * 70)

b96 = EROSBlock96StressDecisionGate()

try:
    out96 = b96.certify(stress_gate=out95)

    print("CERTIFY : PASS")
    print("TYPE    :", type(out96))
    print("STATUS  :", out96.get("status"))
    print("KEYS    :", list(out96.keys()))

except Exception as exc:
    print("BLOCK 96 : FAIL")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    raise SystemExit(1)

# ------------------------------------------------------------
# BLOCK 97
# ------------------------------------------------------------

print()
print("=" * 70)
print("BLOCK 97")
print("=" * 70)

b97 = EROSBlock97StressReadinessGate()

try:
    out97 = b97.certify(decision=out96)

    print("CERTIFY : PASS")
    print("TYPE    :", type(out97))
    print("STATUS  :", out97.get("status"))
    print("KEYS    :", list(out97.keys()))

except Exception as exc:
    print("BLOCK 97 : FAIL")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    raise SystemExit(1)

# ------------------------------------------------------------
# BLOCK 98
# ------------------------------------------------------------

print()
print("=" * 70)
print("BLOCK 98")
print("=" * 70)

b98 = EROSBlock98ExecutionGovernanceBridge()

try:
    out98 = b98.certify(decision=out97)

    print("CERTIFY : PASS")
    print("TYPE    :", type(out98))
    print("STATUS  :", out98.get("status"))
    print("KEYS    :", list(out98.keys()))

except Exception as exc:
    print("BLOCK 98 : FAIL")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    raise SystemExit(1)

# ------------------------------------------------------------
# BLOCK 99
# ------------------------------------------------------------

print()
print("=" * 70)
print("BLOCK 99")
print("=" * 70)

b99 = EROSBlock99ExecutionIntentAuthorizationGate()

try:
    out99 = b99.certify(governance=out98)

    print("CERTIFY : PASS")
    print("TYPE    :", type(out99))
    print("STATUS  :", out99.get("status"))
    print("KEYS    :", list(out99.keys()))

except Exception as exc:
    print("BLOCK 99 : FAIL")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    raise SystemExit(1)

# ------------------------------------------------------------
# BLOCK 100
# ------------------------------------------------------------

print()
print("=" * 70)
print("BLOCK 100")
print("=" * 70)

b100 = EROSBlock100PaperExecutionFillGate()

try:
    out100 = b100.certify(
        intent=out99,
        fill_ratio=1.0,
    )

    print("CERTIFY : PASS")
    print("TYPE    :", type(out100))
    print("STATUS  :", out100.get("status"))
    print("KEYS    :", list(out100.keys()))

except Exception as exc:
    print("BLOCK 100 : FAIL")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    raise SystemExit(1)

# ------------------------------------------------------------
# BLOCK 101
# ------------------------------------------------------------

print()
print("=" * 70)
print("BLOCK 101")
print("=" * 70)

b101 = EROSBlock101ExecutionEvidenceReconciliationGate()

try:
    out101 = b101.certify(execution=out100)

    print("CERTIFY : PASS")
    print("TYPE    :", type(out101))
    print("STATUS  :", out101.get("status"))
    print("KEYS    :", list(out101.keys()))

except Exception as exc:
    print("BLOCK 101 : FAIL")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    raise SystemExit(1)

# ------------------------------------------------------------
# SAFETY CHECK
# ------------------------------------------------------------

print()
print("=" * 70)
print("SAFETY VERIFICATION")
print("=" * 70)

objects = {
    "94": out94,
    "95": out95,
    "96": out96,
    "97": out97,
    "98": out98,
    "99": out99,
    "100": out100,
    "101": out101,
}

safety_failures = []

for block_id, payload in objects.items():
    safety = payload.get("safety", {})

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
        if safety.get(field) is True:
            safety_failures.append(f"Block {block_id}: {field}=True")

    if safety.get("execution_blocked") is not True:
        safety_failures.append(f"Block {block_id}: execution_blocked != True")

    if safety.get("non_mutation_invariant") is not True:
        safety_failures.append(f"Block {block_id}: non_mutation_invariant != True")

if safety_failures:
    print("SAFETY : FAIL")
    for failure in safety_failures:
        print(" -", failure)
    raise SystemExit(1)

print("SAFETY : PASS")
print("ORDER CREATION    : FALSE")
print("BROKER SUBMISSION : FALSE")
print("LIVE EXECUTION    : FALSE")
print("MUTATION          : FALSE")
print("EXECUTION BLOCKED : TRUE")
print("NON-MUTATION      : TRUE")

# ------------------------------------------------------------
# FINAL CHAIN
# ------------------------------------------------------------

print()
print("=" * 70)
print("FINAL REAL DATA-FLOW CHAIN")
print("=" * 70)

print("94 -> 95 : PASS")
print("95 -> 96 : PASS")
print("96 -> 97 : PASS")
print("97 -> 98 : PASS")
print("98 -> 99 : PASS")
print("99 -> 100 : PASS")
print("100 -> 101 : PASS")

print()
print("============================================================")
print("BLOCK 94-101 REAL DATA-FLOW TEST : PASS")
print("============================================================")
print("READ ONLY         : TRUE")
print("ORDER CREATION    : FALSE")
print("BROKER SUBMISSION : FALSE")
print("LIVE EXECUTION    : FALSE")
print("MUTATION          : FALSE")
print("EXECUTION BLOCKED : TRUE")
print("NON-MUTATION      : TRUE")
print("============================================================")
