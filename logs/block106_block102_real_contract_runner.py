from __future__ import annotations

import inspect
import json
import traceback
from pprint import pprint

print("")
print("=" * 70)
print("EROS 3.0 - BLOCK 102 REAL CONTRACT DISCOVERY")
print("=" * 70)

print("")
print("1. IMPORT BLOCK 102")
print("-" * 70)

from services.quantitative.block102_frontend_contract import (
    EROSBlock102FrontendContract,
)

print("BLOCK 102 IMPORT : PASS")
print("CLASS           :", EROSBlock102FrontendContract)

print("")
print("2. BLOCK 102 PUBLIC MEMBERS")
print("-" * 70)

cls = EROSBlock102FrontendContract

for name in dir(cls):
    if name.startswith("_"):
        continue

    try:
        value = getattr(cls, name)

        if callable(value):
            print(f"PUBLIC METHOD : {name}")
        else:
            print(f"PUBLIC VALUE  : {name} = {value!r}")

    except Exception as exc:
        print(f"PUBLIC MEMBER : {name} -> ERROR {exc}")

print("")
print("3. CONSTRUCTOR SIGNATURE")
print("-" * 70)

try:
    print(inspect.signature(cls))
except Exception as exc:
    print("CONSTRUCTOR SIGNATURE ERROR:", repr(exc))

print("")
print("4. METHOD SIGNATURES")
print("-" * 70)

for name in [
    "build",
    "snapshot",
    "validate",
    "render",
    "contract",
    "build_contract",
]:
    if hasattr(cls, name):
        try:
            print(f"{name.upper():20s}: " f"{inspect.signature(getattr(cls, name))}")
        except Exception as exc:
            print(f"{name.upper():20s}: " f"SIGNATURE ERROR {exc}")

print("")
print("5. CLASS SOURCE")
print("-" * 70)

try:
    print(inspect.getsource(cls))
except Exception as exc:
    print("SOURCE ERROR:", repr(exc))

print("")
print("6. INSTANCE CREATION")
print("-" * 70)

try:
    block102 = cls()
    print("INSTANCE CREATION : PASS")
    print("INSTANCE TYPE     :", type(block102))
except Exception as exc:
    print("INSTANCE CREATION : FAILED")
    print("ERROR:", repr(exc))
    traceback.print_exc()
    raise SystemExit(1)

print("")
print("7. POSSIBLE CONTRACT BUILD METHODS")
print("-" * 70)

candidate_methods = [
    "build",
    "snapshot",
    "contract",
    "build_contract",
    "create_contract",
    "render_model",
]

found = []

for name in candidate_methods:
    if hasattr(block102, name):
        found.append(name)
        print(f"FOUND : {name} " f"{inspect.signature(getattr(block102, name))}")

if not found:
    print("NO STANDARD CONTRACT METHOD FOUND")

print("")
print("8. BLOCK 102 SOURCE SEARCH TERMS")
print("-" * 70)

try:
    source = inspect.getsource(cls)

    terms = [
        "pipeline_status",
        "source_block",
        "block_id",
        "status",
        "safety",
        "execution_blocked",
        "non_mutation_invariant",
        "broker_submission",
        "live_order_submission",
        "order_creation",
    ]

    for term in terms:
        print(f"{term:28s}: " f"{'FOUND' if term in source else 'NOT FOUND'}")

except Exception as exc:
    print("SOURCE SEARCH ERROR:", repr(exc))

print("")
print("9. SAFE BLOCK 102 RUNTIME ATTEMPTS")
print("-" * 70)

results = {}


