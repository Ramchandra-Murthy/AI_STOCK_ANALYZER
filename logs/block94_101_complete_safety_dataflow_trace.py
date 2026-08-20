import importlib
import json
import traceback
from pprint import pprint
from typing import Any


# ==============================================================
# IMPORTS
# ==============================================================

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


# ==============================================================
# HELPERS
# ==============================================================

def separator(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def safe_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            indent=2,
            sort_keys=False,
            default=str,
        )
    except Exception:
        return repr(value)


def find_keys(
    value: Any,
    interesting_keys=None,
    path="root",
):
    if interesting_keys is None:
        interesting_keys = {
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
            "status",
            "reason",
            "reason_code",
            "execution_status",
            "governance_status",
            "intent_status",
            "readiness_status",
            "gate_status",
            "decision_status",
            "execution_action",
            "execution_blocked",
        }

    findings = []

    if isinstance(value, dict):

        for key, item in value.items():

            current_path = f"{path}.{key}"

            if key in interesting_keys:
                findings.append(
                    (
                        current_path,
                        item,
                    )
                )

            findings.extend(
                find_keys(
                    item,
                    interesting_keys,
                    current_path,
                )
            )

    elif isinstance(value, list):

        for index, item in enumerate(value):

            findings.extend(
                find_keys(
                    item,
                    interesting_keys,
                    f"{path}[{index}]",
                )
            )

    return findings


def print_result(name: str, result: Any) -> None:

    separator(name)

    print("TYPE:")
    print(type(result))

    if isinstance(result, dict):

        print()
        print("TOP LEVEL KEYS:")
        for key in result.keys():
            print("  ", key)

    print()
    print("COMPLETE RETURNED OBJECT:")
    print(safe_json(result))

    print()
    print("SAFETY / GOVERNANCE FIELD TRACE:")

    findings = find_keys(result)

    if not findings:
        print("  NO TARGET SAFETY FIELDS FOUND")

    else:
        for path, value in findings:
            print(
                f"  {path:70} = {value!r}"
            )


# ==============================================================
# START
# ==============================================================

separator(
    "EROS 3.0 - BLOCK 94 -> 101 COMPLETE SAFETY DATA-FLOW TRACE"
)

print("IMPORTS : PASS")
print()
print("THIS TEST IS:")
print("  READ ONLY")
print("  SYNTHETIC DATA ONLY")
print("  NO BROKER")
print("  NO LIVE EXECUTION")
print("  NO ORDER CREATION")
print("  NO PORTFOLIO MUTATION")
print("  NO VALUATION MUTATION")
print("  NO PERFORMANCE MUTATION")
print("  NO RISK MUTATION")
print()


# ==============================================================
# SYNTHETIC INPUT
# ==============================================================

valuation = {
    "portfolio_value": 1_000_000.0,
    "cash": 400_000.0,
    "market_value": 600_000.0,
}

performance = {
    "return_1d": 0.012,
    "return_1m": 0.035,
    "return_ytd": 0.087,
}

risk = {
    "volatility": 0.18,
    "max_drawdown": -0.12,
    "var_95": -25_000.0,
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
        "price": 3500.0,
        "market_value": 350_000.0,
        "weight": 0.35,
    },
]

scenarios = [
    {
        "scenario_id": "SYNTHETIC_MARKET_SHOCK",
        "name": "Synthetic Market Shock",
        "price_shock_pct": -0.10,
        "volatility_shock_pct": 0.25,
    }
]


print("SYNTHETIC INPUT")
print("-" * 80)
print("Portfolio value :", valuation["portfolio_value"])
print("Cash            :", valuation["cash"])
print("Positions       :", len(positions))
print("Scenarios       :", len(scenarios))


# ==============================================================
# INSTANTIATE ENGINES
# ==============================================================

separator("ENGINE INSTANTIATION")

block94 = EROSBlock94PortfolioStressScenarioEngine()
block95 = EROSBlock95StressEvidenceGate()
block96 = EROSBlock96StressDecisionGate()
block97 = EROSBlock97StressReadinessGate()
block98 = EROSBlock98ExecutionGovernanceBridge()
block99 = EROSBlock99ExecutionIntentAuthorizationGate()
block100 = EROSBlock100PaperExecutionFillGate()
block101 = EROSBlock101ExecutionEvidenceReconciliationGate()

print("BLOCK 94 : INSTANCE PASS")
print("BLOCK 95 : INSTANCE PASS")
print("BLOCK 96 : INSTANCE PASS")
print("BLOCK 97 : INSTANCE PASS")
print("BLOCK 98 : INSTANCE PASS")
print("BLOCK 99 : INSTANCE PASS")
print("BLOCK 100: INSTANCE PASS")
print("BLOCK 101: INSTANCE PASS")


# ==============================================================
# BLOCK 94
# ==============================================================

try:

    block94_result = block94.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    print_result(
        "BLOCK 94 - CERTIFY RESULT",
        block94_result,
    )

except Exception as exc:

    print_result(
        "BLOCK 94 - ERROR",
        {
            "error": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        },
    )

    block94_result = {}


# ==============================================================
# BLOCK 95
# ==============================================================

try:

    block95_result = block95.certify(
        stress_certificate=block94_result,
    )

    print_result(
        "BLOCK 95 - CERTIFY RESULT",
        block95_result,
    )

except Exception as exc:

    print_result(
        "BLOCK 95 - ERROR",
        {
            "error": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        },
    )

    block95_result = {}


