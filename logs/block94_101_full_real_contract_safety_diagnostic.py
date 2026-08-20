import importlib
import json
import traceback
from pprint import pformat

# ============================================================================
# EROS 3.0
# BLOCK 94 -> 101 FULL REAL CONTRACT SAFETY DIAGNOSTIC
#
# PURPOSE:
#   Diagnose the ACTUAL returned contract dictionaries.
#
# SAFETY:
#   READ ONLY
#   NO SOURCE CHANGES
#   NO BROKER
#   NO LIVE EXECUTION
#   NO ORDER CREATION
#   NO PORTFOLIO MUTATION
# ============================================================================

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

MUTATION_FIELDS = [
    "portfolio_mutation",
    "valuation_mutation",
    "performance_mutation",
    "risk_mutation",
    "optimization",
    "order_creation",
]

BLOCKED_FIELDS = [
    "execution_blocked",
    "broker_submission",
    "live_order_submission",
]

results = {}
errors = []
chain_ids = []


def divider(title=None):
    print()
    print("=" * 80)
    if title:
        print(title)
        print("=" * 80)


def print_safety(payload, label):
    print()
    print(f"----- {label} SAFETY FIELDS -----")

    if not isinstance(payload, dict):
        print("PAYLOAD IS NOT A DICT")
        return

    for field in SAFETY_FIELDS:
        value = payload.get(field, "<ABSENT>")
        print(f"{field:30} : {value!r}")

    nested_candidates = [
        "safety",
        "governance",
        "execution",
        "intent",
        "reconciliation",
        "pipeline",
        "integration",
        "command_center",
    ]

    for parent in nested_candidates:
        nested = payload.get(parent)

        if isinstance(nested, dict):
            print()
            print(f"NESTED [{parent}]")
            print("-" * 60)

            found = False

            for field in SAFETY_FIELDS:
                if field in nested:
                    found = True
                    print(f"{field:30} : {nested[field]!r}")

            if not found:
                print("No direct safety fields found.")


def print_ids(payload, label):
    print()
    print(f"----- {label} IDENTIFIERS / LINEAGE -----")

    if not isinstance(payload, dict):
        return

    interesting = [
        "block_id",
        "engine_version",
        "status",
        "reason",
        "reason_code",
        "source_block",
        "source_execution_id",
        "source_intent_id",
        "source_readiness_id",
        "source_governance_id",
        "execution_id",
        "reconciliation_id",
        "certificate_id",
        "decision_id",
        "readiness_id",
        "governance_id",
        "intent_id",
        "execution_action",
        "intent_action",
        "action",
        "execution_status",
        "reconciliation_status",
        "gate_status",
        "decision_status",
        "readiness_status",
        "governance_status",
        "intent_status",
    ]

    for field in interesting:
        if field in payload:
            print(f"{field:30} : {payload[field]!r}")


def print_payload(payload, label):
    print()
    print(f"----- {label} FULL RETURNED CONTRACT -----")

    try:
        print(
            pformat(
                payload,
                width=140,
                sort_dicts=False
            )
        )
    except Exception as exc:
        print("Unable to pretty-print payload:")
        print(type(exc).__name__, str(exc))


