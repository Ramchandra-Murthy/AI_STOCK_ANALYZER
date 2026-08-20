import importlib
import json
from pprint import pprint

print("=" * 90)
print("EROS 3.0 - BLOCK 94 -> 106 END-TO-END CONTRACT TRACE")
print("=" * 90)

def show(title, obj):
    print()
    print("-" * 90)
    print(title)
    print("-" * 90)
    print("TYPE:", type(obj).__name__)

    if isinstance(obj, dict):
        print("KEYS:")
        for key in obj.keys():
            print("  ", key)

        print()
        print("FULL OBJECT:")
        pprint(obj, width=160, sort_dicts=False)

    else:
        pprint(obj, width=160, sort_dicts=False)


# ============================================================
# IMPORTS
# ============================================================

modules = {}

module_names = [
    "services.quantitative.block94_portfolio_stress_scenario_engine",
    "services.quantitative.block95_stress_evidence_gate",
    "services.quantitative.block96_stress_decision_gate",
    "services.quantitative.block97_stress_readiness_gate",
    "services.quantitative.block98_execution_governance_bridge",
    "services.quantitative.block99_execution_intent_authorization_gate",
    "services.quantitative.block100_paper_execution_fill_gate",
    "services.quantitative.block101_execution_evidence_reconciliation",
    "services.quantitative.block102_frontend_contract",
    "services.quantitative.block103_institutional_frontend_read_model",
    "services.quantitative.block104_eros_command_center",
    "services.quantitative.block106_institutional_integration_boundary",
]

print()
print("IMPORT PHASE")
print("=" * 90)

for name in module_names:
    try:
        modules[name] = importlib.import_module(name)
        print("PASS :", name)
    except Exception as exc:
        print("FAIL :", name)
        print("      ", type(exc).__name__, str(exc))


# ============================================================
# SYNTHETIC PORTFOLIO
# ============================================================

valuation = {
    "portfolio_value": 1_000_000.0,
    "cash": 250_000.0,
    "gross_exposure": 750_000.0,
}

performance = {
    "daily_return": 0.012,
    "monthly_return": 0.034,
    "drawdown": -0.045,
}

risk = {
    "volatility": 0.18,
    "var": -0.025,
    "risk_score": 42,
}

positions = [
    {
        "symbol": "RELIANCE.NS",
        "quantity": 100,
        "price": 2900.0,
        "market_value": 290000.0,
    },
    {
        "symbol": "TCS.NS",
        "quantity": 50,
        "price": 3800.0,
        "market_value": 190000.0,
    },
]

scenarios = [
    {
        "scenario_id": "MARKET_STRESS_01",
        "name": "Broad Market Stress",
        "shock": -0.10,
    }
]

policy = {
    "allow_execution": False,
    "allow_broker_submission": False,
    "allow_live_orders": False,
    "allow_portfolio_mutation": False,
    "allow_valuation_mutation": False,
    "allow_performance_mutation": False,
    "allow_risk_mutation": False,
    "allow_optimization": False,
    "allow_order_creation": False,
}


print()
print("=" * 90)
print("SYNTHETIC INPUT")
print("=" * 90)

print("Portfolio value :", valuation["portfolio_value"])
print("Positions       :", len(positions))
print("Scenarios       :", len(scenarios))
print("Execution       :", policy["allow_execution"])
print("Broker          :", policy["allow_broker_submission"])
print("Live orders     :", policy["allow_live_orders"])


# ============================================================
# BLOCK 94
# ============================================================

print()
print("=" * 90)
print("BLOCK 94 - PORTFOLIO STRESS")
print("=" * 90)

b94 = modules[
    "services.quantitative.block94_portfolio_stress_scenario_engine"
].EROSBlock94PortfolioStressScenarioEngine()

try:
    r94 = b94.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )
    print("STATUS : PASS")
    show("BLOCK 94 OUTPUT", r94)
except Exception as exc:
    r94 = {}
    print("STATUS : ERROR")
    print(type(exc).__name__, str(exc))


# ============================================================
# BLOCK 95
# ============================================================

print()
print("=" * 90)
print("BLOCK 95 - STRESS EVIDENCE GATE")
print("=" * 90)

b95 = modules[
    "services.quantitative.block95_stress_evidence_gate"
].EROSBlock95StressEvidenceGate()

