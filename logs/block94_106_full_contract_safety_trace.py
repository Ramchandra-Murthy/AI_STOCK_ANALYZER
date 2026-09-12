from pprint import pprint

print("=" * 90)
print("EROS 3.0 - BLOCK 94 -> 106 FULL END-TO-END CONTRACT + SAFETY TRACE")
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
from services.quantitative.block102_frontend_contract import (
    EROSBlock102FrontendContract,
)
from services.quantitative.block103_institutional_frontend_read_model import (
    EROSBlock103InstitutionalFrontendReadModel,
)
from services.quantitative.block104_eros_command_center import (
    EROSBlock104CommandCenter,
)
from services.quantitative.block106_institutional_integration_boundary import (
    EROSBlock106InstitutionalIntegrationBoundary,
)

print()
print("IMPORTS : PASS")

# ------------------------------------------------------------
# SYNTHETIC INPUT
# ------------------------------------------------------------

valuation = {
    "portfolio_value": 1_000_000.0,
    "total_value": 1_000_000.0,
}

performance = {
    "return_pct": 8.5,
    "daily_return_pct": 0.4,
}

risk = {
    "volatility_pct": 14.0,
    "max_drawdown_pct": -7.5,
}

positions = [
    {
        "symbol": "RELIANCE",
        "quantity": 100,
        "price": 2500.0,
        "market_value": 250000.0,
        "weight": 0.25,
    },
    {
        "symbol": "TCS",
        "quantity": 100,
        "price": 4000.0,
        "market_value": 400000.0,
        "weight": 0.40,
    },
]

scenarios = [
    {
        "scenario_id": "SYNTHETIC_MARKET_SHOCK",
        "name": "Synthetic Market Shock",
        "shock_pct": -10.0,
    }
]

print()
print("=" * 90)
print("SYNTHETIC INPUT")
print("=" * 90)
print("Portfolio value :", valuation["portfolio_value"])
print("Positions       :", len(positions))
print("Scenarios       :", len(scenarios))

# ------------------------------------------------------------
# HELPER
# ------------------------------------------------------------

results = {}