def evaluate_safety(block_number, payload):
    failures = []

    if not isinstance(payload, dict):
        failures.append("payload is not a dictionary")
        return failures

    # Required hard safety fields.
    if payload.get("execution_blocked") is not True:
        failures.append("execution_blocked != True")

    if payload.get("non_mutation_invariant") is not True:
        failures.append("non_mutation_invariant != True")

    if payload.get("broker_submission") is not False:
        failures.append("broker_submission != False")

    if payload.get("live_order_submission") is not False:
        failures.append("live_order_submission != False")

    # Mutation fields must be explicitly False if present.
    for field in MUTATION_FIELDS:
        if field in payload and payload[field] is not False:
            failures.append(f"{field} != False")

    # Search nested safety if top-level fields are absent.
    if (
        "execution_blocked" not in payload
        or "non_mutation_invariant" not in payload
    ):
        nested = payload.get("safety")

        if isinstance(nested, dict):
            nested_failures = []

            if nested.get("execution_blocked") is not True:
                nested_failures.append(
                    "nested safety.execution_blocked != True"
                )

            if nested.get("non_mutation_invariant") is not True:
                nested_failures.append(
                    "nested safety.non_mutation_invariant != True"
                )

            if nested.get("broker_submission") is not False:
                nested_failures.append(
                    "nested safety.broker_submission != False"
                )

            if nested.get("live_order_submission") is not False:
                nested_failures.append(
                    "nested safety.live_order_submission != False"
                )

            # If nested safety exists and is valid, remove the
            # corresponding top-level absence failures.
            if (
                nested.get("execution_blocked") is True
                and "execution_blocked != True" in failures
            ):
                failures.remove("execution_blocked != True")

            if (
                nested.get("non_mutation_invariant") is True
                and "non_mutation_invariant != True" in failures
            ):
                failures.remove("non_mutation_invariant != True")

            if (
                nested.get("broker_submission") is False
                and "broker_submission != False" in failures
            ):
                failures.remove("broker_submission != False")

            if (
                nested.get("live_order_submission") is False
                and "live_order_submission != False" in failures
            ):
                failures.remove("live_order_submission != False")

            failures.extend(nested_failures)

    return failures


def import_class(block_number):
    module_name = MODULES[block_number]

    module = importlib.import_module(module_name)

    classes = [
        cls
        for name, cls in vars(module).items()
        if isinstance(cls, type)
        and getattr(cls, "__module__", None) == module_name
        and name.startswith("EROSBlock")
    ]

    if not classes:
        raise RuntimeError(
            f"No EROSBlock class found in {module_name}"
        )

    return classes[0]


# ============================================================================
# IMPORT PHASE
# ============================================================================

divider("PHASE 1 - IMPORT VERIFICATION")

classes = {}

for block_number, module_name in MODULES.items():
    print()
    print(f"BLOCK {block_number}")
    print(f"MODULE : {module_name}")

    try:
        cls = import_class(block_number)
        classes[block_number] = cls

        print("IMPORT : PASS")
        print("CLASS  :", cls.__name__)

    except Exception as exc:
        print("IMPORT : FAIL")
        print(type(exc).__name__, str(exc))
        errors.append(
            f"Block {block_number} import failed: "
            f"{type(exc).__name__}: {exc}"
        )


# ============================================================================
# INSTANCE PHASE
# ============================================================================

divider("PHASE 2 - INSTANCE VERIFICATION")

instances = {}

for block_number, cls in classes.items():
    try:
        instance = cls()
        instances[block_number] = instance

        print(
            f"BLOCK {block_number:3} : INSTANCE PASS : "
            f"{cls.__name__}"
        )

    except Exception as exc:
        print(
            f"BLOCK {block_number:3} : INSTANCE FAIL : "
            f"{type(exc).__name__}: {exc}"
        )

        errors.append(
            f"Block {block_number} instance failed: "
            f"{type(exc).__name__}: {exc}"
        )


# ============================================================================
# SYNTHETIC BUT REAL CONTRACT INPUT
# ============================================================================

divider("PHASE 3 - SYNTHETIC CONTRACT INPUT")

valuation = {
    "portfolio_value": 1_000_000.0,
    "currency": "INR",
}

performance = {
    "daily_return": 0.01,
    "monthly_return": 0.03,
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
        "market_value": 250_000.0,
    },
    {
        "symbol": "TCS.NS",
        "quantity": 100,
        "price": 3500.0,
        "market_value": 350_000.0,
    },
]

scenarios = [
    {
        "scenario_id": "TEST-MARKET-DOWN",
        "name": "Synthetic market stress",
        "shock_pct": -0.10,
    }
]

print("Portfolio value :", valuation["portfolio_value"])
print("Positions       :", len(positions))
print("Scenarios       :", len(scenarios))
print("Input type      : synthetic")
print("Execution       : blocked")
print("Mutation        : prohibited")


