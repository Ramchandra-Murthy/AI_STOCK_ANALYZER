import json
import traceback
from datetime import datetime, timezone

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


# ============================================================
# CONFIGURATION
# ============================================================

REQUIRED_SAFETY_FIELDS = [
    "execution_blocked",
    "non_mutation_invariant",
    "broker_submission",
    "live_order_submission",
]

OPTIONAL_MUTATION_FIELDS = [
    "portfolio_mutation",
    "valuation_mutation",
    "performance_mutation",
    "risk_mutation",
    "optimization",
    "order_creation",
]

ALL_SAFETY_FIELDS = (
    REQUIRED_SAFETY_FIELDS +
    OPTIONAL_MUTATION_FIELDS
)


# ============================================================
# HELPERS
# ============================================================

def recursive_find(obj, target, path="root"):
    """
    Find every occurrence of target key recursively.
    """
    found = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            current = f"{path}.{key}"

            if key == target:
                found.append((current, value))

            found.extend(
                recursive_find(value, target, current)
            )

    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            current = f"{path}[{index}]"
            found.extend(
                recursive_find(value, target, current)
            )

    return found


def compact(value, limit=300):
    """
    Safe one-line representation.
    """
    try:
        text = repr(value)
    except Exception:
        text = "<repr-error>"

    if len(text) > limit:
        return text[:limit] + "...<TRUNCATED>"

    return text


def safety_analysis(block_id, result):
    """
    Analyze actual returned schema without modifying it.
    """

    analysis = {
        "block": block_id,
        "top_level_keys": [],
        "required": {},
        "optional": {},
        "nested_safety": [],
        "problems": [],
    }

    if not isinstance(result, dict):
        analysis["problems"].append(
            f"Returned object is {type(result).__name__}, not dict"
        )
        return analysis

    analysis["top_level_keys"] = list(result.keys())

    for field in REQUIRED_SAFETY_FIELDS:

        occurrences = recursive_find(result, field)

        if not occurrences:
            analysis["required"][field] = {
                "status": "MISSING",
                "locations": [],
                "values": [],
            }

            analysis["problems"].append(
                f"{field}: MISSING"
            )

        else:
            values = [value for _, value in occurrences]
            locations = [path for path, _ in occurrences]

            correct = all(
                value is True
                for value in values
            )

            analysis["required"][field] = {
                "status": "PASS" if correct else "WRONG_VALUE",
                "locations": locations,
                "values": values,
            }

            if not correct:
                analysis["problems"].append(
                    f"{field}: expected True, actual {values}"
                )

    for field in OPTIONAL_MUTATION_FIELDS:

        occurrences = recursive_find(result, field)

        if not occurrences:
            analysis["optional"][field] = {
                "status": "ABSENT",
            }
        else:
            analysis["optional"][field] = {
                "status": "PRESENT",
                "locations": [p for p, _ in occurrences],
                "values": [v for _, v in occurrences],
            }

    # Nested safety structures
    nested = recursive_find(result, "safety")

    for path, value in nested:
        analysis["nested_safety"].append({
            "path": path,
            "value": value,
        })

    return analysis


# ============================================================
# HEADER
# ============================================================

print("=" * 80)
print("EROS 3.0 - DEFINITIVE BLOCK 94-101 SAFETY CONTRACT TRACE")
print("=" * 80)

print()
print("TIMESTAMP :", datetime.now(timezone.utc).isoformat())
print("MODE      : READ ONLY")
print("BROKER    : DISABLED")
print("LIVE      : DISABLED")
print("ORDERS    : DISABLED")
print("MUTATION  : DISABLED")
print("SOURCE    : NO CHANGES")
print()

# ============================================================
# SYNTHETIC INPUT
# ============================================================

valuation = {
    "portfolio_value": 1_000_000.0,
    "currency": "INR",
}

performance = {
    "daily_return": 0.01,
    "weekly_return": 0.02,
    "monthly_return": 0.04,
}

risk = {
    "volatility": 0.18,
    "max_drawdown": 0.12,
    "var": 0.05,
}

positions = [
    {
        "symbol": "RELIANCE.NS",
        "quantity": 100,
        "price": 2500.0,
        "market_value": 250000.0,
    },
    {
        "symbol": "TCS.NS",
        "quantity": 100,
        "price": 3500.0,
        "market_value": 350000.0,
    },
]

