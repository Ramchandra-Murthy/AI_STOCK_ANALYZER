"""
EROS 3.0
Blocks 106-109 Golden Chain Runtime Gate

Purpose:
    Prove the actual runtime contracts and lineage of:

        Block 104
            ↓
        Block 106
            ↓
        Block 107
            ↓
        Block 108
            ↓
        Block 109

This diagnostic is READ-ONLY.

It does not:
    - create orders
    - submit to brokers
    - execute trades
    - mutate portfolio state
    - mutate valuation
    - mutate performance
    - mutate risk
"""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import traceback


PASS = 0
FAIL = 0
WARN = 0


def section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL

    if condition:
        PASS += 1
        print(f"[PASS] {name}")
    else:
        FAIL += 1
        print(f"[FAIL] {name}")

    if detail:
        print(f"       {detail}")


def warn(name: str, detail: str = "") -> None:
    global WARN

    WARN += 1
    print(f"[WARN] {name}")

    if detail:
        print(f"       {detail}")


def safe_repr(value) -> str:
    try:
        return repr(value)
    except Exception:
        return f"<repr failed: {type(value).__name__}>"


def public_api(obj) -> None:
    print(f"OBJECT : {type(obj).__name__}")

    for name in dir(obj):
        if name.startswith("_"):
            continue

        try:
            value = getattr(obj, name)
        except Exception:
            continue

        if callable(value):
            try:
                print(
                    f"  {name}{inspect.signature(value)}"
                )
            except Exception:
                print(f"  {name}")


# ======================================================================
# IMPORTS
# ======================================================================

section("IMPORT 106-109")

try:
    import services.quantitative.block106_institutional_integration_boundary as b106
    print("[PASS] BLOCK 106 IMPORT")
except Exception:
    print("[FAIL] BLOCK 106 IMPORT")
    traceback.print_exc()
    raise SystemExit(1)

try:
    import services.quantitative.block107_application_read_boundary as b107
    print("[PASS] BLOCK 107 IMPORT")
except Exception:
    print("[FAIL] BLOCK 107 IMPORT")
    traceback.print_exc()
    raise SystemExit(1)

try:
    import services.quantitative.block108_institutional_application_service_boundary as b108
    print("[PASS] BLOCK 108 IMPORT")
except Exception:
    print("[FAIL] BLOCK 108 IMPORT")
    traceback.print_exc()
    raise SystemExit(1)

try:
    import services.quantitative.block109_institutional_application_query_gateway as b109
    print("[PASS] BLOCK 109 IMPORT")
except Exception:
    print("[FAIL] BLOCK 109 IMPORT")
    traceback.print_exc()
    raise SystemExit(1)


# ======================================================================
# MODULE / CLASS DISCOVERY
# ======================================================================

section("PUBLIC CLASS / FUNCTION DISCOVERY")

for number, module in [
    ("106", b106),
    ("107", b107),
    ("108", b108),
    ("109", b109),
]:
    print()
    print(f"--- BLOCK {number} ---")

    for name, obj in vars(module).items():

        if name.startswith("_"):
            continue

        if inspect.isclass(obj):
            print(f"CLASS : {name}")

            for method_name in dir(obj):

                if method_name.startswith("_"):
                    continue

                try:
                    method = getattr(obj, method_name)
                except Exception:
                    continue

                if callable(method):
                    try:
                        print(
                            f"  METHOD : {method_name}"
                            f"{inspect.signature(method)}"
                        )
                    except Exception:
                        print(
                            f"  METHOD : {method_name}"
                        )

        elif inspect.isfunction(obj):
            try:
                print(
                    f"FUNCTION : {name}"
                    f"{inspect.signature(obj)}"
                )
            except Exception:
                print(f"FUNCTION : {name}")


# ======================================================================
# IDENTIFY IMPLEMENTATION CLASSES
# ======================================================================

section("CLASS IDENTIFICATION")

classes = {}

