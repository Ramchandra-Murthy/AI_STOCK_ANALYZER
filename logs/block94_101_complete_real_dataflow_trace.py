import importlib
import traceback
from pprint import pprint

BASE = "services.quantitative."

MODULES = {
    94: BASE + "block94_portfolio_stress_scenario_engine",
    95: BASE + "block95_stress_evidence_gate",
    96: BASE + "block96_stress_decision_gate",
    97: BASE + "block97_stress_readiness_gate",
    98: BASE + "block98_execution_governance_bridge",
    99: BASE + "block99_execution_intent_authorization_gate",
    100: BASE + "block100_paper_execution_fill_gate",
    101: BASE + "block101_execution_evidence_reconciliation",
}

CLASS_NAMES = {
    94: "EROSBlock94PortfolioStressScenarioEngine",
    95: "EROSBlock95StressEvidenceGate",
    96: "EROSBlock96StressDecisionGate",
    97: "EROSBlock97StressReadinessGate",
    98: "EROSBlock98ExecutionGovernanceBridge",
    99: "EROSBlock99ExecutionIntentAuthorizationGate",
    100: "EROSBlock100PaperExecutionFillGate",
    101: "EROSBlock101ExecutionEvidenceReconciliationGate",
}


def load(block):
    module = importlib.import_module(MODULES[block])
    cls = getattr(module, CLASS_NAMES[block])
    return cls()


def get_path(data, path):
    current = data

    for key in path.split("."):
        if not isinstance(current, dict):
            return "<NOT-A-DICT>"

        if key not in current:
            return "<ABSENT>"

        current = current[key]

    return current