scenarios = [
    {
        "scenario_id": "SYNTHETIC_STRESS_01",
        "name": "Synthetic Market Stress",
        "shock_pct": -0.10,
    }
]

print("=" * 80)
print("SYNTHETIC INPUT")
print("=" * 80)

print("Portfolio value :", valuation["portfolio_value"])
print("Positions       :", len(positions))
print("Scenarios       :", len(scenarios))
print()


# ============================================================
# INSTANTIATE ENGINES
# ============================================================

b94 = EROSBlock94PortfolioStressScenarioEngine()
b95 = EROSBlock95StressEvidenceGate()
b96 = EROSBlock96StressDecisionGate()
b97 = EROSBlock97StressReadinessGate()
b98 = EROSBlock98ExecutionGovernanceBridge()
b99 = EROSBlock99ExecutionIntentAuthorizationGate()
b100 = EROSBlock100PaperExecutionFillGate()
b101 = EROSBlock101ExecutionEvidenceReconciliationGate()


# ============================================================
# RESULT STORAGE
# ============================================================

results = {}
analyses = {}


# ============================================================
# BLOCK 94
# ============================================================

print("=" * 80)
print("BLOCK 94 - PORTFOLIO STRESS SCENARIO ENGINE")
print("=" * 80)

try:

    result94 = b94.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    results["94"] = result94

    print("EXECUTION : PASS")
    print("TYPE      :", type(result94))
    print("STATUS    :", result94.get("status"))
    print("TOP KEYS  :", list(result94.keys()))

    analyses["94"] = safety_analysis("94", result94)

except Exception as exc:

    print("EXECUTION : FAIL")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()

    result94 = {
        "status": "ERROR",
        "error": str(exc),
    }

    results["94"] = result94
    analyses["94"] = safety_analysis("94", result94)


# ============================================================
# BLOCK 95
# ============================================================

print()
print("=" * 80)
print("BLOCK 95 - STRESS EVIDENCE GATE")
print("=" * 80)

try:

    result95 = b95.certify(
        stress_certificate=result94,
    )

    results["95"] = result95

    print("EXECUTION : PASS")
    print("TYPE      :", type(result95))
    print("STATUS    :", result95.get("status"))
    print("TOP KEYS  :", list(result95.keys()))

    analyses["95"] = safety_analysis("95", result95)

except Exception as exc:

    print("EXECUTION : FAIL")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()

    result95 = {
        "status": "ERROR",
        "error": str(exc),
    }

    results["95"] = result95
    analyses["95"] = safety_analysis("95", result95)


# ============================================================
# BLOCK 96
# ============================================================

print()
print("=" * 80)
print("BLOCK 96 - STRESS DECISION GATE")
print("=" * 80)

try:

    result96 = b96.certify(
        stress_gate=result95,
    )

    results["96"] = result96

    print("EXECUTION : PASS")
    print("TYPE      :", type(result96))
    print("STATUS    :", result96.get("status"))
    print("TOP KEYS  :", list(result96.keys()))

    analyses["96"] = safety_analysis("96", result96)

except Exception as exc:

    print("EXECUTION : FAIL")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()

    result96 = {
        "status": "ERROR",
        "error": str(exc),
    }

    results["96"] = result96
    analyses["96"] = safety_analysis("96", result96)


# ============================================================
# BLOCK 97
# ============================================================

print()
print("=" * 80)
print("BLOCK 97 - STRESS READINESS GATE")
print("=" * 80)

try:

    result97 = b97.certify(
        decision=result96,
    )

    results["97"] = result97

    print("EXECUTION : PASS")
    print("TYPE      :", type(result97))
    print("STATUS    :", result97.get("status"))
    print("TOP KEYS  :", list(result97.keys()))

    analyses["97"] = safety_analysis("97", result97)

except Exception as exc:

    print("EXECUTION : FAIL")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()

    result97 = {
        "status": "ERROR",
        "error": str(exc),
    }

    results["97"] = result97
    analyses["97"] = safety_analysis("97", result97)


# ============================================================
# BLOCK 98
# ============================================================

print()
print("=" * 80)
print("BLOCK 98 - EXECUTION GOVERNANCE BRIDGE")
print("=" * 80)

try:

    result98 = b98.certify(
        decision=result97,
    )

    results["98"] = result98

    print("EXECUTION : PASS")
    print("TYPE      :", type(result98))
    print("STATUS    :", result98.get("status"))
    print("TOP KEYS  :", list(result98.keys()))

    analyses["98"] = safety_analysis("98", result98)