for number, module in [
    ("106", b106),
    ("107", b107),
    ("108", b108),
    ("109", b109),
]:

    candidates = []

    for name, obj in vars(module).items():
        if name.startswith("_"):
            continue

        if inspect.isclass(obj):
            if obj.__module__ == module.__name__:
                candidates.append((name, obj))

    print(f"BLOCK {number} CANDIDATES")

    for name, obj in candidates:
        print(f"  {name}")

    if len(candidates) == 1:
        classes[number] = candidates[0][1]
        print(
            f"[PASS] BLOCK {number} IMPLEMENTATION CLASS "
            f"IDENTIFIED: {candidates[0][0]}"
        )
    elif len(candidates) > 1:
        warn(
            f"BLOCK {number} HAS MULTIPLE LOCAL CLASSES",
            "Runtime method selection will be discovered below."
        )
    else:
        warn(
            f"BLOCK {number} HAS NO LOCAL IMPLEMENTATION CLASS",
            "Module-level functions may be the contract."
        )


# ======================================================================
# INSTANTIATION
# ======================================================================

section("INSTANTIATION")

objects = {}

for number in ["106", "107", "108", "109"]:

    cls = classes.get(number)

    if cls is None:
        warn(
            f"BLOCK {number} INSTANCE NOT CREATED",
            "No unique implementation class was identified."
        )
        continue

    try:
        obj = cls()
        objects[number] = obj

        check(
            f"BLOCK {number} INSTANTIATION",
            True,
            type(obj).__name__,
        )

        public_api(obj)

    except Exception as exc:
        check(
            f"BLOCK {number} INSTANTIATION",
            False,
            repr(exc),
        )


# ======================================================================
# SAFETY CONTRACTS
# ======================================================================

section("SAFETY CONTRACT INSPECTION")

for number, obj in objects.items():

    print()
    print(f"--- BLOCK {number} ---")

    safety = None

    for method_name in [
        "_build_safety_contract",
        "build_safety_contract",
        "safety_contract",
        "get_safety_contract",
    ]:

        if hasattr(obj, method_name):

            try:
                candidate = getattr(obj, method_name)

                if callable(candidate):
                    safety = candidate()
                else:
                    safety = candidate

                print(
                    f"SAFETY_SOURCE : {method_name}"
                )
                print(
                    f"SAFETY_VALUE  : {safe_repr(safety)}"
                )
                break

            except Exception as exc:
                print(
                    f"SAFETY_ERROR : {method_name} "
                    f"{repr(exc)}"
                )

    if safety is None:
        warn(
            f"BLOCK {number} SAFETY CONTRACT NOT DIRECTLY EXPOSED"
        )
        continue

    if isinstance(safety, dict):

        for key in [
            "read_only",
            "allow_order_creation",
            "allow_broker_submission",
            "allow_live_execution",
            "allow_portfolio_mutation",
            "allow_valuation_mutation",
            "allow_performance_mutation",
            "allow_risk_mutation",
            "execution_blocked",
            "non_mutation_invariant",
        ]:

            if key in safety:
                value = safety[key]

                if key in [
                    "read_only",
                    "execution_blocked",
                    "non_mutation_invariant",
                ]:
                    check(
                        f"BLOCK {number} SAFETY {key}=True",
                        value is True,
                        safe_repr(value),
                    )

                elif key.startswith("allow_"):
                    check(
                        f"BLOCK {number} SAFETY {key}=False",
                        value is False,
                        safe_repr(value),
                    )


# ======================================================================
# SNAPSHOT DISCOVERY
# ======================================================================

section("SNAPSHOT DISCOVERY")

snapshots = {}

for number, obj in objects.items():

    print()
    print(f"--- BLOCK {number} ---")

    found = False

    for method_name in [
        "snapshot",
        "get_snapshot",
        "build_snapshot",
        "current_snapshot",
        "state",
    ]:

        if not hasattr(obj, method_name):
            continue

        try:
            method = getattr(obj, method_name)

            if callable(method):
                signature = inspect.signature(method)

                if len(signature.parameters) == 0:
                    value = method()
                else:
                    continue
            else:
                value = method

            snapshots[number] = copy.deepcopy(value)

            print(
                f"[PASS] SNAPSHOT SOURCE : {method_name}"
            )
            print(
                f"TYPE : {type(value).__name__}"
            )
            print(
                f"VALUE : {safe_repr(value)}"
            )

            found = True
            break

        except Exception as exc:
            print(
                f"[WARN] SNAPSHOT {method_name} FAILED : "
                f"{repr(exc)}"
            )

    if not found:
        warn(
            f"BLOCK {number} SNAPSHOT NOT DIRECTLY AVAILABLE"
        )


