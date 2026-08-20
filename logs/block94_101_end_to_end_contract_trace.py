import importlib
import json
from pprint import pprint

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

lines = []

def out(text=""):
    print(text)
    lines.append(str(text))

def section(title):
    out()
    out("=" * 76)
    out(title)
    out("=" * 76)

def inspect_result(label, result):
    out()
    out(f"----- {label} -----")
    out("TYPE : " + str(type(result)))

    if isinstance(result, dict):
        out("TOP LEVEL KEYS:")
        for key in result.keys():
            out(f"  {key}")

        out()
        out("IMPORTANT SAFETY / CONTROL FIELDS:")

        safety_keys = [
            "status",
            "gate_status",
            "decision_status",
            "readiness_status",
            "governance_status",
            "intent_status",
            "execution_status",
            "reconciliation_status",
            "reason",
            "reason_code",
            "execution_action",
            "intent_action",
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
            "execution_id",
            "source_block",
            "source_intent_id",
            "source_readiness_id",
            "source_governance_id",
        ]

        for key in safety_keys:
            if key in result:
                out(f"{key:30} = {result[key]!r}")

        out()
        out("FULL RESULT:")
        pprint(result, width=140, sort_dicts=False)

    else:
        out("VALUE:")
        pprint(result, width=140, sort_dicts=False)


# ============================================================
# IMPORTS
# ============================================================

section("1. MODULE IMPORT VALIDATION")

loaded = {}

for block_id, module_name in MODULES.items():
    try:
        module = importlib.import_module(module_name)
        loaded[block_id] = module
        out(f"BLOCK {block_id}: IMPORT PASS")
    except Exception as exc:
        out(f"BLOCK {block_id}: IMPORT FAIL")
        out(f"  {type(exc).__name__}: {exc}")


# ============================================================
# INSTANCE CREATION
# ============================================================

section("2. EROS INSTANCE VALIDATION")

instances = {}

for block_id, module in loaded.items():
    class_name = CLASS_NAMES[block_id]

    try:
        cls = getattr(module, class_name)
        instance = cls()
        instances[block_id] = instance
        out(f"BLOCK {block_id}: INSTANCE PASS")
    except Exception as exc:
        out(f"BLOCK {block_id}: INSTANCE FAIL")
        out(f"  {type(exc).__name__}: {exc}")


# ============================================================
# SYNTHETIC INPUT
# ============================================================

section("3. SYNTHETIC INPUT")

valuation = {
    "portfolio_value": 1_000_000.0,
    "cash": 250_000.0,
}

performance = {
    "daily_return": -0.012,
    "drawdown": 0.08,
}

risk = {
    "volatility": 0.22,
    "var": 35_000.0,
    "risk_score": 72.0,
}

positions = [
    {
        "symbol": "RELIANCE",
        "quantity": 100,
        "price": 2500.0,
        "weight": 0.25,
    },
    {
        "symbol": "HDFCBANK",
        "quantity": 100,
        "price": 2500.0,
        "weight": 0.25,
    },
]

scenarios = [
    {
        "scenario_id": "TEST_STRESS_01",
        "name": "Synthetic Market Stress",
        "shock": -0.10,
        "severity": "HIGH",
    }
]

out("Portfolio value : 1,000,000")
out("Cash            : 250,000")
out("Positions       : 2")
out("Scenarios       : 1")
out("Safety mode     : READ-ONLY / SYNTHETIC")


# ============================================================
# BLOCK 94
# ============================================================

section("4. BLOCK 94 -> STRESS SCENARIO ENGINE")

b94 = None

try:
    b94 = instances[94].certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    inspect_result("BLOCK 94 CERTIFY OUTPUT", b94)

except Exception as exc:
    out("BLOCK 94 ERROR")
    out(type(exc).__name__ + ": " + str(exc))


# ============================================================
# BLOCK 95
# ============================================================

section("5. BLOCK 95 -> STRESS EVIDENCE GATE")

b95 = None

if isinstance(b94, dict):

    try:
        b95 = instances[95].certify(
            stress_certificate=b94
        )

        inspect_result("BLOCK 95 CERTIFY OUTPUT", b95)

    except Exception as exc:
        out("BLOCK 95 ERROR")
        out(type(exc).__name__ + ": " + str(exc))

else:
    out("BLOCK 95 SKIPPED: Block 94 did not produce a dictionary")


# ============================================================
# BLOCK 96
# ============================================================

section("6. BLOCK 96 -> STRESS DECISION GATE")

b96 = None

if isinstance(b95, dict):

    try:
        b96 = instances[96].certify(
            stress_gate=b95
        )

        inspect_result("BLOCK 96 CERTIFY OUTPUT", b96)

    except Exception as exc:
        out("BLOCK 96 ERROR")
        out(type(exc).__name__ + ": " + str(exc))

else:
    out("BLOCK 96 SKIPPED")


# ============================================================
# BLOCK 97
# ============================================================

section("7. BLOCK 97 -> STRESS READINESS GATE")

b97 = None

if isinstance(b96, dict):

    try:
        b97 = instances[97].certify(
            decision=b96
        )

        inspect_result("BLOCK 97 CERTIFY OUTPUT", b97)

    except Exception as exc:
        out("BLOCK 97 ERROR")
        out(type(exc).__name__ + ": " + str(exc))

else:
    out("BLOCK 97 SKIPPED")


# ============================================================
# BLOCK 98
# ============================================================

section("8. BLOCK 98 -> EXECUTION GOVERNANCE BRIDGE")

b98 = None

