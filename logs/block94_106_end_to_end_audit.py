import importlib
import pprint
import sys
import traceback

# ============================================================
# EROS 3.0 - BLOCK 94 -> 106 END-TO-END AUDIT
# READ ONLY / NO MUTATION / NO BROKER
# ============================================================

MODULES = [
    ("94", "services.quantitative.block94_portfolio_stress_scenario_engine"),
    ("95", "services.quantitative.block95_stress_evidence_gate"),
    ("96", "services.quantitative.block96_stress_decision_gate"),
    ("97", "services.quantitative.block97_stress_readiness_gate"),
    ("98", "services.quantitative.block98_execution_governance_bridge"),
    ("99", "services.quantitative.block99_execution_intent_authorization_gate"),
    ("100", "services.quantitative.block100_paper_execution_fill_gate"),
    ("101", "services.quantitative.block101_execution_evidence_reconciliation"),
    ("102", "services.quantitative.block102_frontend_contract"),
    ("103", "services.quantitative.block103_institutional_frontend_read_model"),
    ("104", "services.quantitative.block104_eros_command_center"),
    ("106", "services.quantitative.block106_institutional_integration_boundary"),
]

output = []

def emit(text=""):
    print(text)
    output.append(str(text))


def get_class(module, module_name):
    for name, obj in vars(module).items():
        if (
            isinstance(obj, type)
            and getattr(obj, "__module__", None) == module_name
            and name.startswith("EROSBlock")
        ):
            return obj
    return None


def inspect_safety(payload, label):
    emit()
    emit(f"----- SAFETY TRACE: {label} -----")

    if not isinstance(payload, dict):
        emit(f"PAYLOAD TYPE : {type(payload)}")
        emit("SAFETY TRACE : NOT A DICT")
        return

    safety = payload.get("safety")

    if isinstance(safety, dict):
        emit("SAFETY LOCATION : nested [safety]")
        source = safety
    else:
        emit("SAFETY LOCATION : top-level")
        source = payload

    fields = [
        "execution_blocked",
        "non_mutation_invariant",
        "broker_submission",
        "live_order_submission",
        "order_creation",
        "portfolio_mutation",
        "valuation_mutation",
        "performance_mutation",
        "risk_mutation",
        "optimization",
    ]

    for field in fields:
        if field in source:
            emit(f"{field:28} : {source[field]!r}")
        else:
            emit(f"{field:28} : <ABSENT>")

    if isinstance(safety, dict):
        emit("NESTED SAFETY KEYS:")
        for key in safety.keys():
            emit(f"  {key}")

