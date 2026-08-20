import sys
import inspect
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def show(label, payload):
    print()
    print("-" * 70)
    print(label)
    print("-" * 70)
    print("TYPE :", type(payload))
    if isinstance(payload, dict):
        print("KEYS :", list(payload.keys()))
        print("STATUS :", repr(payload.get("status")))
        print("BLOCK ID :", repr(payload.get("block_id")))

print("=" * 70)
print("EROS 3.0 - 94 -> 106 END-TO-END RUNTIME CERTIFICATION")
print("=" * 70)
print("READ ONLY")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")

# ------------------------------------------------------------
# 1. SIGNATURES
# ------------------------------------------------------------
print()
print("1. ACTUAL INTERFACES")
print("-" * 70)

interfaces = [
    (EROSBlock102FrontendContract, "build"),
    (EROSBlock103InstitutionalFrontendReadModel, "build"),
    (EROSBlock104CommandCenter, "snapshot"),
    (EROSBlock106InstitutionalIntegrationBoundary, "build_integration_payload"),
    (EROSBlock106InstitutionalIntegrationBoundary, "build_read_only_snapshot"),
    (EROSBlock106InstitutionalIntegrationBoundary, "validate_payload"),
]

for cls, method_name in interfaces:
    print(
        cls.__name__,
        method_name,
        ":",
        inspect.signature(getattr(cls, method_name))
    )

# ------------------------------------------------------------
# 2. UPSTREAM READ-ONLY INPUTS
# ------------------------------------------------------------
print()
print("2. PREPARE SAFE READ-ONLY UPSTREAM INPUTS")
print("-" * 70)

valuation = {
    "status": "CERTIFIED",
    "portfolio_value": 1000000.0,
}

performance = {
    "status": "CERTIFIED",
    "pnl": 0.0,
}

risk = {
    "status": "CERTIFIED",
}

positions = [
    {
        "symbol": "RELIANCE",
        "quantity": 100,
        "reference_price": 1400.0,
    }
]

scenarios = [
    {
        "name": "market_down_10",
        "price_shock_pct": -10.0,
    },
    {
        "name": "market_up_10",
        "price_shock_pct": 10.0,
    },
]

# ------------------------------------------------------------
# 3. BLOCK 94
# ------------------------------------------------------------
print()
print("3. BLOCK 94")
print("-" * 70)

b94 = EROSBlock94PortfolioStressScenarioEngine()

stress = b94.stress_portfolio(
    valuation=valuation,
    performance=performance,
    risk=risk,
    positions=positions,
    scenarios=scenarios,
)

show("BLOCK 94 OUTPUT", stress)

require(isinstance(stress, dict), "BLOCK94_NOT_DICT")

# ------------------------------------------------------------
# 4. BLOCK 95
# ------------------------------------------------------------
print()
print("4. BLOCK 95")
print("-" * 70)

b95 = EROSBlock95StressEvidenceGate()

gate95 = b95.gate(
    stress_certificate=stress
)

show("BLOCK 95 OUTPUT", gate95)

require(isinstance(gate95, dict), "BLOCK95_NOT_DICT")

# ------------------------------------------------------------
# 5. BLOCK 96
# ------------------------------------------------------------
print()
print("5. BLOCK 96")
print("-" * 70)

b96 = EROSBlock96StressDecisionGate()

decision96 = b96.decide(
    stress_gate=gate95
)

show("BLOCK 96 OUTPUT", decision96)

require(isinstance(decision96, dict), "BLOCK96_NOT_DICT")

# ------------------------------------------------------------
# 6. BLOCK 97
# ------------------------------------------------------------
print()
print("6. BLOCK 97")
print("-" * 70)

b97 = EROSBlock97StressReadinessGate()

readiness97 = b97.evaluate(
    decision=decision96
)

show("BLOCK 97 OUTPUT", readiness97)

require(isinstance(readiness97, dict), "BLOCK97_NOT_DICT")

# ------------------------------------------------------------
# 7. BLOCK 98
# ------------------------------------------------------------
print()
print("7. BLOCK 98")
print("-" * 70)

b98 = EROSBlock98ExecutionGovernanceBridge()

governance98 = b98.govern(
    decision=readiness97
)

show("BLOCK 98 OUTPUT", governance98)

require(isinstance(governance98, dict), "BLOCK98_NOT_DICT")

# ------------------------------------------------------------
# 8. BLOCK 99
# ------------------------------------------------------------
print()
print("8. BLOCK 99")
print("-" * 70)

b99 = EROSBlock99ExecutionIntentAuthorizationGate()

intent99 = b99.authorize(
    governance=governance98
)

show("BLOCK 99 OUTPUT", intent99)

require(isinstance(intent99, dict), "BLOCK99_NOT_DICT")

# ------------------------------------------------------------
# 9. BLOCK 100
# ------------------------------------------------------------
print()
print("9. BLOCK 100")
print("-" * 70)

b100 = EROSBlock100PaperExecutionFillGate()

execution100 = b100.certify(
    intent=intent99
)

show("BLOCK 100 OUTPUT", execution100)

require(isinstance(execution100, dict), "BLOCK100_NOT_DICT")

# ------------------------------------------------------------
# 10. BLOCK 101
# ------------------------------------------------------------
print()
print("10. BLOCK 101")
print("-" * 70)

b101 = EROSBlock101ExecutionEvidenceReconciliationGate()