if isinstance(b97, dict):

    try:
        b98 = instances[98].certify(
            decision=b97
        )

        inspect_result("BLOCK 98 CERTIFY OUTPUT", b98)

    except Exception as exc:
        out("BLOCK 98 ERROR")
        out(type(exc).__name__ + ": " + str(exc))

else:
    out("BLOCK 98 SKIPPED")


# ============================================================
# BLOCK 99
# ============================================================

section("9. BLOCK 99 -> EXECUTION INTENT AUTHORIZATION")

b99 = None

if isinstance(b98, dict):

    try:
        b99 = instances[99].certify(
            governance=b98
        )

        inspect_result("BLOCK 99 CERTIFY OUTPUT", b99)

    except Exception as exc:
        out("BLOCK 99 ERROR")
        out(type(exc).__name__ + ": " + str(exc))

else:
    out("BLOCK 99 SKIPPED")


# ============================================================
# BLOCK 100
# ============================================================

section("10. BLOCK 100 -> PAPER EXECUTION FILL GATE")

b100 = None

if isinstance(b99, dict):

    try:
        b100 = instances[100].certify(
            intent=b99,
            fill_ratio=1.0,
        )

        inspect_result("BLOCK 100 CERTIFY OUTPUT", b100)

    except Exception as exc:
        out("BLOCK 100 ERROR")
        out(type(exc).__name__ + ": " + str(exc))

else:
    out("BLOCK 100 SKIPPED")


# ============================================================
# BLOCK 101
# ============================================================

section("11. BLOCK 101 -> EXECUTION EVIDENCE RECONCILIATION")

b101 = None

if isinstance(b100, dict):

    try:
        b101 = instances[101].certify(
            execution=b100
        )

        inspect_result("BLOCK 101 CERTIFY OUTPUT", b101)

    except Exception as exc:
        out("BLOCK 101 ERROR")
        out(type(exc).__name__ + ": " + str(exc))

else:
    out("BLOCK 101 SKIPPED")


# ============================================================
# CROSS-BLOCK FIELD PROPAGATION
# ============================================================

section("12. CROSS-BLOCK SAFETY FIELD PROPAGATION")

results = {
    94: b94,
    95: b95,
    96: b96,
    97: b97,
    98: b98,
    99: b99,
    100: b100,
    101: b101,
}

fields = [
    "status",
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

    out()
    out(f"BLOCK {block_id}")

    if not isinstance(result, dict):
        out("  RESULT: <NOT AVAILABLE>")
        continue

    for field in fields:
        if field in result:
            out(f"  {field:28} = {result[field]!r}")
        else:
            out(f"  {field:28} = <ABSENT>")


# ============================================================
# SAFETY VERDICT
# ============================================================

section("13. SAFETY CONTRACT VERDICT")

required = [
    "execution_blocked",
    "non_mutation_invariant",
    "broker_submission",
    "live_order_submission",
]

for block_id, result in results.items():

    out()
    out(f"BLOCK {block_id}")

    if not isinstance(result, dict):
        out("  VERDICT: NO RESULT")
        continue

    missing = []

    for field in required:
        if field not in result:
            missing.append(field)

    if missing:
        out("  CONTRACT STATUS : INCOMPLETE")
        out("  MISSING FIELDS  : " + ", ".join(missing))
    else:
        safe = (
            result.get("execution_blocked") is True
            and result.get("non_mutation_invariant") is True
            and result.get("broker_submission") is False
            and result.get("live_order_submission") is False
        )

        out(
            "  CONTRACT STATUS : "
            + ("SAFE" if safe else "UNSAFE")
        )


# ============================================================
# FINAL SUMMARY
# ============================================================

section("14. FINAL TRACE SUMMARY")

out("BLOCK 94  : " + ("OUTPUT CREATED" if isinstance(b94, dict) else "FAILED"))
out("BLOCK 95  : " + ("OUTPUT CREATED" if isinstance(b95, dict) else "FAILED"))
out("BLOCK 96  : " + ("OUTPUT CREATED" if isinstance(b96, dict) else "FAILED"))
out("BLOCK 97  : " + ("OUTPUT CREATED" if isinstance(b97, dict) else "FAILED"))
out("BLOCK 98  : " + ("OUTPUT CREATED" if isinstance(b98, dict) else "FAILED"))
out("BLOCK 99  : " + ("OUTPUT CREATED" if isinstance(b99, dict) else "FAILED"))
out("BLOCK 100 : " + ("OUTPUT CREATED" if isinstance(b100, dict) else "FAILED"))
out("BLOCK 101 : " + ("OUTPUT CREATED" if isinstance(b101, dict) else "FAILED"))

out()
out("IMPORTANT")
out("This was a SYNTHETIC / READ-ONLY contract trace.")
out("No broker was contacted.")
out("No live order was created.")
out("No portfolio was mutated.")
out("No source files were modified.")
out()
out("=" * 76)
out("END OF EROS 3.0 CONTRACT TRACE")
out("=" * 76)

# ============================================================
# COPY COMPLETE OUTPUT TO WINDOWS CLIPBOARD
# ============================================================

try:
    import subprocess

    final_text = "\n".join(lines)

    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Set-Clipboard -Value ([Console]::In.ReadToEnd())"],
        input=final_text,
        text=True,
        check=True,
    )

    print()
    print("=" * 76)
    print("COPIED TO WINDOWS CLIPBOARD : YES")
    print("=" * 76)

except Exception as exc:
    print()
    print("=" * 76)
    print("CLIPBOARD COPY : FAILED")
    print(type(exc).__name__, str(exc))
    print("=" * 76)