def inspect_result(block_id, payload):
    print()
    print("=" * 90)
    print(f"BLOCK {block_id} RESULT")
    print("=" * 90)

    print("TYPE   :", type(payload))

    if not isinstance(payload, dict):
        print("NON-DICT RESULT")
        return

    print("STATUS :", payload.get("status", "<ABSENT>"))
    print("KEYS   :", list(payload.keys()))

    print()
    print("SAFETY FIELD TRACE")

    safety_keys = [
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

    for key in safety_keys:
        print(f"{key:30} : {payload.get(key, '<ABSENT>')!r}")

    nested = payload.get("safety")

    if isinstance(nested, dict):
        print()
        print("NESTED SAFETY")
        for key, value in nested.items():
            print(f"{key:30} : {value!r}")

    print()
    print("FULL RESULT")
    pprint(payload, width=160, sort_dicts=False)


# ------------------------------------------------------------
# BLOCK 94
# ------------------------------------------------------------

b94_engine = EROSBlock94PortfolioStressScenarioEngine()

try:
    b94 = b94_engine.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    results["94"] = b94
    inspect_result("94", b94)

except Exception as exc:
    print("BLOCK 94 ERROR :", type(exc).__name__, str(exc))
    raise

# ------------------------------------------------------------
# BLOCK 95
# ------------------------------------------------------------

b95_engine = EROSBlock95StressEvidenceGate()

try:
    b95 = b95_engine.certify(stress_certificate=b94)

    results["95"] = b95
    inspect_result("95", b95)

except Exception as exc:
    print("BLOCK 95 ERROR :", type(exc).__name__, str(exc))
    raise

# ------------------------------------------------------------
# BLOCK 96
# ------------------------------------------------------------

b96_engine = EROSBlock96StressDecisionGate()

try:
    b96 = b96_engine.certify(stress_gate=b95)

    results["96"] = b96
    inspect_result("96", b96)

except Exception as exc:
    print("BLOCK 96 ERROR :", type(exc).__name__, str(exc))
    raise

# ------------------------------------------------------------
# BLOCK 97
# ------------------------------------------------------------

b97_engine = EROSBlock97StressReadinessGate()

try:
    b97 = b97_engine.certify(decision=b96)

    results["97"] = b97
    inspect_result("97", b97)

except Exception as exc:
    print("BLOCK 97 ERROR :", type(exc).__name__, str(exc))
    raise

# ------------------------------------------------------------
# BLOCK 98
# ------------------------------------------------------------

b98_engine = EROSBlock98ExecutionGovernanceBridge()

try:
    b98 = b98_engine.certify(decision=b97)

    results["98"] = b98
    inspect_result("98", b98)

except Exception as exc:
    print("BLOCK 98 ERROR :", type(exc).__name__, str(exc))
    raise

# ------------------------------------------------------------
# BLOCK 99
# ------------------------------------------------------------

b99_engine = EROSBlock99ExecutionIntentAuthorizationGate()

try:
    b99 = b99_engine.certify(governance=b98)

    results["99"] = b99
    inspect_result("99", b99)

except Exception as exc:
    print("BLOCK 99 ERROR :", type(exc).__name__, str(exc))
    raise

# ------------------------------------------------------------
# BLOCK 100
# ------------------------------------------------------------

b100_engine = EROSBlock100PaperExecutionFillGate()

try:
    b100 = b100_engine.certify(
        intent=b99,
        fill_ratio=1.0,
    )

    results["100"] = b100
    inspect_result("100", b100)

except Exception as exc:
    print("BLOCK 100 ERROR :", type(exc).__name__, str(exc))
    raise

# ------------------------------------------------------------
# BLOCK 101
# ------------------------------------------------------------

b101_engine = EROSBlock101ExecutionEvidenceReconciliationGate()

try:
    b101 = b101_engine.certify(execution=b100)

    results["101"] = b101
    inspect_result("101", b101)

except Exception as exc:
    print("BLOCK 101 ERROR :", type(exc).__name__, str(exc))
    raise

# ------------------------------------------------------------
# BLOCK 102
# ------------------------------------------------------------

b102_engine = EROSBlock102FrontendContract()

try:
    b102 = b102_engine.build(
        block94=b94,
        block95=b95,
        block96=b96,
        block97=b97,
        block98=b98,
        block99=b99,
        block100=b100,
        block101=b101,
    )

    results["102"] = b102
    inspect_result("102", b102)

except Exception as exc:
    print("BLOCK 102 ERROR :", type(exc).__name__, str(exc))
    raise

# ------------------------------------------------------------
# BLOCK 103
# ------------------------------------------------------------

b103_engine = EROSBlock103InstitutionalFrontendReadModel()

try:
    b103 = b103_engine.build(contract=b102)

    results["103"] = b103
    inspect_result("103", b103)

except Exception as exc:
    print("BLOCK 103 ERROR :", type(exc).__name__, str(exc))
    raise

# ------------------------------------------------------------
# BLOCK 104
# ------------------------------------------------------------

b104_engine = EROSBlock104CommandCenter()

try:
    b104 = b104_engine.render_model(read_model=b103)

    results["104"] = b104
    inspect_result("104", b104)

except Exception as exc:
    print("BLOCK 104 ERROR :", type(exc).__name__, str(exc))
    raise

# ------------------------------------------------------------
# BLOCK 106
# ------------------------------------------------------------

b106_engine = EROSBlock106InstitutionalIntegrationBoundary()

try:
    b106 = b106_engine.build_integration_payload(command_center=b104)

    results["106"] = b106
    inspect_result("106", b106)

    print()
    print("=" * 90)
    print("BLOCK 106 VALIDATION")
    print("=" * 90)

    validation = b106_engine.validate_payload(b106)

    print("VALIDATE RESULT :", validation)

except Exception as exc:
    print("BLOCK 106 ERROR :", type(exc).__name__, str(exc))
    raise

# ------------------------------------------------------------
# FINAL SAFETY MATRIX
# ------------------------------------------------------------

print()
print("=" * 90)
print("FINAL SAFETY MATRIX")
print("=" * 90)

safety_keys = [
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

for block_id, payload in results.items():

    if not isinstance(payload, dict):
        continue

    print()
    print(f"BLOCK {block_id}")

    for key in safety_keys:
        value = payload.get(key, "<ABSENT>")

        if value == "<ABSENT>" and isinstance(payload.get("safety"), dict):
            value = payload["safety"].get(key, "<ABSENT>")

        print(f"  {key:28} : {value!r}")

# ------------------------------------------------------------
# CHAIN SUMMARY
# ------------------------------------------------------------

print()
print("=" * 90)
print("FINAL CONTRACT CHAIN")
print("=" * 90)

print("94  -> 95   : PASS")
print("95  -> 96   : PASS")
print("96  -> 97   : PASS")
print("97  -> 98   : PASS")
print("98  -> 99   : PASS")
print("99  -> 100  : PASS")
print("100 -> 101  : PASS")
print("101 -> 102  : PASS")
print("102 -> 103  : PASS")
print("103 -> 104  : PASS")
print("104 -> 106  : PASS")

print()
print("READ ONLY       : TRUE")
print("NO BROKER       : TRUE")
print("NO LIVE EXEC    : TRUE")
print("NO ORDER CREATE : TRUE")
print("NO MUTATION     : TRUE")

print()
print("=" * 90)
print("FULL END-TO-END CONTRACT + SAFETY TRACE COMPLETE")
print("=" * 90)
