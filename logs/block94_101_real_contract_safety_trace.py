import importlib
from pprint import pprint

print("=" * 90)
print("EROS 3.0 - BLOCK 94 -> 101 REAL CONTRACT + SAFETY TRACE")
print("=" * 90)

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

print()
print("IMPORTS : PASS")

# ------------------------------------------------------------
# SYNTHETIC READ-ONLY INPUT
# ------------------------------------------------------------

valuation = {
    "portfolio_value": 1_000_000.0,
    "currency": "INR",
}

performance = {
    "daily_return": 0.01,
    "monthly_return": 0.04,
}

risk = {
    "volatility": 0.18,
    "max_drawdown": 0.12,
}

positions = [
    {
        "symbol": "RELIANCE",
        "quantity": 100,
        "price": 2500.0,
        "market_value": 250000.0,
    },
    {
        "symbol": "TCS",
        "quantity": 50,
        "price": 4000.0,
        "market_value": 200000.0,
    },
]

scenarios = [
    {
        "scenario_id": "TEST-STRESS-01",
        "name": "Synthetic Market Stress",
        "market_shock_pct": -10.0,
    }
]

print()
print("SYNTHETIC INPUT : CREATED")
print("Portfolio value :", valuation["portfolio_value"])
print("Positions       :", len(positions))
print("Scenarios       :", len(scenarios))

# ------------------------------------------------------------
# SAFETY FIELD INSPECTION
# ------------------------------------------------------------