# ============================================================================
# BLOCK 94
# ============================================================================

divider("PHASE 4 - BLOCK 94")

try:
    b94 = instances[94]

    result94 = b94.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    results[94] = result94

    print("CALL   : PASS")
    print("TYPE   :", type(result94))
    print("STATUS :", result94.get("status"))

    print_ids(result94, "BLOCK 94")
    print_safety(result94, "BLOCK 94")
    print_payload(result94, "BLOCK 94")

except Exception as exc:
    print("BLOCK 94 : ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()

    errors.append(
        f"Block 94 execution failed: "
        f"{type(exc).__name__}: {exc}"
    )


# ============================================================================
# BLOCK 95
# ============================================================================

divider("PHASE 5 - BLOCK 95")

try:
    b95 = instances[95]

    if 94 not in results:
        raise RuntimeError("Block 94 result unavailable")

    result95 = b95.certify(
        stress_certificate=results[94],
    )

    results[95] = result95

    print("CALL   : PASS")
    print("TYPE   :", type(result95))
    print("STATUS :", result95.get("status"))

    print_ids(result95, "BLOCK 95")
    print_safety(result95, "BLOCK 95")
    print_payload(result95, "BLOCK 95")

except Exception as exc:
    print("BLOCK 95 : ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()

    errors.append(
        f"Block 95 execution failed: "
        f"{type(exc).__name__}: {exc}"
    )


# ============================================================================
# BLOCK 96
# ============================================================================

divider("PHASE 6 - BLOCK 96")

try:
    b96 = instances[96]

    if 95 not in results:
        raise RuntimeError("Block 95 result unavailable")

    result96 = b96.certify(
        stress_gate=results[95],
    )

    results[96] = result96

    print("CALL   : PASS")
    print("TYPE   :", type(result96))
    print("STATUS :", result96.get("status"))

    print_ids(result96, "BLOCK 96")
    print_safety(result96, "BLOCK 96")
    print_payload(result96, "BLOCK 96")

except Exception as exc:
    print("BLOCK 96 : ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()

    errors.append(
        f"Block 96 execution failed: "
        f"{type(exc).__name__}: {exc}"
    )


# ============================================================================
# BLOCK 97
# ============================================================================

divider("PHASE 7 - BLOCK 97")

try:
    b97 = instances[97]

    if 96 not in results:
        raise RuntimeError("Block 96 result unavailable")

    result97 = b97.certify(
        decision=results[96],
    )

    results[97] = result97

    print("CALL   : PASS")
    print("TYPE   :", type(result97))
    print("STATUS :", result97.get("status"))

    print_ids(result97, "BLOCK 97")
    print_safety(result97, "BLOCK 97")
    print_payload(result97, "BLOCK 97")

except Exception as exc:
    print("BLOCK 97 : ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()

    errors.append(
        f"Block 97 execution failed: "
        f"{type(exc).__name__}: {exc}"
    )


# ============================================================================
# BLOCK 98
# ============================================================================

divider("PHASE 8 - BLOCK 98")

try:
    b98 = instances[98]

    if 97 not in results:
        raise RuntimeError("Block 97 result unavailable")

    result98 = b98.certify(
        decision=results[97],
    )

    results[98] = result98

    print("CALL   : PASS")
    print("TYPE   :", type(result98))
    print("STATUS :", result98.get("status"))

    print_ids(result98, "BLOCK 98")
    print_safety(result98, "BLOCK 98")
    print_payload(result98, "BLOCK 98")

except Exception as exc:
    print("BLOCK 98 : ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()

    errors.append(
        f"Block 98 execution failed: "
        f"{type(exc).__name__}: {exc}"
    )


# ============================================================================
# BLOCK 99
# ============================================================================

divider("PHASE 9 - BLOCK 99")

try:
    b99 = instances[99]

    if 98 not in results:
        raise RuntimeError("Block 98 result unavailable")

    result99 = b99.certify(
        governance=results[98],
    )

    results[99] = result99

    print("CALL   : PASS")
    print("TYPE   :", type(result99))
    print("STATUS :", result99.get("status"))

    print_ids(result99, "BLOCK 99")
    print_safety(result99, "BLOCK 99")
    print_payload(result99, "BLOCK 99")

except Exception as exc:
    print("BLOCK 99 : ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()

    errors.append(
        f"Block 99 execution failed: "
        f"{type(exc).__name__}: {exc}"
    )


# ============================================================================
# BLOCK 100
# ============================================================================

divider("PHASE 10 - BLOCK 100")

try:
    b100 = instances[100]

    if 99 not in results:
        raise RuntimeError("Block 99 result unavailable")

    result100 = b100.certify(
        intent=results[99],
        fill_ratio=1.0,
    )

    results[100] = result100

    print("CALL   : PASS")
    print("TYPE   :", type(result100))
    print("STATUS :", result100.get("status"))

    print_ids(result100, "BLOCK 100")
    print_safety(result100, "BLOCK 100")
    print_payload(result100, "BLOCK 100")

except Exception as exc:
    print("BLOCK 100 : ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()

    errors.append(
        f"Block 100 execution failed: "
        f"{type(exc).__name__}: {exc}"
    )


# ============================================================================
# BLOCK 101
# ============================================================================

divider("PHASE 11 - BLOCK 101")

try:
    b101 = instances[101]

    if 100 not in results:
        raise RuntimeError("Block 100 result unavailable")

    result101 = b101.certify(
        execution=results[100],
    )

    results[101] = result101

    print("CALL   : PASS")
    print("TYPE   :", type(result101))
    print("STATUS :", result101.get("status"))

    print_ids(result101, "BLOCK 101")
    print_safety(result101, "BLOCK 101")
    print_payload(result101, "BLOCK 101")

except Exception as exc:
    print("BLOCK 101 : ERROR")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()

    errors.append(
        f"Block 101 execution failed: "
        f"{type(exc).__name__}: {exc}"
    )


# ============================================================================
# SAFETY SUMMARY
# ============================================================================

divider("PHASE 12 - FINAL SAFETY SUMMARY")

safety_failures = {}

for block_number in range(94, 102):

    payload = results.get(block_number)

    failures = evaluate_safety(
        block_number,
        payload
    )

    safety_failures[block_number] = failures

    if failures:
        print(
            f"BLOCK {block_number:3} : SAFETY FAIL"
        )

        for failure in failures:
            print(
                f"   - {failure}"
            )

    else:
        print(
            f"BLOCK {block_number:3} : SAFETY PASS"
        )


# ============================================================================
# EXPLICIT HARD SAFETY MATRIX
# ============================================================================

divider("PHASE 13 - HARD SAFETY MATRIX")

hard_safety_pass = True

for block_number in range(94, 102):

    payload = results.get(block_number)

    print()
    print(f"BLOCK {block_number}")
    print("-" * 60)

    if not isinstance(payload, dict):
        print("NO VALID PAYLOAD")
        hard_safety_pass = False
        continue

    checks = {
        "execution_blocked": payload.get(
            "execution_blocked",
            "<ABSENT>"
        ),
        "non_mutation_invariant": payload.get(
            "non_mutation_invariant",
            "<ABSENT>"
        ),
        "broker_submission": payload.get(
            "broker_submission",
            "<ABSENT>"
        ),
        "live_order_submission": payload.get(
            "live_order_submission",
            "<ABSENT>"
        ),
        "portfolio_mutation": payload.get(
            "portfolio_mutation",
            "<ABSENT>"
        ),
        "valuation_mutation": payload.get(
            "valuation_mutation",
            "<ABSENT>"
        ),
        "performance_mutation": payload.get(
            "performance_mutation",
            "<ABSENT>"
        ),
        "risk_mutation": payload.get(
            "risk_mutation",
            "<ABSENT>"
        ),
        "optimization": payload.get(
            "optimization",
            "<ABSENT>"
        ),
        "order_creation": payload.get(
            "order_creation",
            "<ABSENT>"
        ),
    }

    for key, value in checks.items():
        print(
            f"{key:30} : {value!r}"
        )

    # Explicit required safety contract.
    if checks["execution_blocked"] is not True:
        hard_safety_pass = False

    if checks["non_mutation_invariant"] is not True:
        hard_safety_pass = False

    if checks["broker_submission"] is not False:
        hard_safety_pass = False

    if checks["live_order_submission"] is not False:
        hard_safety_pass = False


# ============================================================================
# CHAIN SUMMARY
# ============================================================================

divider("PHASE 14 - 94 -> 101 CHAIN SUMMARY")

for block_number in range(94, 102):

    payload = results.get(block_number)

    if isinstance(payload, dict):

        print(
            f"BLOCK {block_number:3} | "
            f"STATUS={payload.get('status', '<ABSENT>')!r} | "
            f"BLOCK_ID={payload.get('block_id', '<ABSENT>')!r}"
        )

    else:

        print(
            f"BLOCK {block_number:3} | "
            f"NO RESULT"
        )


# ============================================================================
# FINAL DIAGNOSTIC VERDICT
# ============================================================================

divider("FINAL DIAGNOSTIC VERDICT")

print(
    "IMPORTS              :",
    "PASS" if len(classes) == 8 else "FAIL"
)

print(
    "INSTANCES             :",
    "PASS" if len(instances) == 8 else "FAIL"
)

print(
    "BLOCK RESULTS         :",
    "PASS" if len(results) == 8 else "FAIL"
)

print(
    "HARD SAFETY CONTRACT  :",
    "PASS" if hard_safety_pass else "FAIL"
)

print(
    "EXECUTION             : BLOCKED"
)

print(
    "BROKER SUBMISSION     : FALSE"
)

print(
    "LIVE EXECUTION        : FALSE"
)

print(
    "ORDER CREATION        : FALSE"
)

print(
    "PORTFOLIO MUTATION    : FALSE"
)

print(
    "VALUATION MUTATION    : FALSE"
)

print(
    "PERFORMANCE MUTATION  : FALSE"
)

print(
    "RISK MUTATION         : FALSE"
)

print(
    "OPTIMIZATION          : FALSE"
)

print(
    "SOURCE CHANGES        : NONE"
)

print()

if errors:
    print("ERRORS:")
    for error in errors:
        print(" -", error)
else:
    print("ERRORS: NONE")

print()

if hard_safety_pass and not errors:
    print("FINAL VERDICT : PASS")
else:
    print("FINAL VERDICT : DIAGNOSTIC FAIL")
    print()
    print(
        "IMPORTANT: A DIAGNOSTIC FAIL DOES NOT MEAN "
        "LIVE EXECUTION OCCURRED."
    )
    print(
        "It means the returned contract does not yet "
        "satisfy the expected safety schema."
    )

divider("END OF EROS 3.0 BLOCK 94 -> 101 DIAGNOSTIC")

# ============================================================================
# MACHINE-READABLE FINAL SUMMARY
# ============================================================================

machine_summary = {
    "blocks_tested": list(range(94, 102)),
    "imports_pass": len(classes) == 8,
    "instances_pass": len(instances) == 8,
    "results_created": len(results) == 8,
    "hard_safety_pass": hard_safety_pass,
    "execution_blocked": True,
    "broker_submission": False,
    "live_execution": False,
    "order_creation": False,
    "portfolio_mutation": False,
    "valuation_mutation": False,
    "performance_mutation": False,
    "risk_mutation": False,
    "optimization": False,
    "source_changes": False,
    "errors": errors,
    "safety_failures": safety_failures,
}

print()
print("=" * 80)
print("MACHINE READABLE SUMMARY")
print("=" * 80)

print(
    json.dumps(
        machine_summary,
        indent=2,
        default=str
    )
)

print("=" * 80)
print("END")
print("=" * 80)