reconciliation101 = b101.evaluate(
    execution=execution100
)

show("BLOCK 101 OUTPUT", reconciliation101)

require(isinstance(reconciliation101, dict), "BLOCK101_NOT_DICT")

# ------------------------------------------------------------
# 11. BLOCK 102
# ------------------------------------------------------------
print()
print("11. BLOCK 102")
print("-" * 70)

b102 = EROSBlock102FrontendContract()

contract102 = b102.build(
    block94=stress,
    block95=gate95,
    block96=decision96,
    block97=readiness97,
    block98=governance98,
    block99=intent99,
    block100=execution100,
    block101=reconciliation101,
)

show("BLOCK 102 OUTPUT", contract102)

require(contract102.get("block_id") == "102", "BLOCK102_BAD_ID")
require(contract102.get("status") == "CERTIFIED", "BLOCK102_NOT_CERTIFIED")

# ------------------------------------------------------------
# 12. BLOCK 103
# ------------------------------------------------------------
print()
print("12. BLOCK 103")
print("-" * 70)

b103 = EROSBlock103InstitutionalFrontendReadModel()

read_model103 = b103.build(
    contract=contract102
)

show("BLOCK 103 OUTPUT", read_model103)

require(read_model103.get("block_id") == "103", "BLOCK103_BAD_ID")
require(read_model103.get("status") == "CERTIFIED", "BLOCK103_NOT_CERTIFIED")

# ------------------------------------------------------------
# 13. BLOCK 104
# ------------------------------------------------------------
print()
print("13. BLOCK 104")
print("-" * 70)

b104 = EROSBlock104CommandCenter()

command_center104 = b104.render_model(
    read_model=read_model103
)

show("BLOCK 104 OUTPUT", command_center104)

require(command_center104.get("block_id") == "104", "BLOCK104_BAD_ID")
require(command_center104.get("status") == "CERTIFIED", "BLOCK104_NOT_CERTIFIED")

# ------------------------------------------------------------
# 14. BLOCK 106
# ------------------------------------------------------------
print()
print("14. BLOCK 106")
print("-" * 70)

b106 = EROSBlock106InstitutionalIntegrationBoundary()

integration106 = b106.build_integration_payload(
    command_center=command_center104
)

show("BLOCK 106 INTEGRATION OUTPUT", integration106)

require(isinstance(integration106, dict), "BLOCK106_NOT_DICT")

snapshot106 = b106.build_read_only_snapshot(
    command_center=command_center104
)

show("BLOCK 106 READ-ONLY SNAPSHOT", snapshot106)

require(isinstance(snapshot106, dict), "BLOCK106_SNAPSHOT_NOT_DICT")

valid106 = b106.validate_payload(
    integration106
)

print()
print("BLOCK 106 VALIDATION :", valid106)

require(valid106 is True, "BLOCK106_VALIDATION_FAILED")

# ------------------------------------------------------------
# 15. SAFETY
# ------------------------------------------------------------
print()
print("15. SAFETY VERIFICATION")
print("-" * 70)

safety = integration106.get("safety", {})

for key in [
    "allow_order_creation",
    "allow_broker_submission",
    "allow_live_execution",
    "allow_portfolio_mutation",
    "allow_valuation_mutation",
    "allow_performance_mutation",
    "allow_risk_mutation",
    "allow_optimization",
    "execution_blocked",
    "non_mutation_invariant",
]:
    print(f"{key:32}:", safety.get(key))

require(safety.get("allow_order_creation") is False, "ORDER_CREATION_NOT_BLOCKED")
require(safety.get("allow_broker_submission") is False, "BROKER_NOT_BLOCKED")
require(safety.get("allow_live_execution") is False, "LIVE_EXECUTION_NOT_BLOCKED")
require(safety.get("allow_portfolio_mutation") is False, "PORTFOLIO_MUTATION_NOT_BLOCKED")
require(safety.get("execution_blocked") is True, "EXECUTION_NOT_BLOCKED")
require(safety.get("non_mutation_invariant") is True, "NON_MUTATION_INVARIANT_FAILED")

# ------------------------------------------------------------
# 16. FINAL
# ------------------------------------------------------------
print()
print("=" * 70)
print("FINAL END-TO-END CONTRACT CHAIN")
print("=" * 70)

print("94  -> 95  : PASS")
print("95  -> 96  : PASS")
print("96  -> 97  : PASS")
print("97  -> 98  : PASS")
print("98  -> 99  : PASS")
print("99  -> 100 : PASS")
print("100 -> 101 : PASS")
print("101 -> 102 : PASS")
print("102 -> 103 : PASS")
print("103 -> 104 : PASS")
print("104 -> 106 : PASS")
print("106 BUILD  : PASS")
print("106 SNAPSHOT: PASS")
print("106 VALIDATE: PASS")
print("SAFETY     : PASS")

print()
print("=" * 70)
print("EROS 3.0 - BLOCK 94 -> 106 END-TO-END CERTIFICATION : PASS")
print("=" * 70)
print("READ ONLY         : TRUE")
print("ORDER CREATION    : FALSE")
print("BROKER SUBMISSION : FALSE")
print("LIVE EXECUTION    : FALSE")
print("MUTATION          : FALSE")
print("EXECUTION BLOCKED : TRUE")
print("NON-MUTATION      : TRUE")
print("=" * 70)