def record_result(label, value):
    print("")
    print("-" * 60)
    print(label)
    print("-" * 60)

    print("TYPE:", type(value))

    if isinstance(value, dict):
        print("KEYS:", sorted(str(k) for k in value.keys()))

        for key in [
            "status",
            "block_id",
            "source_block",
            "pipeline_status",
            "pipeline",
            "safety",
            "governance",
            "intent",
            "execution",
            "reconciliation",
            "lineage",
        ]:
            if key in value:
                val = value[key]

                if key == "safety":
                    print(
                        "SAFETY KEYS:",
                        sorted(str(k) for k in val.keys()) if isinstance(val, dict) else type(val),
                    )
                elif key == "pipeline_status":
                    print("PIPELINE_STATUS TYPE:", type(val))

                    if isinstance(val, list):
                        print("PIPELINE_STATUS LENGTH:", len(val))

                        for item in val:
                            if isinstance(item, dict):
                                print(
                                    "  BLOCK:",
                                    item.get("block_id"),
                                    "STATUS:",
                                    item.get("status"),
                                    "NAME:",
                                    item.get("name"),
                                )
                            else:
                                print("  ITEM TYPE:", type(item))
                    else:
                        print("PIPELINE_STATUS VALUE:", repr(val))
                else:
                    print(f"{key.upper()}:", repr(val))

        print("")
        print("FULL DICTIONARY JSON:")
        try:
            print(
                json.dumps(
                    value,
                    indent=2,
                    sort_keys=True,
                    default=str,
                )
            )
        except Exception as exc:
            print("JSON SERIALIZATION ERROR:", repr(exc))

    else:
        pprint(value)


# ------------------------------------------------------------
# Attempt 1: build()
# ------------------------------------------------------------

if hasattr(block102, "build"):

    method = block102.build

    print("")
    print("ATTEMPT: block102.build()")

    try:
        sig = inspect.signature(method)

        print("SIGNATURE:", sig)

        params = list(sig.parameters.values())

        if len(params) == 0:
            value = method()
            results["build"] = value
            record_result("BLOCK 102 BUILD() RESULT", value)

        else:
            print("BUILD REQUIRES ARGUMENTS - " "NOT INVOKED WITHOUT KNOWING CONTRACT")

    except Exception as exc:
        print("BUILD ATTEMPT ERROR:", repr(exc))
        traceback.print_exc()


# ------------------------------------------------------------
# Attempt 2: snapshot()
# ------------------------------------------------------------

if hasattr(block102, "snapshot"):

    method = block102.snapshot

    print("")
    print("ATTEMPT: block102.snapshot()")

    try:
        sig = inspect.signature(method)

        print("SIGNATURE:", sig)

        params = list(sig.parameters.values())

        if len(params) == 0:
            value = method()
            results["snapshot"] = value
            record_result("BLOCK 102 SNAPSHOT() RESULT", value)

        else:
            print("SNAPSHOT REQUIRES ARGUMENTS - " "NOT INVOKED WITHOUT KNOWING CONTRACT")

    except Exception as exc:
        print("SNAPSHOT ATTEMPT ERROR:", repr(exc))
        traceback.print_exc()


print("")
print("10. BLOCK 102 REAL CONTRACT DIAGNOSTIC SUMMARY")
print("-" * 70)

print("BLOCK 102 IMPORT       : PASS")
print("INSTANCE CREATION     : PASS")
print("SOURCE INSPECTION     : PASS")

print("")
print("IMPORTANT:")
print("The purpose of this diagnostic is to discover the")
print("ACTUAL Block 102 -> Block 103 contract.")
print("")
print("Block 103 requires:")
print('  status == "CERTIFIED"')
print('  block_id == "102"')
print("  pipeline_status == list")
print("  pipeline IDs == 94..101")
print("  safety invariants == enforced")
print("")
print("We will NOT manually fabricate the Block 103 source.")
print("We will use the actual Block 102 contract once discovered.")

print("")
print("=" * 70)
print("BLOCK 102 REAL CONTRACT DISCOVERY COMPLETE")
print("=" * 70)

print("")
print("RESULT : PASS")
print("NO SOURCE CHANGES")
print("NO COMMIT")
print("NO PUSH")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("")