def main():

    emit("=" * 80)
    emit("EROS 3.0 - BLOCK 94 -> 106 END-TO-END CONTRACT AUDIT")
    emit("=" * 80)
    emit(f"PYTHON : {sys.version.split()[0]}")
    emit(f"PATH   : {sys.path[0]}")
    emit()

    imported = {}
    instances = {}

    # ========================================================
    # 1. IMPORT AUDIT
    # ========================================================

    emit("=" * 80)
    emit("1. IMPORT AUDIT")
    emit("=" * 80)

    import_failures = []

    for block_id, module_name in MODULES:
        try:
            module = importlib.import_module(module_name)
            imported[block_id] = module
            emit(f"BLOCK {block_id:>3} IMPORT : PASS")
        except Exception as exc:
            import_failures.append(block_id)
            emit(f"BLOCK {block_id:>3} IMPORT : FAIL")
            emit(f"  {type(exc).__name__}: {exc}")

    # ========================================================
    # 2. INSTANCE AUDIT
    # ========================================================

    emit()
    emit("=" * 80)
    emit("2. CLASS / INSTANCE AUDIT")
    emit("=" * 80)

    instance_failures = []

    for block_id, module_name in MODULES:
        module = imported.get(block_id)

        if module is None:
            continue

        cls = get_class(module, module_name)

        if cls is None:
            instance_failures.append(block_id)
            emit(f"BLOCK {block_id:>3} CLASS : FAIL")
            continue

        try:
            instance = cls()
            instances[block_id] = instance
            emit(f"BLOCK {block_id:>3} CLASS : {cls.__name__}")
            emit(f"BLOCK {block_id:>3} INSTANCE : PASS")
        except Exception as exc:
            instance_failures.append(block_id)
            emit(f"BLOCK {block_id:>3} INSTANCE : FAIL")
            emit(f"  {type(exc).__name__}: {exc}")

    # ========================================================
    # 3. SNAPSHOT AUDIT
    # ========================================================

    emit()
    emit("=" * 80)
    emit("3. SNAPSHOT / READ-MODEL AUDIT")
    emit("=" * 80)

    snapshot_results = {}

    for block_id, instance in instances.items():

        if not hasattr(instance, "snapshot"):
            emit(f"BLOCK {block_id:>3} SNAPSHOT : NOT AVAILABLE")
            continue

        try:
            result = instance.snapshot()
            snapshot_results[block_id] = result

            emit(f"BLOCK {block_id:>3} SNAPSHOT : PASS")
            emit(f"  TYPE : {type(result)}")

            if isinstance(result, dict):
                emit(f"  KEYS : {list(result.keys())}")

            inspect_safety(result, f"BLOCK {block_id} SNAPSHOT")

        except Exception as exc:
            emit(f"BLOCK {block_id:>3} SNAPSHOT : FAIL")
            emit(f"  {type(exc).__name__}: {exc}")

    # ========================================================
    # 4. HISTORY AUDIT
    # ========================================================

    emit()
    emit("=" * 80)
    emit("4. HISTORY AUDIT")
    emit("=" * 80)

    for block_id, instance in instances.items():

        for method_name in [
            "certificate_history",
            "scenario_history",
        ]:

            if not hasattr(instance, method_name):
                continue

            try:
                result = getattr(instance, method_name)()

                emit(f"BLOCK {block_id:>3} {method_name} : PASS")
                emit(f"  TYPE : {type(result)}")
                emit(f"  VALUE: {result!r}")

            except Exception as exc:
                emit(f"BLOCK {block_id:>3} {method_name} : FAIL")
                emit(f"  {type(exc).__name__}: {exc}")

    # ========================================================
    # 5. SAFETY SCHEMA CONSISTENCY
    # ========================================================

    emit()
    emit("=" * 80)
    emit("5. SAFETY SCHEMA CONSISTENCY")
    emit("=" * 80)

    expected = {
        "execution_blocked": True,
        "non_mutation_invariant": True,
        "broker_submission": False,
        "live_order_submission": False,
        "order_creation": False,
        "portfolio_mutation": False,
        "valuation_mutation": False,
        "performance_mutation": False,
        "risk_mutation": False,
        "optimization": False,
    }

    safety_failures = []

    for block_id, payload in snapshot_results.items():

        if not isinstance(payload, dict):
            continue

        safety = payload.get("safety")

        if isinstance(safety, dict):
            source = safety
        else:
            source = payload

        emit()
        emit(f"BLOCK {block_id} SAFETY CONTRACT")

        for field, expected_value in expected.items():

            actual = source.get(field, "<ABSENT>")

            if actual == expected_value:
                emit(
                    f"  {field:28} : PASS "
                    f"(actual={actual!r})"
                )
            else:
                emit(
                    f"  {field:28} : FAIL "
                    f"(actual={actual!r}, expected={expected_value!r})"
                )

                safety_failures.append(
                    (block_id, field, actual, expected_value)
                )

    # ========================================================
    # 6. FINAL RESULT
    # ========================================================

    emit()
    emit("=" * 80)
    emit("6. FINAL AUDIT RESULT")
    emit("=" * 80)

    emit(
        f"IMPORT FAILURES       : "
        f"{len(import_failures)}"
    )

    emit(
        f"INSTANCE FAILURES     : "
        f"{len(instance_failures)}"
    )

    emit(
        f"SAFETY FAILURES       : "
        f"{len(safety_failures)}"
    )

    if (
        len(import_failures) == 0
        and len(instance_failures) == 0
        and len(safety_failures) == 0
    ):
        emit()
        emit("============================================================")
        emit("EROS 3.0 BLOCK 94 -> 106 AUDIT : PASS")
        emit("============================================================")
        emit("READ ONLY              : TRUE")
        emit("ORDER CREATION         : FALSE")
        emit("BROKER SUBMISSION      : FALSE")
        emit("LIVE EXECUTION         : FALSE")
        emit("PORTFOLIO MUTATION     : FALSE")
        emit("VALUATION MUTATION     : FALSE")
        emit("PERFORMANCE MUTATION   : FALSE")
        emit("RISK MUTATION          : FALSE")
        emit("OPTIMIZATION           : FALSE")
        emit("EXECUTION BLOCKED      : TRUE")
        emit("NON-MUTATION INVARIANT : TRUE")
        emit("============================================================")
        final_status = "PASS"

    else:
        emit()
        emit("============================================================")
        emit("EROS 3.0 BLOCK 94 -> 106 AUDIT : REVIEW REQUIRED")
        emit("============================================================")

        if import_failures:
            emit(f"IMPORT FAILURES : {import_failures}")

        if instance_failures:
            emit(f"INSTANCE FAILURES : {instance_failures}")

        if safety_failures:
            emit("SAFETY FAILURES:")
            for failure in safety_failures:
                emit(
                    f"  BLOCK {failure[0]} | "
                    f"{failure[1]} | "
                    f"actual={failure[2]!r} | "
                    f"expected={failure[3]!r}"
                )

        final_status = "REVIEW_REQUIRED"

    emit()
    emit("=" * 80)
    emit("AUDIT COMPLETE")
    emit("=" * 80)

    return final_status


try:
    status = main()
except Exception as exc:
    emit()
    emit("=" * 80)
    emit("AUDIT SCRIPT ERROR")
    emit("=" * 80)
    emit(type(exc).__name__)
    emit(str(exc))
    traceback.print_exc()
    status = "SCRIPT_ERROR"

# ============================================================
# COPY COMPLETE OUTPUT TO CLIPBOARD
# ============================================================

text = "\n".join(output)

try:
    import subprocess

    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Set-Clipboard -Value ([Console]::In.ReadToEnd())",
        ],
        input=text,
        text=True,
        check=True,
    )

    print()
    print("=" * 80)
    print("COMPLETE AUDIT OUTPUT COPIED TO CLIPBOARD")
    print("=" * 80)
    print("NOW COME BACK TO CHATGPT AND PRESS CTRL+V")
    print("=" * 80)

except Exception as exc:
    print()
    print("CLIPBOARD COPY FAILED")
    print(type(exc).__name__, str(exc))
    print("You can still copy the output manually.")

sys.exit(0)