# ======================================================================
# BLOCK 109 SAFETY CONTRACT
# ======================================================================

section("BLOCK 109 READ-ONLY GOVERNANCE")

gateway = objects.get("109")

if gateway is not None:

    safety = None

    for name in [
        "_build_safety_contract",
        "build_safety_contract",
        "safety_contract",
    ]:

        if hasattr(gateway, name):

            try:
                value = getattr(gateway, name)

                safety = value() if callable(value) else value

                break

            except Exception:
                pass

    print(
        "BLOCK109_SAFETY =",
        safe_repr(safety),
    )

    if isinstance(safety, dict):

        required_false = [
            "allow_order_creation",
            "allow_broker_submission",
            "allow_live_execution",
            "allow_portfolio_mutation",
            "allow_valuation_mutation",
            "allow_performance_mutation",
            "allow_risk_mutation",
        ]

        for key in required_false:
            if key in safety:
                check(
                    f"BLOCK109 {key}=False",
                    safety[key] is False,
                    safe_repr(safety[key]),
                )

        for key in [
            "read_only",
            "execution_blocked",
            "non_mutation_invariant",
        ]:
            if key in safety:
                check(
                    f"BLOCK109 {key}=True",
                    safety[key] is True,
                    safe_repr(safety[key]),
                )

else:
    warn("BLOCK109 OBJECT UNAVAILABLE")


# ======================================================================
# RUNTIME GOLDEN-CHAIN LINEAGE CHECK
# ======================================================================

section("RUNTIME GOLDEN CHAIN LINEAGE")

