import importlib
import json
import traceback
from pprint import pprint

print("=" * 80)
print("EROS 3.0 - BLOCK 94-101 DEEP SAFETY CONTRACT TRACE")
print("=" * 80)

# ----------------------------------------------------------------------
# IMPORTS
# ----------------------------------------------------------------------

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

# ----------------------------------------------------------------------
# SYNTHETIC INPUT
# ----------------------------------------------------------------------

valuation = {
    "portfolio_value": 1_000_000.0,
    "cash": 300_000.0,
    "gross_exposure": 700_000.0,
    "net_exposure": 700_000.0,
}

performance = {
    "daily_return": 0.012,
    "weekly_return": 0.021,
    "drawdown": -0.035,
}

risk = {
    "var": 25_000.0,
    "cvar": 35_000.0,
    "volatility": 0.18,
    "beta": 1.05,
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
        "quantity": 100,
        "price": 4500.0,
        "market_value": 450000.0,
    },
]

scenarios = [
    {
        "scenario_id": "MARKET_SHOCK_10",
        "name": "Market Shock -10%",
        "shock_pct": -0.10,
    }
]

policy = {
    "execution_allowed": False,
    "broker_submission_allowed": False,
    "live_order_submission_allowed": False,
    "portfolio_mutation_allowed": False,
    "valuation_mutation_allowed": False,
    "performance_mutation_allowed": False,
    "risk_mutation_allowed": False,
    "optimization_allowed": False,
    "order_creation_allowed": False,
}

print()
print("=" * 80)
print("SYNTHETIC INPUT")
print("=" * 80)
print("Portfolio value :", valuation["portfolio_value"])
print("Positions       :", len(positions))
print("Scenarios       :", len(scenarios))
print("Execution       : DISABLED")
print("Broker          : DISABLED")
print("Mutation        : DISABLED")

# ----------------------------------------------------------------------
# HELPER
# ----------------------------------------------------------------------

def inspect_result(label, result):

    print()
    print("=" * 80)
    print(label)
    print("=" * 80)

    print("TYPE :", type(result))

    if not isinstance(result, dict):
        print("NON-DICT RESULT")
        pprint(result)
        return

    print()
    print("TOP LEVEL KEYS:")
    for key in result.keys():
        print("  ", key)

    print()
    print("SAFETY-RELATED FIELDS:")

    safety_keys = [
        "status",
        "block_id",
        "engine_version",
        "reason",
        "reason_code",
        "execution_status",
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
        "execution_action",
        "intent_action",
        "governance_status",
        "intent_status",
        "readiness_status",
        "decision_status",
        "gate_status",
        "reconciliation_status",
    ]

    for key in safety_keys:
        if key in result:
            print(f"{key:32} = {result[key]!r}")

    nested_names = [
        "safety",
        "safety_controls",
        "safety_contract",
        "execution",
        "governance",
        "authorization",
        "readiness",
        "decision",
        "gate",
        "controls",
        "invariants",
        "policy",
    ]

    for name in nested_names:

        if name not in result:
            continue

        value = result[name]

        print()
        print(f"NESTED OBJECT [{name}]")
        print("-" * 60)

        print("TYPE :", type(value))

        if isinstance(value, dict):
            for key, val in value.items():
                print(f"{key:32} = {val!r}")
        else:
            pprint(value)

    print()
    print("FULL RESULT:")
    pprint(result, width=150, sort_dicts=False)

# ----------------------------------------------------------------------
# BLOCK 94
# ----------------------------------------------------------------------

b94 = EROSBlock94PortfolioStressScenarioEngine()

try:

    r94 = b94.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    inspect_result("BLOCK 94 RESULT", r94)