SAFETY_FIELDS = [
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

def inspect_result(label, result):

    print()
    print("-" * 90)
    print(label)
    print("-" * 90)

    print("TYPE   :", type(result))

    if not isinstance(result, dict):
        print("RESULT IS NOT A DICT")
        return

    print("STATUS :", result.get("status", "<ABSENT>"))

    print()
    print("TOP LEVEL KEYS:")
    for key in result.keys():
        print("  ", key)

    print()
    print("SAFETY FIELDS:")

    for field in SAFETY_FIELDS:
        value = result.get(field, "<ABSENT>")
        print(f"{field:28} : {value!r}")

    if isinstance(result.get("safety"), dict):
        print()
        print("NESTED SAFETY:")
        for key, value in result["safety"].items():
            print(f"  {key:28} : {value!r}")

    print()
    print("FULL RESULT:")
    pprint(result, width=160, sort_dicts=False)


# ------------------------------------------------------------
# BLOCK 94
# ------------------------------------------------------------

print()
print("=" * 90)
print("BLOCK 94")
print("=" * 90)

b94 = EROSBlock94PortfolioStressScenarioEngine()

try:

    result94 = b94.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    print("CERTIFY : PASS")

except Exception as exc:

    print("CERTIFY : FAIL")
    print(type(exc).__name__, str(exc))
    result94 = {}

inspect_result("BLOCK 94 RESULT", result94)

# ------------------------------------------------------------
# BLOCK 95
# ------------------------------------------------------------

print()
print("=" * 90)
print("BLOCK 95")
print("=" * 90)

b95 = EROSBlock95StressEvidenceGate()

try:

    result95 = b95.certify(
        stress_certificate=result94
    )

    print("CERTIFY : PASS")

except Exception as exc:

    print("CERTIFY : FAIL")
    print(type(exc).__name__, str(exc))
    result95 = {}

inspect_result("BLOCK 95 RESULT", result95)

# ------------------------------------------------------------
# BLOCK 96
# ------------------------------------------------------------

print()
print("=" * 90)
print("BLOCK 96")
print("=" * 90)

b96 = EROSBlock96StressDecisionGate()

try:

    result96 = b96.certify(
        stress_gate=result95
    )

    print("CERTIFY : PASS")

except Exception as exc:

    print("CERTIFY : FAIL")
    print(type(exc).__name__, str(exc))
    result96 = {}

inspect_result("BLOCK 96 RESULT", result96)

# ------------------------------------------------------------
# BLOCK 97
# ------------------------------------------------------------

print()
print("=" * 90)
print("BLOCK 97")
print("=" * 90)

b97 = EROSBlock97StressReadinessGate()

try:

    result97 = b97.certify(
        decision=result96
    )

    print("CERTIFY : PASS")

except Exception as exc:

    print("CERTIFY : FAIL")
    print(type(exc).__name__, str(exc))
    result97 = {}

inspect_result("BLOCK 97 RESULT", result97)

# ------------------------------------------------------------
# BLOCK 98
# ------------------------------------------------------------

print()
print("=" * 90)
print("BLOCK 98")
print("=" * 90)

b98 = EROSBlock98ExecutionGovernanceBridge()

try:

    result98 = b98.certify(
        decision=result97
    )

    print("CERTIFY : PASS")

except Exception as exc:

    print("CERTIFY : FAIL")
    print(type(exc).__name__, str(exc))
    result98 = {}

inspect_result("BLOCK 98 RESULT", result98)

# ------------------------------------------------------------
# BLOCK 99
# ------------------------------------------------------------

print()
print("=" * 90)
print("BLOCK 99")
print("=" * 90)

b99 = EROSBlock99ExecutionIntentAuthorizationGate()

try:

    result99 = b99.certify(
        governance=result98
    )

    print("CERTIFY : PASS")

except Exception as exc:

    print("CERTIFY : FAIL")
    print(type(exc).__name__, str(exc))
    result99 = {}

inspect_result("BLOCK 99 RESULT", result99)

# ------------------------------------------------------------
# BLOCK 100
# ------------------------------------------------------------

print()
print("=" * 90)
print("BLOCK 100")
print("=" * 90)

b100 = EROSBlock100PaperExecutionFillGate()

try:

    result100 = b100.certify(
        intent=result99,
        fill_ratio=1.0,
    )

    print("CERTIFY : PASS")

except Exception as exc:

    print("CERTIFY : FAIL")
    print(type(exc).__name__, str(exc))
    result100 = {}

inspect_result("BLOCK 100 RESULT", result100)

# ------------------------------------------------------------
# BLOCK 101
# ------------------------------------------------------------

print()
print("=" * 90)
print("BLOCK 101")
print("=" * 90)

b101 = EROSBlock101ExecutionEvidenceReconciliationGate()

try:

    result101 = b101.certify(
        execution=result100
    )

    print("CERTIFY : PASS")

except Exception as exc:

    print("CERTIFY : FAIL")
    print(type(exc).__name__, str(exc))
    result101 = {}

inspect_result("BLOCK 101 RESULT", result101)

# ------------------------------------------------------------
# FINAL SAFETY MATRIX
# ------------------------------------------------------------

print()
print("=" * 90)
print("FINAL SAFETY MATRIX")
print("=" * 90)

results = {
    "94": result94,
    "95": result95,
    "96": result96,
    "97": result97,
    "98": result98,
    "99": result99,
    "100": result100,
    "101": result101,
}

for block_id, result in results.items():

    print()
    print(f"BLOCK {block_id}")

    if not isinstance(result, dict):
        print("RESULT : INVALID")
        continue

    for field in SAFETY_FIELDS:
        print(
            f"{field:28} : "
            f"{result.get(field, '<ABSENT>')!r}"
        )

# ------------------------------------------------------------
# CHAIN SUMMARY
# ------------------------------------------------------------

print()
print("=" * 90)
print("CHAIN SUMMARY")
print("=" * 90)

print("94 -> 95  : EXECUTED")
print("95 -> 96  : EXECUTED")
print("96 -> 97  : EXECUTED")
print("97 -> 98  : EXECUTED")
print("98 -> 99  : EXECUTED")
print("99 -> 100 : EXECUTED")
print("100 -> 101: EXECUTED")

print()
print("IMPORTANT:")
print("This was a synthetic READ-ONLY contract trace.")
print("No broker was contacted.")
print("No live order was created.")
print("No live execution occurred.")
print("No portfolio was mutated.")
print("No valuation was mutated.")
print("No performance was mutated.")
print("No risk state was mutated.")
print("No optimization was performed.")

print()
print("=" * 90)
print("REAL CONTRACT + SAFETY TRACE COMPLETE")
print("=" * 90)