try:
    r95 = b95.certify(
        stress_certificate=r94,
        policy=policy,
    )
    print("STATUS : PASS")
    show("BLOCK 95 OUTPUT", r95)
except Exception as exc:
    r95 = {}
    print("STATUS : ERROR")
    print(type(exc).__name__, str(exc))


# ============================================================
# BLOCK 96
# ============================================================

print()
print("=" * 90)
print("BLOCK 96 - STRESS DECISION")
print("=" * 90)

b96 = modules[
    "services.quantitative.block96_stress_decision_gate"
].EROSBlock96StressDecisionGate()

try:
    r96 = b96.certify(
        stress_gate=r95,
        policy=policy,
    )
    print("STATUS : PASS")
    show("BLOCK 96 OUTPUT", r96)
except Exception as exc:
    r96 = {}
    print("STATUS : ERROR")
    print(type(exc).__name__, str(exc))


# ============================================================
# BLOCK 97
# ============================================================

print()
print("=" * 90)
print("BLOCK 97 - STRESS READINESS")
print("=" * 90)

b97 = modules[
    "services.quantitative.block97_stress_readiness_gate"
].EROSBlock97StressReadinessGate()

try:
    r97 = b97.certify(
        decision=r96,
    )
    print("STATUS : PASS")
    show("BLOCK 97 OUTPUT", r97)
except Exception as exc:
    r97 = {}
    print("STATUS : ERROR")
    print(type(exc).__name__, str(exc))


# ============================================================
# BLOCK 98
# ============================================================

print()
print("=" * 90)
print("BLOCK 98 - EXECUTION GOVERNANCE")
print("=" * 90)

b98 = modules[
    "services.quantitative.block98_execution_governance_bridge"
].EROSBlock98ExecutionGovernanceBridge()

try:
    r98 = b98.certify(
        decision=r97,
    )
    print("STATUS : PASS")
    show("BLOCK 98 OUTPUT", r98)
except Exception as exc:
    r98 = {}
    print("STATUS : ERROR")
    print(type(exc).__name__, str(exc))


# ============================================================
# BLOCK 99
# ============================================================

print()
print("=" * 90)
print("BLOCK 99 - EXECUTION INTENT AUTHORIZATION")
print("=" * 90)

b99 = modules[
    "services.quantitative.block99_execution_intent_authorization_gate"
].EROSBlock99ExecutionIntentAuthorizationGate()

try:
    r99 = b99.certify(
        governance=r98,
    )
    print("STATUS : PASS")
    show("BLOCK 99 OUTPUT", r99)
except Exception as exc:
    r99 = {}
    print("STATUS : ERROR")
    print(type(exc).__name__, str(exc))


# ============================================================
# BLOCK 100
# ============================================================

print()
print("=" * 90)
print("BLOCK 100 - PAPER EXECUTION")
print("=" * 90)

b100 = modules[
    "services.quantitative.block100_paper_execution_fill_gate"
].EROSBlock100PaperExecutionFillGate()

try:
    r100 = b100.certify(
        intent=r99,
        fill_ratio=1.0,
    )
    print("STATUS : PASS")
    show("BLOCK 100 OUTPUT", r100)
except Exception as exc:
    r100 = {}
    print("STATUS : ERROR")
    print(type(exc).__name__, str(exc))


# ============================================================
# BLOCK 101
# ============================================================

print()
print("=" * 90)
print("BLOCK 101 - EXECUTION EVIDENCE RECONCILIATION")
print("=" * 90)

b101 = modules[
    "services.quantitative.block101_execution_evidence_reconciliation"
].EROSBlock101ExecutionEvidenceReconciliationGate()

try:
    r101 = b101.certify(
        execution=r100,
    )
    print("STATUS : PASS")
    show("BLOCK 101 OUTPUT", r101)
except Exception as exc:
    r101 = {}
    print("STATUS : ERROR")
    print(type(exc).__name__, str(exc))


# ============================================================
# BLOCK 102
# ============================================================

print()
print("=" * 90)
print("BLOCK 102 - FRONTEND CONTRACT")
print("=" * 90)

b102 = modules[
    "services.quantitative.block102_frontend_contract"
].EROSBlock102FrontendContract()