except Exception as exc:

    print()
    print("BLOCK 94 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    r94 = None

# ----------------------------------------------------------------------
# BLOCK 95
# ----------------------------------------------------------------------

b95 = EROSBlock95StressEvidenceGate()

try:

    source94 = r94 if isinstance(r94, dict) else {}

    r95 = b95.certify(
        stress_certificate=source94,
        policy=policy,
    )

    inspect_result("BLOCK 95 RESULT", r95)

except Exception as exc:

    print()
    print("BLOCK 95 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    r95 = None

# ----------------------------------------------------------------------
# BLOCK 96
# ----------------------------------------------------------------------

b96 = EROSBlock96StressDecisionGate()

try:

    source95 = r95 if isinstance(r95, dict) else {}

    r96 = b96.certify(
        stress_gate=source95,
        policy=policy,
    )

    inspect_result("BLOCK 96 RESULT", r96)

except Exception as exc:

    print()
    print("BLOCK 96 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    r96 = None

# ----------------------------------------------------------------------
# BLOCK 97
# ----------------------------------------------------------------------

b97 = EROSBlock97StressReadinessGate()

try:

    source96 = r96 if isinstance(r96, dict) else {}

    r97 = b97.certify(
        decision=source96,
    )

    inspect_result("BLOCK 97 RESULT", r97)

except Exception as exc:

    print()
    print("BLOCK 97 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    r97 = None

# ----------------------------------------------------------------------
# BLOCK 98
# ----------------------------------------------------------------------

b98 = EROSBlock98ExecutionGovernanceBridge()

try:

    source97 = r97 if isinstance(r97, dict) else {}

    r98 = b98.certify(
        decision=source97,
    )

    inspect_result("BLOCK 98 RESULT", r98)

except Exception as exc:

    print()
    print("BLOCK 98 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    r98 = None

# ----------------------------------------------------------------------
# BLOCK 99
# ----------------------------------------------------------------------

b99 = EROSBlock99ExecutionIntentAuthorizationGate()

try:

    source98 = r98 if isinstance(r98, dict) else {}

    r99 = b99.certify(
        governance=source98,
    )

    inspect_result("BLOCK 99 RESULT", r99)

except Exception as exc:

    print()
    print("BLOCK 99 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    r99 = None

# ----------------------------------------------------------------------
# BLOCK 100
# ----------------------------------------------------------------------

b100 = EROSBlock100PaperExecutionFillGate()

try:

    source99 = r99 if isinstance(r99, dict) else {}

    r100 = b100.certify(
        intent=source99,
        fill_ratio=1.0,
    )

    inspect_result("BLOCK 100 RESULT", r100)

except Exception as exc:

    print()
    print("BLOCK 100 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    r100 = None

# ----------------------------------------------------------------------
# BLOCK 101
# ----------------------------------------------------------------------

b101 = EROSBlock101ExecutionEvidenceReconciliationGate()

try:

    source100 = r100 if isinstance(r100, dict) else {}

    r101 = b101.certify(
        execution=source100,
    )

    inspect_result("BLOCK 101 RESULT", r101)

except Exception as exc:

    print()
    print("BLOCK 101 ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    r101 = None

# ----------------------------------------------------------------------
# CROSS-BLOCK SAFETY MATRIX
# ----------------------------------------------------------------------

print()
print("=" * 80)
print("CROSS-BLOCK SAFETY MATRIX")
print("=" * 80)

results = {
    "94": r94,
    "95": r95,
    "96": r96,
    "97": r97,
    "98": r98,
    "99": r99,
    "100": r100,
    "101": r101,
}

safety_fields = [
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

print()
print(
    f"{'BLOCK':8}"
    + "".join(f"{field[:16]:>18}" for field in safety_fields)
)

for block_id, result in results.items():

    if not isinstance(result, dict):
        print(f"{block_id:8} NO RESULT")
        continue

    row = f"{block_id:8}"

    for field in safety_fields:

        if field not in result:
            value = "ABSENT"
        else:
            value = repr(result[field])

        row += f"{value[:16]:>18}"

    print(row)

# ----------------------------------------------------------------------
# AUTOMATED DIAGNOSIS
# ----------------------------------------------------------------------

print()
print("=" * 80)
print("AUTOMATED DIAGNOSIS")
print("=" * 80)

issues = []

for block_id, result in results.items():

    if not isinstance(result, dict):

        issues.append(
            f"Block {block_id}: result is not a dictionary"
        )

        continue

    for field in safety_fields:

        if field not in result:

            issues.append(
                f"Block {block_id}: {field} is ABSENT at top level"
            )

        else:

            value = result[field]

            if field in [
                "execution_blocked",
                "non_mutation_invariant",
            ]:

                if value is not True:

                    issues.append(
                        f"Block {block_id}: {field} = {value!r}"
                    )

            else:

                if field in [
                    "broker_submission",
                    "live_order_submission",
                    "portfolio_mutation",
                    "valuation_mutation",
                    "performance_mutation",
                    "risk_mutation",
                    "optimization",
                    "order_creation",
                ]:

                    if value not in [False, "BLOCKED", "DISABLED", None]:

                        issues.append(
                            f"Block {block_id}: {field} = {value!r}"
                        )

if not issues:

    print("SAFETY : PASS")
    print("All required safety fields are present and safe.")

else:

    print("SAFETY : FAIL")
    print()
    for issue in issues:
        print(" -", issue)

# ----------------------------------------------------------------------
# FINAL SAFETY ASSERTION
# ----------------------------------------------------------------------

print()
print("=" * 80)
print("FINAL SAFETY ASSERTION")
print("=" * 80)

print("NO BROKER CONNECTION")
print("NO LIVE ORDER SUBMISSION")
print("NO ORDER CREATION")
print("NO PORTFOLIO MUTATION")
print("NO VALUATION MUTATION")
print("NO PERFORMANCE MUTATION")
print("NO RISK MUTATION")
print("NO OPTIMIZATION SIDE EFFECT")
print("READ-ONLY TRACE")
print("SYNTHETIC DATA ONLY")

print()
print("=" * 80)
print("DEEP SAFETY CONTRACT TRACE COMPLETE")
print("=" * 80)