except Exception as exc:

    print("EXECUTION : FAIL")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()

    result98 = {
        "status": "ERROR",
        "error": str(exc),
    }

    results["98"] = result98
    analyses["98"] = safety_analysis("98", result98)


# ============================================================
# BLOCK 99
# ============================================================

print()
print("=" * 80)
print("BLOCK 99 - EXECUTION INTENT AUTHORIZATION")
print("=" * 80)

try:

    result99 = b99.certify(
        governance=result98,
    )

    results["99"] = result99

    print("EXECUTION : PASS")
    print("TYPE      :", type(result99))
    print("STATUS    :", result99.get("status"))
    print("TOP KEYS  :", list(result99.keys()))

    analyses["99"] = safety_analysis("99", result99)

except Exception as exc:

    print("EXECUTION : FAIL")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()

    result99 = {
        "status": "ERROR",
        "error": str(exc),
    }

    results["99"] = result99
    analyses["99"] = safety_analysis("99", result99)


# ============================================================
# BLOCK 100
# ============================================================

print()
print("=" * 80)
print("BLOCK 100 - PAPER EXECUTION FILL GATE")
print("=" * 80)

try:

    result100 = b100.certify(
        intent=result99,
        fill_ratio=1.0,
    )

    results["100"] = result100

    print("EXECUTION : PASS")
    print("TYPE      :", type(result100))
    print("STATUS    :", result100.get("status"))
    print("TOP KEYS  :", list(result100.keys()))

    analyses["100"] = safety_analysis("100", result100)

except Exception as exc:

    print("EXECUTION : FAIL")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()

    result100 = {
        "status": "ERROR",
        "error": str(exc),
    }

    results["100"] = result100
    analyses["100"] = safety_analysis("100", result100)


# ============================================================
# BLOCK 101
# ============================================================

print()
print("=" * 80)
print("BLOCK 101 - EXECUTION EVIDENCE RECONCILIATION")
print("=" * 80)

try:

    result101 = b101.certify(
        execution=result100,
    )

    results["101"] = result101

    print("EXECUTION : PASS")
    print("TYPE      :", type(result101))
    print("STATUS    :", result101.get("status"))
    print("TOP KEYS  :", list(result101.keys()))

    analyses["101"] = safety_analysis("101", result101)

except Exception as exc:

    print("EXECUTION : FAIL")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()

    result101 = {
        "status": "ERROR",
        "error": str(exc),
    }

    results["101"] = result101
    analyses["101"] = safety_analysis("101", result101)


# ============================================================
# ACTUAL RESULT SUMMARY
# ============================================================

print()
print("=" * 80)
print("ACTUAL SAFETY FIELD SUMMARY")
print("=" * 80)

overall_pass = True

for block_id in [
    "94",
    "95",
    "96",
    "97",
    "98",
    "99",
    "100",
    "101",
]:

    analysis = analyses.get(block_id, {})

    print()
    print(f"BLOCK {block_id}")
    print("-" * 80)

    problems = analysis.get("problems", [])

    if problems:
        overall_pass = False

        print("STATUS : FAIL")

        for problem in problems:
            print("  PROBLEM :", problem)

    else:
        print("STATUS : PASS")

    print()
    print("REQUIRED SAFETY FIELDS:")

    for field in REQUIRED_SAFETY_FIELDS:

        info = analysis.get("required", {}).get(field)

        if info is None:
            print(
                f"  {field:28} : <NOT ANALYZED>"
            )
            overall_pass = False
            continue

        print(
            f"  {field:28} : "
            f"{info.get('status')} "
            f"values={info.get('values')}"
        )

        if info.get("status") != "PASS":
            overall_pass = False

    print()
    print("OPTIONAL MUTATION FIELDS:")

    for field in OPTIONAL_MUTATION_FIELDS:

        info = analysis.get("optional", {}).get(field)

        if info is None:
            continue

        print(
            f"  {field:28} : "
            f"{info.get('status')} "
            f"values={info.get('values', '')}"
        )


# ============================================================
# TOP-LEVEL SCHEMA TRACE
# ============================================================

print()
print("=" * 80)
print("TOP-LEVEL SCHEMA TRACE")
print("=" * 80)