try:

    import services.quantitative.block103_institutional_frontend_read_model as b103
    import services.quantitative.block104_eros_command_center as b104

    # --------------------------------------------------------------
    # Build the same certified upstream contract used by the
    # existing EROS 103 -> 104 -> 106 -> 107 -> 108 -> 109 test.
    # --------------------------------------------------------------

    pipeline_status = []

    for block_id in range(94, 102):
        pipeline_status.append(
            {
                "block_id": str(block_id),
                "name": f"EROS Block {block_id}",
                "status": "BLOCKED",
                "identifier": f"EROS-BLOCK-{block_id}",
                "source_block": (
                    str(block_id - 1)
                    if block_id > 94
                    else None
                ),
                "execution_blocked": True,
            }
        )

    source_102 = {
        "status": "CERTIFIED",
        "block_id": "102",
        "pipeline_status": pipeline_status,
        "safety": {
            "portfolio_mutation": False,
            "valuation_mutation": False,
            "performance_mutation": False,
            "risk_mutation": False,
            "optimization": False,
            "order_creation": False,
            "broker_submission": False,
            "live_order_submission": False,
            "execution_blocked": True,
            "non_mutation_invariant": True,
        },
    }

    read_model_103 = (
        b103.EROSBlock103InstitutionalFrontendReadModel()
        .build(
            contract=source_102
        )
    )

    command_center_104 = b104.build_command_center(
        read_model=read_model_103
    )

    check(
        "BLOCK104 RUNTIME CERTIFIED",
        command_center_104.get("status") == "CERTIFIED",
    )

    check(
        "BLOCK104 RUNTIME ID",
        str(command_center_104.get("block_id")) == "104",
    )

    # --------------------------------------------------------------
    # 104 -> 106
    # --------------------------------------------------------------

    block106 = objects.get("106")

    integration_payload = (
        block106.build_integration_payload(
            command_center_104
        )
    )

    check(
        "104 -> 106 RUNTIME LINEAGE",
        str(integration_payload.get("integration", {}).get("source_block_id"))
        == "104",
    )

    check(
        "BLOCK106 RUNTIME VALIDATION",
        block106.validate_payload(
            integration_payload
        ),
    )

    # --------------------------------------------------------------
    # 106 -> 107
    # --------------------------------------------------------------

    block107 = objects.get("107")

    application_snapshot = (
        block107.build_application_snapshot(
            integration_payload
        )
    )

    check(
        "106 -> 107 RUNTIME LINEAGE",
        str(application_snapshot.get("application", {}).get("source_block_id"))
        == "106",
    )

    check(
        "BLOCK107 RUNTIME VALIDATION",
        block107.validate_application_snapshot(
            application_snapshot
        ),
    )

    # --------------------------------------------------------------
    # 107 -> 108
    # --------------------------------------------------------------

    block108 = objects.get("108")

    application_service_model = (
        block108.build_application_service_model(
            application_snapshot
        )
    )

    check(
        "107 -> 108 RUNTIME LINEAGE",
        str(application_service_model.get("lineage", {}).get("source_block"))
        == "107",
    )

    check(
        "BLOCK108 RUNTIME VALIDATION",
        block108.validate_application_service_model(
            application_service_model
        ),
    )

    # --------------------------------------------------------------
    # 108 -> 109
    # --------------------------------------------------------------

    block109 = objects.get("109")

    query_model = block109.build_query_model(
        application_service_model=application_service_model
    )

    check(
        "108 -> 109 RUNTIME LINEAGE",
        str(query_model.get("query", {}).get("source_block_id"))
        == "108",
    )

    check(
        "BLOCK109 RUNTIME VALIDATION",
        block109.validate_query_model(
            query_model
        ),
    )

    # --------------------------------------------------------------
    # Confirm the complete runtime chain terminates at Block 109.
    # --------------------------------------------------------------

    check(
        "GOLDEN CHAIN TERMINATES AT BLOCK109",
        str(query_model.get("query", {}).get("block_id")) == "109",
    )

    print()
    print("RUNTIME CHAIN : 104 -> 106 -> 107 -> 108 -> 109 : PASS")

except Exception as exc:
    check(
        "RUNTIME GOLDEN CHAIN LINEAGE",
        False,
        repr(exc),
    )


# ======================================================================
# SHA-256 / INTEGRITY CONTRACT
# ======================================================================

section("BLOCK 109 INTEGRITY CONTRACT")

try:

    source_file = (
        "services/quantitative/"
        "block109_institutional_application_query_gateway.py"
    )

    with open(source_file, "r", encoding="utf-8") as fh:
        source = fh.read()

    check(
        "BLOCK109 SHA-256 ALGORITHM DECLARED",
        '"SHA-256"' in source,
    )

    check(
        "BLOCK109 INTEGRITY SECTION PRESENT",
        '"integrity"' in source,
    )

    check(
        "BLOCK109 LINEAGE SECTION PRESENT",
        '"lineage"' in source,
    )

except Exception as exc:
    check(
        "BLOCK109 INTEGRITY SOURCE INSPECTION",
        False,
        repr(exc),
    )
# ======================================================================

section("BLOCK 109 INTEGRITY CONTRACT")

try:

    check(
        "BLOCK109 SHA-256 ALGORITHM DECLARED",
        '"SHA-256"' in source,
    )

    check(
        "BLOCK109 INTEGRITY SECTION PRESENT",
        '"integrity"' in source,
    )

    check(
        "BLOCK109 LINEAGE SECTION PRESENT",
        '"lineage"' in source,
    )

except Exception as exc:
    check(
        "BLOCK109 INTEGRITY SOURCE INSPECTION",
        False,
        repr(exc),
    )


# ======================================================================
# NON-MUTATION SOURCE CONTRACT
# ======================================================================

section("NON-MUTATION SOURCE CONTRACT")

