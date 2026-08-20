import importlib
import json
import traceback
from datetime import datetime

# ================================================================
# EROS 3.0
# BLOCK 94 -> 101 DEFINITIVE CONTRACT FLOW AUDIT
# READ ONLY / SYNTHETIC DATA ONLY
# ================================================================

EXPECTED_SAFETY = [
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

EXPECTED_FALSE_FIELDS = [
    "broker_submission",
    "live_order_submission",
    "portfolio_mutation",
    "valuation_mutation",
    "performance_mutation",
    "risk_mutation",
    "optimization",
    "order_creation",
]

EXPECTED_TRUE_FIELDS = [
    "execution_blocked",
    "non_mutation_invariant",
]

MODULES = {
    94: "services.quantitative.block94_portfolio_stress_scenario_engine",
    95: "services.quantitative.block95_stress_evidence_gate",
    96: "services.quantitative.block96_stress_decision_gate",
    97: "services.quantitative.block97_stress_readiness_gate",
    98: "services.quantitative.block98_execution_governance_bridge",
    99: "services.quantitative.block99_execution_intent_authorization_gate",
    100: "services.quantitative.block100_paper_execution_fill_gate",
    101: "services.quantitative.block101_execution_evidence_reconciliation",
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

report = []

def out(text=""):
    print(text)
    report.append(str(text))

def section(title):
    out()
    out("=" * 70)
    out(title)
    out("=" * 70)

def compact(value):
    if isinstance(value, dict):
        return {
            k: value[k]
            for k in value
            if k in EXPECTED_SAFETY
            or k in [
                "status",
                "block_id",
                "engine_version",
                "reason",
                "reason_code",
                "gate_status",
                "decision_status",
                "readiness_status",
                "governance_status",
                "intent_status",
                "execution_status",
                "reconciliation_status",
                "execution_id",
                "reconciliation_id",
            ]
        }
    return value

def inspect_safety(block_id, result):
    out()
    out(f"BLOCK {block_id} SAFETY CONTRACT")

    if not isinstance(result, dict):
        out("RESULT TYPE              : " + str(type(result)))
        out("SAFETY RESULT            : FAIL - result is not dict")
        return {
            "missing": EXPECTED_SAFETY,
            "wrong": ["result_not_dict"],
            "passed": False,
        }

    missing = []
    wrong = []

    for key in EXPECTED_SAFETY:
        if key not in result:
            missing.append(key)

    for key in EXPECTED_TRUE_FIELDS:
        if key in result and result[key] is not True:
            wrong.append(f"{key}={result[key]!r}")

    for key in EXPECTED_FALSE_FIELDS:
        if key in result and result[key] is not False:
            wrong.append(f"{key}={result[key]!r}")

    for key in EXPECTED_SAFETY:
        if key in result:
            out(f"  {key:28} : {result[key]!r}")
        else:
            out(f"  {key:28} : <ABSENT>")

    if missing:
        out("MISSING FIELDS            : " + ", ".join(missing))
    else:
        out("MISSING FIELDS            : NONE")

    if wrong:
        out("WRONG SAFETY VALUES       : " + ", ".join(wrong))
    else:
        out("WRONG SAFETY VALUES       : NONE")

    passed = not missing and not wrong

    out("SAFETY CONTRACT           : " + ("PASS" if passed else "FAIL"))

    return {
        "missing": missing,
        "wrong": wrong,
        "passed": passed,
    }

# ================================================================
# IMPORTS
# ================================================================

section("1. MODULE IMPORT AUDIT")

instances = {}
import_results = {}

for block_id, module_name in MODULES.items():

    try:
        module = importlib.import_module(module_name)
        class_name = CLASS_NAMES[block_id]
        cls = getattr(module, class_name)
        instance = cls()

        instances[block_id] = instance
        import_results[block_id] = True

        out(f"BLOCK {block_id:03d} : IMPORT PASS")
        out(f"           CLASS : {class_name}")

    except Exception as exc:

        import_results[block_id] = False

        out(f"BLOCK {block_id:03d} : IMPORT FAIL")
        out(f"           ERROR : {type(exc).__name__}: {exc}")

# ================================================================
# SYNTHETIC INPUT
# ================================================================

section("2. SYNTHETIC PORTFOLIO INPUT")

valuation = {
    "portfolio_value": 1_000_000.0,
    "cash": 300_000.0,
}

performance = {
    "daily_return": 0.012,
    "monthly_return": 0.035,
}

risk = {
    "volatility": 0.18,
    "max_drawdown": 0.12,
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
        "quantity": 50,
        "price": 3500.0,
        "market_value": 175000.0,
    },
]

scenarios = [
    {
        "scenario_id": "SYNTHETIC_MARKET_SHOCK",
        "name": "Synthetic Market Shock",
        "shock_pct": -10.0,
    }
]

out("Portfolio value : 1,000,000.00")
out("Cash            : 300,000.00")
out("Positions       : 2")
out("Scenarios       : 1")
out("DATA SOURCE     : SYNTHETIC")
out("LIVE DATA       : NO")

# ================================================================
# BLOCK 94
# ================================================================

section("3. BLOCK 94 - PORTFOLIO STRESS SCENARIO ENGINE")

chain = {}
safety_results = {}

try:

    b94 = instances[94]

    result94 = b94.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    chain[94] = result94

    out("CERTIFY                   : PASS")
    out("TYPE                      : " + str(type(result94)))
    out("STATUS                    : " + repr(result94.get("status")))
    out("BLOCK ID                  : " + repr(result94.get("block_id")))
    out("KEY COUNT                 : " + str(len(result94)))

    safety_results[94] = inspect_safety(94, result94)

except Exception as exc:

    out("BLOCK 94 EXECUTION        : FAIL")
    out(type(exc).__name__ + ": " + str(exc))
    traceback.print_exc()

# ================================================================
# BLOCK 95
# ================================================================

section("4. BLOCK 95 - STRESS EVIDENCE GATE")

try:

    b95 = instances[95]

    result95 = b95.certify(
        stress_certificate=result94
    )

    chain[95] = result95

    out("CERTIFY                   : PASS")
    out("TYPE                      : " + str(type(result95)))
    out("STATUS                    : " + repr(result95.get("status")))
    out("BLOCK ID                  : " + repr(result95.get("block_id")))
    out("KEY COUNT                 : " + str(len(result95)))

    safety_results[95] = inspect_safety(95, result95)

except Exception as exc:

    out("BLOCK 95 EXECUTION        : FAIL")
    out(type(exc).__name__ + ": " + str(exc))

# ================================================================
# BLOCK 96
# ================================================================

section("5. BLOCK 96 - STRESS DECISION GATE")

try:

    b96 = instances[96]

    result96 = b96.certify(
        stress_gate=result95
    )

    chain[96] = result96

    out("CERTIFY                   : PASS")
    out("TYPE                      : " + str(type(result96)))
    out("STATUS                    : " + repr(result96.get("status")))
    out("BLOCK ID                  : " + repr(result96.get("block_id")))
    out("KEY COUNT                 : " + str(len(result96)))

    safety_results[96] = inspect_safety(96, result96)

except Exception as exc:

    out("BLOCK 96 EXECUTION        : FAIL")
    out(type(exc).__name__ + ": " + str(exc))

# ================================================================
# BLOCK 97
# ================================================================

section("6. BLOCK 97 - STRESS READINESS GATE")

try:

    b97 = instances[97]

    result97 = b97.certify(
        decision=result96
    )

    chain[97] = result97

    out("CERTIFY                   : PASS")
    out("TYPE                      : " + str(type(result97)))
    out("STATUS                    : " + repr(result97.get("status")))
    out("BLOCK ID                  : " + repr(result97.get("block_id")))
    out("KEY COUNT                 : " + str(len(result97)))

    safety_results[97] = inspect_safety(97, result97)

except Exception as exc:

    out("BLOCK 97 EXECUTION        : FAIL")
    out(type(exc).__name__ + ": " + str(exc))

# ================================================================
# BLOCK 98
# ================================================================

section("7. BLOCK 98 - EXECUTION GOVERNANCE BRIDGE")

try:

    b98 = instances[98]

    result98 = b98.certify(
        decision=result97
    )

    chain[98] = result98

    out("CERTIFY                   : PASS")
    out("TYPE                      : " + str(type(result98)))
    out("STATUS                    : " + repr(result98.get("status")))
    out("BLOCK ID                  : " + repr(result98.get("block_id")))
    out("KEY COUNT                 : " + str(len(result98)))

    safety_results[98] = inspect_safety(98, result98)

except Exception as exc:

    out("BLOCK 98 EXECUTION        : FAIL")
    out(type(exc).__name__ + ": " + str(exc))

# ================================================================
# BLOCK 99
# ================================================================

section("8. BLOCK 99 - EXECUTION INTENT AUTHORIZATION")

try:

    b99 = instances[99]

    result99 = b99.certify(
        governance=result98
    )

    chain[99] = result99

    out("CERTIFY                   : PASS")
    out("TYPE                      : " + str(type(result99)))
    out("STATUS                    : " + repr(result99.get("status")))
    out("BLOCK ID                  : " + repr(result99.get("block_id")))
    out("KEY COUNT                 : " + str(len(result99)))

    safety_results[99] = inspect_safety(99, result99)

except Exception as exc:

    out("BLOCK 99 EXECUTION        : FAIL")
    out(type(exc).__name__ + ": " + str(exc))

# ================================================================
# BLOCK 100
# ================================================================

section("9. BLOCK 100 - PAPER EXECUTION FILL GATE")

try:

    b100 = instances[100]

    result100 = b100.certify(
        intent=result99,
        fill_ratio=1.0,
    )

    chain[100] = result100

    out("CERTIFY                   : PASS")
    out("TYPE                      : " + str(type(result100)))
    out("STATUS                    : " + repr(result100.get("status")))
    out("BLOCK ID                  : " + repr(result100.get("block_id")))
    out("EXECUTION ID             : " + repr(result100.get("execution_id")))
    out("KEY COUNT                 : " + str(len(result100)))

    safety_results[100] = inspect_safety(100, result100)

except Exception as exc:

    out("BLOCK 100 EXECUTION       : FAIL")
    out(type(exc).__name__ + ": " + str(exc))

# ================================================================
# BLOCK 101
# ================================================================

section("10. BLOCK 101 - EXECUTION EVIDENCE RECONCILIATION")

try:

    b101 = instances[101]

    result101 = b101.certify(
        execution=result100
    )

    chain[101] = result101

    out("CERTIFY                   : PASS")
    out("TYPE                      : " + str(type(result101)))
    out("STATUS                    : " + repr(result101.get("status")))
    out("BLOCK ID                  : " + repr(result101.get("block_id")))
    out("RECONCILIATION ID        : " + repr(result101.get("reconciliation_id")))
    out("KEY COUNT                 : " + str(len(result101)))

    safety_results[101] = inspect_safety(101, result101)

except Exception as exc:

    out("BLOCK 101 EXECUTION       : FAIL")
    out(type(exc).__name__ + ": " + str(exc))

# ================================================================
# CHAIN SUMMARY
# ================================================================

section("11. COMPLETE CHAIN SUMMARY")

for block_id in range(94, 102):

    result = chain.get(block_id)

    if result is None:
        out(f"BLOCK {block_id:03d} : NO RESULT")
        continue

    out(
        f"BLOCK {block_id:03d} : "
        f"status={result.get('status', '<ABSENT>')!r} "
        f"keys={len(result)}"
    )

# ================================================================
# SAFETY MATRIX
# ================================================================

section("12. SAFETY MATRIX")

for block_id in range(94, 102):

    result = chain.get(block_id)

    if result is None:
        out(f"BLOCK {block_id:03d} : NO RESULT")
        continue

    out()
    out(f"BLOCK {block_id:03d}")

    for key in EXPECTED_SAFETY:

        if key not in result:
            value = "<ABSENT>"
        else:
            value = repr(result[key])

        out(f"  {key:28} : {value}")

# ================================================================
# UNIFORMITY ANALYSIS
# ================================================================

section("13. UNIFORM SAFETY SCHEMA ANALYSIS")

all_missing = {}
all_wrong = {}

for block_id in range(94, 102):

    check = safety_results.get(block_id)

    if not check:
        all_missing[block_id] = EXPECTED_SAFETY
        all_wrong[block_id] = ["no_safety_result"]
        continue

    if check["missing"]:
        all_missing[block_id] = check["missing"]

    if check["wrong"]:
        all_wrong[block_id] = check["wrong"]

if not all_missing:
    out("MISSING SAFETY FIELDS     : NONE")
else:
    out("MISSING SAFETY FIELDS:")
    for block_id, fields in all_missing.items():
        out(f"  BLOCK {block_id}: {fields}")

if not all_wrong:
    out("WRONG SAFETY VALUES        : NONE")
else:
    out("WRONG SAFETY VALUES:")
    for block_id, fields in all_wrong.items():
        out(f"  BLOCK {block_id}: {fields}")

uniform_pass = not all_missing and not all_wrong

out()
out(
    "UNIFORM SAFETY CONTRACT    : "
    + ("PASS" if uniform_pass else "FAIL")
)

# ================================================================
# NON-MUTATION CHECK
# ================================================================

section("14. NON-MUTATION / EXECUTION SAFETY CHECK")

required_safe = {
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

global_safety_pass = True

for block_id in range(94, 102):

    result = chain.get(block_id)

    if not isinstance(result, dict):
        out(f"BLOCK {block_id}: FAIL - no dict result")
        global_safety_pass = False
        continue

    block_pass = True

    for key, expected in required_safe.items():

        actual = result.get(key, "<ABSENT>")

        if actual != expected:
            block_pass = False
            global_safety_pass = False
            out(
                f"BLOCK {block_id}: "
                f"{key} expected {expected!r}, got {actual!r}"
            )

    if block_pass:
        out(f"BLOCK {block_id}: SAFETY PASS")

out()
out(
    "GLOBAL NON-MUTATION SAFETY : "
    + ("PASS" if global_safety_pass else "FAIL")
)

# ================================================================
# FINAL CLASSIFICATION
# ================================================================

section("15. FINAL EROS 3.0 CLASSIFICATION")

if uniform_pass and global_safety_pass:

    final_status = "PASS - UNIFORM SAFE CONTRACT VERIFIED"

elif all(
    isinstance(chain.get(i), dict)
    for i in range(94, 102)
):
    final_status = "PARTIAL - CHAIN EXECUTES BUT SAFETY CONTRACT IS NOT UNIFORM"

else:

    final_status = "FAIL - COMPLETE CHAIN COULD NOT BE EXECUTED"

out("FINAL STATUS:")
out(final_status)

out()
out("ARCHITECTURAL INTERPRETATION:")

if final_status.startswith("PASS"):
    out("Block 94 -> 101 forms a uniform safe contract.")
    out("No live broker execution is exposed by this test.")
    out("No order creation is permitted by the tested contract.")
    out("No portfolio mutation is permitted by the tested contract.")

elif final_status.startswith("PARTIAL"):
    out("The blocks execute through the chain.")
    out("The remaining issue is contract/schema uniformity.")
    out("Do NOT patch blindly.")
    out("The next step is to normalize the safety contract deliberately.")

else:
    out("The chain requires further investigation before modification.")

# ================================================================
# TEST BOUNDARY
# ================================================================

section("16. TEST BOUNDARY")

out("SOURCE CHANGES            : NONE")
out("BROKER CONNECTION         : NONE")
out("LIVE EXECUTION            : NONE")
out("ORDER CREATION            : NONE")
out("PORTFOLIO MUTATION        : NONE")
out("LIVE MARKET DATA          : NONE")
out("INPUT DATA                : SYNTHETIC")
out("TEST TYPE                 : READ-ONLY CONTRACT AUDIT")

# ================================================================
# MACHINE-READABLE SUMMARY
# ================================================================

section("17. MACHINE SUMMARY")

summary = {
    "timestamp": datetime.now().isoformat(),
    "blocks_tested": list(range(94, 102)),
    "imports_passed": [
        block_id
        for block_id, passed in import_results.items()
        if passed
    ],
    "chain_blocks_returned": list(chain.keys()),
    "uniform_safety_contract": uniform_pass,
    "global_non_mutation_safety": global_safety_pass,
    "final_status": final_status,
}

out(json.dumps(summary, indent=2))

section("AUDIT COMPLETE")

out("COPY THIS ENTIRE REPORT BACK TO CHATGPT.")
out("NO SOURCE CHANGES WERE MADE.")
out("NO LIVE EXECUTION WAS PERFORMED.")

# ================================================================
# Write a copy into logs too
# ================================================================

try:
    with open(
        "logs/block94_101_definitive_contract_flow_report.txt",
        "w",
        encoding="utf-8",
    ) as f:
        f.write("\n".join(report))

except Exception:
    pass