for block_id, result in results.items():

    print()
    print(f"BLOCK {block_id}")

    if isinstance(result, dict):

        print("TOP LEVEL KEYS:")

        for key in result.keys():
            print("  ", key)

        print()
        print("TOP LEVEL SAFETY VALUES:")

        for field in ALL_SAFETY_FIELDS:

            print(
                f"  {field:28} : "
                f"{result.get(field, '<ABSENT>')!r}"
            )

    else:

        print(
            "RESULT TYPE:",
            type(result).__name__
        )


# ============================================================
# NESTED SAFETY TRACE
# ============================================================

print()
print("=" * 80)
print("NESTED SAFETY TRACE")
print("=" * 80)

for block_id, analysis in analyses.items():

    print()
    print(f"BLOCK {block_id}")

    nested = analysis.get(
        "nested_safety",
        []
    )

    if not nested:

        print("  No nested 'safety' object found.")

    else:

        for item in nested:

            print(
                "  PATH :",
                item["path"]
            )

            print(
                "  VALUE:",
                compact(item["value"], 1000)
            )


# ============================================================
# BLOCK-TO-BLOCK HANDOFF
# ============================================================

print()
print("=" * 80)
print("BLOCK-TO-BLOCK HANDOFF TRACE")
print("=" * 80)

handoffs = [
    ("94", "95", "stress_certificate"),
    ("95", "96", "stress_gate"),
    ("96", "97", "decision"),
    ("97", "98", "decision"),
    ("98", "99", "governance"),
    ("99", "100", "intent"),
    ("100", "101", "execution"),
]

for source, target, argument in handoffs:

    source_result = results.get(source)

    print()
    print(
        f"BLOCK {source} -> BLOCK {target}"
    )

    print(
        "HANDOFF ARGUMENT :",
        argument
    )

    if isinstance(source_result, dict):

        print(
            "SOURCE STATUS    :",
            source_result.get("status")
        )

        print(
            "SOURCE KEYS      :",
            list(source_result.keys())
        )

        print(
            "SAFETY           :",
            {
                field: source_result.get(
                    field,
                    "<ABSENT>"
                )
                for field in REQUIRED_SAFETY_FIELDS
            }
        )

    else:

        print(
            "SOURCE RESULT    :",
            type(source_result).__name__
        )


# ============================================================
# FULL RETURN OBJECTS
# ============================================================

print()
print("=" * 80)
print("FULL RETURN OBJECTS")
print("=" * 80)

for block_id, result in results.items():

    print()
    print(
        f"----- BLOCK {block_id} RETURN OBJECT -----"
    )

    try:

        print(
            json.dumps(
                result,
                indent=2,
                default=str,
                sort_keys=False,
            )
        )

    except Exception as exc:

        print(
            "JSON SERIALIZATION ERROR:",
            type(exc).__name__,
            str(exc)
        )

        print(
            repr(result)
        )


# ============================================================
# FINAL DIAGNOSIS
# ============================================================

print()
print("=" * 80)
print("FINAL DIAGNOSIS")
print("=" * 80)

if overall_pass:

    print()
    print("SAFETY CONTRACT : PASS")
    print()
    print(
        "All required safety fields were found"
    )
    print(
        "and evaluated to True."
    )

else:

    print()
    print("SAFETY CONTRACT : FAIL")
    print()
    print(
        "The architecture currently has a"
    )
    print(
        "safety-schema contract mismatch."
    )
    print()
    print(
        "This diagnostic does NOT modify source."
    )
    print(
        "Do NOT patch Blocks 94-101 yet."
    )
    print(
        "Use the exact field locations and values"
    )
    print(
        "above to determine the correct contract."
    )


# ============================================================
# SAFETY BOUNDARY
# ============================================================

print()
print("=" * 80)
print("SAFETY BOUNDARY")
print("=" * 80)

print("SOURCE CHANGES       : NONE")
print("BROKER CONNECTION    : NONE")
print("LIVE EXECUTION       : NONE")
print("ORDER CREATION       : NONE")
print("PORTFOLIO MUTATION   : NONE")
print("VALUATION MUTATION   : NONE")
print("PERFORMANCE MUTATION : NONE")
print("RISK MUTATION        : NONE")
print("OPTIMIZATION         : NONE")

print()
print("=" * 80)
print("DEFINITIVE TRACE COMPLETE")
print("=" * 80)