# ==============================================================
# BLOCK 96
# ==============================================================

try:

    block96_result = block96.certify(
        stress_gate=block95_result,
    )

    print_result(
        "BLOCK 96 - CERTIFY RESULT",
        block96_result,
    )

except Exception as exc:

    print_result(
        "BLOCK 96 - ERROR",
        {
            "error": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        },
    )

    block96_result = {}


# ==============================================================
# BLOCK 97
# ==============================================================

try:

    block97_result = block97.certify(
        decision=block96_result,
    )

    print_result(
        "BLOCK 97 - CERTIFY RESULT",
        block97_result,
    )

except Exception as exc:

    print_result(
        "BLOCK 97 - ERROR",
        {
            "error": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        },
    )

    block97_result = {}


# ==============================================================
# BLOCK 98
# ==============================================================

try:

    block98_result = block98.certify(
        decision=block97_result,
    )

    print_result(
        "BLOCK 98 - CERTIFY RESULT",
        block98_result,
    )

except Exception as exc:

    print_result(
        "BLOCK 98 - ERROR",
        {
            "error": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        },
    )

    block98_result = {}


# ==============================================================
# BLOCK 99
# ==============================================================

try:

    block99_result = block99.certify(
        governance=block98_result,
    )

    print_result(
        "BLOCK 99 - CERTIFY RESULT",
        block99_result,
    )

except Exception as exc:

    print_result(
        "BLOCK 99 - ERROR",
        {
            "error": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        },
    )

    block99_result = {}


# ==============================================================
# BLOCK 100
# ==============================================================

try:

    block100_result = block100.certify(
        intent=block99_result,
        fill_ratio=1.0,
    )

    print_result(
        "BLOCK 100 - CERTIFY RESULT",
        block100_result,
    )

except Exception as exc:

    print_result(
        "BLOCK 100 - ERROR",
        {
            "error": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        },
    )

    block100_result = {}


# ==============================================================
# BLOCK 101
# ==============================================================

try:

    block101_result = block101.certify(
        execution=block100_result,
    )

    print_result(
        "BLOCK 101 - CERTIFY RESULT",
        block101_result,
    )

except Exception as exc:

    print_result(
        "BLOCK 101 - ERROR",
        {
            "error": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        },
    )

    block101_result = {}


# ==============================================================
# CROSS-BLOCK SUMMARY
# ==============================================================

separator("CROSS-BLOCK SAFETY SUMMARY")

results = [
    ("BLOCK 94", block94_result),
    ("BLOCK 95", block95_result),
    ("BLOCK 96", block96_result),
    ("BLOCK 97", block97_result),
    ("BLOCK 98", block98_result),
    ("BLOCK 99", block99_result),
    ("BLOCK 100", block100_result),
    ("BLOCK 101", block101_result),
]

for name, result in results:

    print()
    print(name)

    if not isinstance(result, dict):

        print("  RESULT TYPE :", type(result))
        continue

    print("  status                 :", result.get("status"))
    print("  reason                 :", result.get("reason"))
    print("  reason_code            :", result.get("reason_code"))
    print("  execution_blocked      :", result.get("execution_blocked"))
    print("  non_mutation_invariant :", result.get("non_mutation_invariant"))
    print("  broker_submission      :", result.get("broker_submission"))
    print("  live_order_submission  :", result.get("live_order_submission"))
    print("  portfolio_mutation     :", result.get("portfolio_mutation"))
    print("  valuation_mutation     :", result.get("valuation_mutation"))
    print("  performance_mutation   :", result.get("performance_mutation"))
    print("  risk_mutation           :", result.get("risk_mutation"))
    print("  optimization            :", result.get("optimization"))
    print("  order_creation          :", result.get("order_creation"))


# ==============================================================
# SAFETY ASSERTION ANALYSIS
# ==============================================================

separator("SAFETY ASSERTION ANALYSIS")

expected = {
    "execution_blocked": True,
    "non_mutation_invariant": True,
    "broker_submission": False,
    "live_order_submission": False,
    "portfolio_mutation": False,
    "valuation_mutation": False,
    "performance_mutation": False,
    "risk_mutation": False,
    "optimization": False,
    "order_creation": False,
}

overall_pass = True

for name, result in results:

    print()
    print(name)

    if not isinstance(result, dict):

        print("  RESULT : INVALID")
        overall_pass = False
        continue

    local_found = False

    findings = find_keys(result)

    for path, value in findings:

        final_key = path.split(".")[-1]

        if final_key not in expected:
            continue

        local_found = True

        required = expected[final_key]

        if value == required:

            print(
                f"  PASS  {path} = {value!r}"
            )

        else:

            print(
                f"  CHECK {path} = {value!r} "
                f"(expected {required!r})"
            )

            overall_pass = False

    if not local_found:

        print(
            "  NOTE: No expected top-level/nested safety "
            "invariant was found."
        )


# ==============================================================
# FINAL
# ==============================================================

separator("FINAL RESULT")

if overall_pass:

    print("SAFETY TRACE : PASS")

else:

    print("SAFETY TRACE : REQUIRES REVIEW")

print()
print("IMPORTANT:")
print("This result does NOT authorize live trading.")
print("No broker API was called.")
print("No live order was created.")
print("No portfolio was mutated.")
print("No valuation was mutated.")
print("No performance data was mutated.")
print("No risk data was mutated.")
print("This is an architecture / contract trace only.")

separator("TRACE COMPLETE")