def safety_report(label, data):
    print()
    print("-" * 70)
    print("SAFETY FIELD REPORT :", label)
    print("-" * 70)

    if not isinstance(data, dict):
        print("OUTPUT TYPE :", type(data))
        print("NOT A DICTIONARY")
        return

    fields = [
        "status",
        "reason",
        "reason_code",
        "action",
        "execution_action",
        "execution_status",
        "intent_status",
        "readiness_status",
        "governance_status",
        "decision_status",
        "gate_status",
        "reconciliation_status",
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

    for field in fields:
        value = data.get(field, "<ABSENT>")
        print(f"{field:30} : {value!r}")

    for container_name in [
        "safety",
        "governance",
        "execution",
        "intent",
        "reconciliation",
        "pipeline",
    ]:

        nested = data.get(container_name)

        if isinstance(nested, dict):
            print()
            print(f"NESTED OBJECT : {container_name}")

            for key, value in nested.items():
                print(f"  {key:28} : {value!r}")


def show_output(label, data):
    print()
    print("=" * 70)
    print(label)
    print("=" * 70)

    print("TYPE :", type(data))

    if isinstance(data, dict):
        print("KEY COUNT :", len(data))
        print("KEYS :")
        for key in data.keys():
            print("  -", key)

    safety_report(label, data)

    print()
    print("FULL OUTPUT:")
    pprint(data, width=140, sort_dicts=False)


print("=" * 70)
print("EROS 3.0 - BLOCK 94-101 COMPLETE REAL DATA-FLOW TRACE")
print("=" * 70)

# ------------------------------------------------------------------
# IMPORT / INSTANCE
# ------------------------------------------------------------------

blocks = {}

print()
print("=" * 70)
print("PHASE 1 - IMPORT AND INSTANCE")
print("=" * 70)

for block in range(94, 102):

    print()
    print(f"BLOCK {block}")

    try:
        instance = load(block)
        blocks[block] = instance
        print("IMPORT   : PASS")
        print("INSTANCE : PASS")
        print("CLASS    :", type(instance).__name__)

    except Exception as exc:
        print("IMPORT   : FAIL")
        print(type(exc).__name__, str(exc))
        traceback.print_exc()

# ------------------------------------------------------------------
# SYNTHETIC INSTITUTIONAL INPUT
# ------------------------------------------------------------------

valuation = {
    "portfolio_value": 1_000_000.0,
    "currency": "INR",
}

performance = {
    "return_1d": 0.012,
    "return_1m": 0.035,
    "return_1y": 0.142,
}

risk = {
    "volatility": 0.18,
    "max_drawdown": 0.11,
    "var_95": 0.025,
}

positions = [
    {
        "symbol": "RELIANCE.NS",
        "quantity": 100,
        "price": 1500.0,
        "market_value": 150000.0,
    },
    {
        "symbol": "HDFCBANK.NS",
        "quantity": 100,
        "price": 1800.0,
        "market_value": 180000.0,
    },
]

scenarios = [
    {
        "scenario_id": "SYNTHETIC_MARKET_STRESS_01",
        "name": "Synthetic Market Stress",
        "shock_pct": -0.10,
    }
]

policy = {
    "allow_execution": False,
    "allow_broker_submission": False,
    "allow_live_execution": False,
    "allow_order_creation": False,
    "allow_portfolio_mutation": False,
    "allow_valuation_mutation": False,
    "allow_performance_mutation": False,
    "allow_risk_mutation": False,
    "allow_optimization": False,
}

print()
print("=" * 70)
print("PHASE 2 - SYNTHETIC INPUT")
print("=" * 70)

print("Portfolio Value :", valuation["portfolio_value"])
print("Positions       :", len(positions))
print("Scenarios       :", len(scenarios))
print("Execution       : DISABLED")
print("Broker          : DISABLED")
print("Mutation        : DISABLED")

# ------------------------------------------------------------------
# BLOCK 94
# ------------------------------------------------------------------

print()
print("=" * 70)
print("PHASE 3 - BLOCK 94")
print("=" * 70)

try:
    output94 = blocks[94].certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    show_output("BLOCK 94 OUTPUT", output94)

except Exception as exc:
    print("BLOCK 94 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    output94 = {}

# ------------------------------------------------------------------
# BLOCK 95
# ------------------------------------------------------------------

print()
print("=" * 70)
print("PHASE 4 - BLOCK 95")
print("=" * 70)

try:
    output95 = blocks[95].certify(
        stress_certificate=output94,
        policy=policy,
    )

    print("INPUT SOURCE : BLOCK 94")
    show_output("BLOCK 95 OUTPUT", output95)

except Exception as exc:
    print("BLOCK 95 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    output95 = {}

# ------------------------------------------------------------------
# BLOCK 96
# ------------------------------------------------------------------

print()
print("=" * 70)
print("PHASE 5 - BLOCK 96")
print("=" * 70)

try:
    output96 = blocks[96].certify(
        stress_gate=output95,
        policy=policy,
    )

    print("INPUT SOURCE : BLOCK 95")
    show_output("BLOCK 96 OUTPUT", output96)

except Exception as exc:
    print("BLOCK 96 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    output96 = {}

# ------------------------------------------------------------------
# BLOCK 97
# ------------------------------------------------------------------

print()
print("=" * 70)
print("PHASE 6 - BLOCK 97")
print("=" * 70)

try:
    output97 = blocks[97].certify(
        decision=output96,
    )

    print("INPUT SOURCE : BLOCK 96")
    show_output("BLOCK 97 OUTPUT", output97)

except Exception as exc:
    print("BLOCK 97 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    output97 = {}

# ------------------------------------------------------------------
# BLOCK 98
# ------------------------------------------------------------------

print()
print("=" * 70)
print("PHASE 7 - BLOCK 98")
print("=" * 70)

try:
    output98 = blocks[98].certify(
        decision=output97,
    )

    print("INPUT SOURCE : BLOCK 97")
    show_output("BLOCK 98 OUTPUT", output98)

except Exception as exc:
    print("BLOCK 98 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    output98 = {}

# ------------------------------------------------------------------
# BLOCK 99
# ------------------------------------------------------------------

print()
print("=" * 70)
print("PHASE 8 - BLOCK 99")
print("=" * 70)

try:
    output99 = blocks[99].certify(
        governance=output98,
    )

    print("INPUT SOURCE : BLOCK 98")
    show_output("BLOCK 99 OUTPUT", output99)

except Exception as exc:
    print("BLOCK 99 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    output99 = {}

# ------------------------------------------------------------------
# BLOCK 100
# ------------------------------------------------------------------

print()
print("=" * 70)
print("PHASE 9 - BLOCK 100")
print("=" * 70)

try:
    output100 = blocks[100].certify(
        intent=output99,
        fill_ratio=1.0,
    )

    print("INPUT SOURCE : BLOCK 99")
    show_output("BLOCK 100 OUTPUT", output100)

except Exception as exc:
    print("BLOCK 100 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    output100 = {}

# ------------------------------------------------------------------
# BLOCK 101
# ------------------------------------------------------------------

print()
print("=" * 70)
print("PHASE 10 - BLOCK 101")
print("=" * 70)

try:
    output101 = blocks[101].certify(
        execution=output100,
    )

    print("INPUT SOURCE : BLOCK 100")
    show_output("BLOCK 101 OUTPUT", output101)

except Exception as exc:
    print("BLOCK 101 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    output101 = {}

# ------------------------------------------------------------------
# CONTRACT HANDOFF SUMMARY
# ------------------------------------------------------------------

outputs = {
    94: output94,
    95: output95,
    96: output96,
    97: output97,
    98: output98,
    99: output99,
    100: output100,
    101: output101,
}

print()
print("=" * 80)
print("PHASE 11 - CONTRACT HANDOFF SUMMARY")
print("=" * 80)

for block, output in outputs.items():

    print()
    print(f"BLOCK {block}")

    if not isinstance(output, dict):
        print("OUTPUT : NON-DICT")
        continue

    print("STATUS :", output.get("status", "<ABSENT>"))
    print("KEYS   :", list(output.keys()))

    print()
    print("SAFETY FIELDS:")

    for field in [
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
    ]:
        print(f"  {field:28} : " f"{output.get(field, '<ABSENT>')!r}")

# ------------------------------------------------------------------
# SAFETY VERDICT
# ------------------------------------------------------------------

print()
print("=" * 80)
print("PHASE 12 - FINAL SAFETY VERDICT")
print("=" * 80)

expected_true = [
    "execution_blocked",
    "non_mutation_invariant",
]

expected_false = [
    "broker_submission",
    "live_order_submission",
    "portfolio_mutation",
    "valuation_mutation",
    "performance_mutation",
    "risk_mutation",
    "optimization",
    "order_creation",
]

failures = []

for block, output in outputs.items():

    if not isinstance(output, dict):
        failures.append(f"Block {block}: output is not a dictionary")
        continue

    for field in expected_true:
        if output.get(field) is not True:
            failures.append(
                f"Block {block}: {field} != True " f"(actual={output.get(field, '<ABSENT>')!r})"
            )

    for field in expected_false:
        if output.get(field) is not False:
            failures.append(
                f"Block {block}: {field} != False " f"(actual={output.get(field, '<ABSENT>')!r})"
            )

if failures:

    print("SAFETY : FAIL")
    print()
    for failure in failures:
        print(" -", failure)

else:

    print("SAFETY : PASS")
    print("All required safety fields satisfy the institutional boundary.")

print()
print("=" * 80)
print("BLOCK 94 -> 101 COMPLETE REAL DATA-FLOW TRACE FINISHED")
print("=" * 80)
print("READ ONLY")
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print("=" * 80)