for number, module in [
    ("106", b106),
    ("107", b107),
    ("108", b108),
    ("109", b109),
]:

    try:
        filename = inspect.getsourcefile(module)

        if filename:

            with open(
                filename,
                "r",
                encoding="utf-8",
            ) as fh:
                text = fh.read().lower()

            forbidden_terms = [
                "submit_order(",
                "broker.submit(",
                "execute_order(",
                "place_order(",
                "create_order(",
            ]

            hits = [
                term
                for term in forbidden_terms
                if term in text
            ]

            check(
                f"BLOCK {number} FORBIDDEN EXECUTION API ABSENCE",
                len(hits) == 0,
                safe_repr(hits),
            )

    except Exception as exc:
        warn(
            f"BLOCK {number} NON-MUTATION SOURCE SCAN FAILED",
            repr(exc),
        )


# ======================================================================
# OBJECT IMMUTABILITY / DETACHMENT PROBE
# ======================================================================

section("READ-ONLY DETACHMENT PROBE")

for number, obj in objects.items():

    for method_name in [
        "snapshot",
        "get_snapshot",
        "build_snapshot",
        "read_only_snapshot",
    ]:

        if not hasattr(obj, method_name):
            continue

        try:

            method = getattr(obj, method_name)

            if not callable(method):
                continue

            sig = inspect.signature(method)

            if len(sig.parameters) != 0:
                continue

            first = method()

            try:
                second = method()
            except Exception:
                break

            same_identity = first is second

            print(
                f"BLOCK {number} {method_name}: "
                f"same_identity={same_identity}"
            )

            if isinstance(first, dict) and isinstance(second, dict):

                second["__EROS_GATE_PROBE__"] = True

                check(
                    f"BLOCK {number} SNAPSHOT DETACHED",
                    "__EROS_GATE_PROBE__"
                    not in first,
                )

            elif isinstance(first, list) and isinstance(second, list):

                second.append("__EROS_GATE_PROBE__")

                check(
                    f"BLOCK {number} SNAPSHOT DETACHED",
                    "__EROS_GATE_PROBE__"
                    not in first,
                )

            else:

                check(
                    f"BLOCK {number} SNAPSHOT IDENTITY SAFE",
                    not same_identity,
                    f"type={type(first).__name__}",
                )

            break

        except Exception as exc:
            print(
                f"[WARN] BLOCK {number} DETACHMENT "
                f"{method_name}: {repr(exc)}"
            )


# ======================================================================
# HASH PROBE
# ======================================================================

section("DETERMINISTIC HASH PROBE")

def canonical_hash(value):

    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


for number, value in snapshots.items():

    try:

        h1 = canonical_hash(value)
        h2 = canonical_hash(copy.deepcopy(value))

        check(
            f"BLOCK {number} DETERMINISTIC HASH",
            h1 == h2,
            f"{h1}",
        )

    except Exception as exc:
        warn(
            f"BLOCK {number} HASH PROBE FAILED",
            repr(exc),
        )


# ======================================================================
# MODULE CONTRACT SUMMARY
# ======================================================================

section("MODULE CONTRACT SUMMARY")

for number, module in [
    ("106", b106),
    ("107", b107),
    ("108", b108),
    ("109", b109),
]:

    filename = inspect.getsourcefile(module)

    print(
        f"BLOCK {number} : "
        f"{filename}"
    )


# ======================================================================
# FINAL
# ======================================================================

section("GOLDEN CHAIN GATE RESULT")

print(f"PASS COUNT : {PASS}")
print(f"FAIL COUNT : {FAIL}")
print(f"WARN COUNT : {WARN}")

print()

if FAIL == 0:
    print("RESULT : PASS")
    print(
        "106-109 runtime structural/safety gate passed."
    )
else:
    print("RESULT : FAIL")
    print(
        "One or more runtime contracts require investigation."
    )

print()
print("BLOCK 110 : HOLD")
print("BLOCK 111 : HOLD")
print("BLOCK 112 : HOLD")
print("BLOCK 113 : HOLD")

print()
print("MUTATION : NONE")
print("LIVE EXECUTION : NONE")
print("BROKER SUBMISSION : NONE")
print("ORDER CREATION : NONE")