try:
    r102 = b102.build(
        block94=r94,
        block95=r95,
        block96=r96,
        block97=r97,
        block98=r98,
        block99=r99,
        block100=r100,
        block101=r101,
    )
    print("STATUS : PASS")
    show("BLOCK 102 OUTPUT", r102)
except Exception as exc:
    r102 = {}
    print("STATUS : ERROR")
    print(type(exc).__name__, str(exc))


# ============================================================
# BLOCK 103
# ============================================================

print()
print("=" * 90)
print("BLOCK 103 - INSTITUTIONAL FRONTEND READ MODEL")
print("=" * 90)

b103 = modules[
    "services.quantitative.block103_institutional_frontend_read_model"
].EROSBlock103InstitutionalFrontendReadModel()

try:
    r103 = b103.build(contract=r102)
    print("STATUS : PASS")
    show("BLOCK 103 OUTPUT", r103)
except Exception as exc:
    r103 = {}
    print("STATUS : ERROR")
    print(type(exc).__name__, str(exc))


# ============================================================
# BLOCK 104
# ============================================================

print()
print("=" * 90)
print("BLOCK 104 - EROS COMMAND CENTER")
print("=" * 90)

b104 = modules[
    "services.quantitative.block104_eros_command_center"
].EROSBlock104CommandCenter()

try:
    r104 = b104.render_model(read_model=r103)
    print("STATUS : PASS")
    show("BLOCK 104 OUTPUT", r104)
except Exception as exc:
    r104 = {}
    print("STATUS : ERROR")
    print(type(exc).__name__, str(exc))


# ============================================================
# BLOCK 106
# ============================================================

print()
print("=" * 90)
print("BLOCK 106 - INSTITUTIONAL INTEGRATION BOUNDARY")
print("=" * 90)

b106 = modules[
    "services.quantitative.block106_institutional_integration_boundary"
].EROSBlock106InstitutionalIntegrationBoundary()

try:
    r106 = b106.build_integration_payload(
        command_center=r104,
    )

    print("STATUS : PASS")
    show("BLOCK 106 OUTPUT", r106)

    try:
        validation = b106.validate_payload(r106)
        print()
        print("PAYLOAD VALIDATION :", validation)
    except Exception as exc:
        print("PAYLOAD VALIDATION ERROR")
        print(type(exc).__name__, str(exc))

except Exception as exc:
    r106 = {}
    print("STATUS : ERROR")
    print(type(exc).__name__, str(exc))


# ============================================================
# SAFETY SUMMARY
# ============================================================

print()
print("=" * 90)
print("GLOBAL SAFETY SUMMARY")
print("=" * 90)

results = {
    94: r94,
    95: r95,
    96: r96,
    97: r97,
    98: r98,
    99: r99,
    100: r100,
    101: r101,
    102: r102,
    103: r103,
    104: r104,
    106: r106,
}

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

for block_id, result in results.items():

    if not isinstance(result, dict):
        print(f"BLOCK {block_id}: NON-DICT OUTPUT")
        continue

    print()
    print(f"BLOCK {block_id}")

    for key in safety_keys:
        if key in result:
            print(f"  {key:28} = {result[key]!r}")

    if isinstance(result.get("safety"), dict):
        print("  NESTED SAFETY")
        for key, value in result["safety"].items():
            print(f"    {key:26} = {value!r}")


# ============================================================
# FINAL ARCHITECTURAL TRACE
# ============================================================

print()
print("=" * 90)
print("FINAL ARCHITECTURAL TRACE")
print("=" * 90)

print("""
94  Stress Scenario Engine
 ?
95  Stress Evidence Gate
 ?
96  Stress Decision Gate
 ?
97  Stress Readiness Gate
 ?
98  Execution Governance Bridge
 ?
99  Execution Intent Authorization Gate
 ?
100 Paper Execution Fill Gate
 ?
101 Execution Evidence Reconciliation
 ?
102 Frontend Contract
 ?
103 Institutional Frontend Read Model
 ?
104 EROS Command Center
 ?
106 Institutional Integration Boundary
""")

print("=" * 90)
print("TRACE COMPLETE")
print("=" * 90)
print("READ ONLY")
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO PORTFOLIO MUTATION")
print("=" * 90)

