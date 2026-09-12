from __future__ import annotations

import inspect
import json
from pprint import pprint

from services.quantitative.block102_frontend_contract import (
    EROSBlock102FrontendContract,
)
from services.quantitative.block103_institutional_frontend_read_model import (
    EROSBlock103InstitutionalFrontendReadModel,
)


def heading(title: str) -> None:
    print("")
    print("=" * 70)
    print(title)
    print("=" * 70)


def dump_object(name, value) -> None:
    print("")
    print(f"--- {name} TYPE ---")
    print(type(value))

    print("")
    print(f"--- {name} ---")

    try:
        print(
            json.dumps(
                value,
                indent=2,
                sort_keys=True,
                default=str,
            )
        )
    except Exception:
        pprint(value)


heading("EROS 3.0 - ACTUAL BLOCK 103 OUTPUT DIAGNOSTIC")

print("READ ONLY")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO MUTATION")

heading("1. IMPORTS")

print("BLOCK 102 IMPORT : PASS")
print("BLOCK 103 IMPORT : PASS")

heading("2. ACTUAL CLASS CONTRACT")

print("BLOCK 102 CLASS:")
print(EROSBlock102FrontendContract)

print("")
print("BLOCK 103 CLASS:")
print(EROSBlock103InstitutionalFrontendReadModel)

heading("3. ACTUAL METHOD SIGNATURES")

print(
    "BLOCK 102 BUILD    :",
    inspect.signature(EROSBlock102FrontendContract.build),
)

print(
    "BLOCK 102 SNAPSHOT :",
    inspect.signature(EROSBlock102FrontendContract.snapshot),
)

print(
    "BLOCK 103 BUILD    :",
    inspect.signature(EROSBlock103InstitutionalFrontendReadModel.build),
)

print(
    "BLOCK 103 SNAPSHOT :",
    inspect.signature(EROSBlock103InstitutionalFrontendReadModel.snapshot),
)

heading("4. BLOCK 102 PUBLIC MEMBERS")

block102 = EROSBlock102FrontendContract()

print("INSTANCE TYPE:", type(block102))

for name in dir(block102):
    if name.startswith("_"):
        continue

    try:
        value = getattr(block102, name)

        if callable(value):
            print("PUBLIC METHOD:", name)
        else:
            print(
                "PUBLIC VALUE :",
                name,
                "=",
                repr(value),
            )
    except Exception as exc:
        print(
            "PUBLIC MEMBER ERROR:",
            name,
            repr(exc),
        )

heading("5. BUILD REAL BLOCK 102 CONTRACT")

# These are deliberately read-only certification fixtures.
block94 = {
    "status": "CERTIFIED",
    "block_id": 94,
    "engine_version": "EROS-3.0-BLOCK-94",
}

block95 = {
    "status": "CERTIFIED",
    "block_id": 95,
    "engine_version": "EROS-3.0-BLOCK-95",
}

block96 = {
    "status": "CERTIFIED",
    "block_id": 96,
    "engine_version": "EROS-3.0-BLOCK-96",
}

block97 = {
    "status": "CERTIFIED",
    "block_id": 97,
    "engine_version": "EROS-3.0-BLOCK-97",
}

block98 = {
    "status": "CERTIFIED",
    "block_id": 98,
    "engine_version": "EROS-3.0-BLOCK-98",
    "governance_status": "APPROVED",
}

block99 = {
    "status": "CERTIFIED",
    "block_id": 99,
    "engine_version": "EROS-3.0-BLOCK-99",
    "authorization": "AUTHORIZED",
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "quantity": 100.0,
    "reference_price": 2500.0,
}

block100 = {
    "status": "CERTIFIED",
    "block_id": 100,
    "engine_version": "EROS-3.0-BLOCK-100",
    "execution_status": "SIMULATED",
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "requested_quantity": 100.0,
    "filled_quantity": 100.0,
    "reference_price": 2500.0,
    "fill_price": 2501.25,
    "fill_status": "FILLED",
    "slippage_bps": 5.0,
    "transaction_cost": 250.125,
}

block101 = {
    "status": "CERTIFIED",
    "block_id": 101,
    "engine_version": "EROS-3.0-BLOCK-101",
    "source_block": 100,
    "reconciliation_status": "RECONCILED",
    "quantity_reconciled": True,
    "price_reconciled": True,
    "value_reconciled": True,
    "cost_reconciled": True,
    "lineage_reconciled": True,
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "quantity": 100.0,
    "reference_price": 2500.0,
    "fill_price": 2501.25,
}

block102_output = block102.build(
    block94=block94,
    block95=block95,
    block96=block96,
    block97=block97,
    block98=block98,
    block99=block99,
    block100=block100,
    block101=block101,
)

dump_object(
    "BLOCK 102 ACTUAL OUTPUT",
    block102_output,
)

heading("6. BLOCK 102 OUTPUT STRUCTURE")

if isinstance(block102_output, dict):
    print("BLOCK 102 OUTPUT TYPE : dict")
    print("BLOCK 102 KEYS:")

    for key in block102_output.keys():
        print(
            "  ",
            repr(key),
            "=>",
            type(block102_output[key]).__name__,
        )

    print("")
    print(
        "BLOCK 102 block_id =",
        repr(block102_output.get("block_id")),
    )

    print(
        "BLOCK 102 status =",
        repr(block102_output.get("status")),
    )

    print(
        "BLOCK 102 source_block =",
        repr(block102_output.get("source_block")),
    )

else:
    print(
        "BLOCK 102 OUTPUT IS NOT DICT:",
        type(block102_output),
    )

heading("7. BLOCK 103 VALIDATION REQUIREMENTS")

block103 = EROSBlock103InstitutionalFrontendReadModel()

print("BLOCK 103 INSTANCE:", type(block103))

print("")
print("BLOCK 103 PUBLIC VALUES:")

for name in dir(block103):
    if name.startswith("_"):
        continue

    try:
        value = getattr(block103, name)

        if callable(value):
            continue

        print(
            name,
            "=",
            repr(value),
        )

    except Exception:
        pass

heading("8. BLOCK 103 INTERNAL VALIDATION SOURCE")

source_path = "services/quantitative/" "block103_institutional_frontend_read_model.py"

print("SOURCE:", source_path)

with open(
    source_path,
    encoding="utf-8",
) as handle:
    source_text = handle.read()

lines = source_text.splitlines()

for index, line in enumerate(lines, start=1):
    if (
        "_validate_source" in line
        or "REQUIRED" in line
        or "BLOCK103_INVALID" in line
        or "SOURCE_BLOCK" in line
        or "BLOCK_ID" in line
    ):
        start = max(1, index - 3)
        end = min(len(lines), index + 8)

        print("")
        print(f"--- SOURCE LINES {start}-{end} ---")

        for number in range(start, end + 1):
            print(
                f"{number:04d}:",
                lines[number - 1],
            )

heading("9. ATTEMPT ACTUAL BLOCK 103 BUILD")

try:

    read_model = block103.build(contract=block102_output)

    print("BLOCK 103 BUILD : PASS")

    dump_object(
        "BLOCK 103 ACTUAL OUTPUT",
        read_model,
    )

except Exception as exc:

    print("BLOCK 103 BUILD : FAILED")

    print("")
    print("EXCEPTION TYPE:")
    print(type(exc))

    print("")
    print("EXCEPTION:")
    print(str(exc))

    print("")
    print("This is the important diagnostic result.")

heading("10. BLOCK 103 OUTPUT IDENTITY ANALYSIS")

try:

    if "read_model" in locals():

        print(
            "read_model type:",
            type(read_model),
        )

        if isinstance(read_model, dict):

            print(
                "read_model block_id:",
                repr(read_model.get("block_id")),
            )

            print(
                "read_model source_block:",
                repr(read_model.get("source_block")),
            )

            print(
                "read_model status:",
                repr(read_model.get("status")),
            )

            print("")
            print("read_model top-level keys:")

            for key in read_model.keys():
                print(
                    "  ",
                    repr(key),
                )

except Exception as exc:

    print(
        "IDENTITY ANALYSIS ERROR:",
        repr(exc),
    )

heading("11. DIAGNOSTIC CONCLUSION")

if "read_model" in locals():

    print("BLOCK 103 RUNTIME : PASS")

    print("ACTUAL BLOCK 103 OUTPUT CAPTURED : YES")

    print("NEXT STEP : USE ACTUAL BLOCK 103 OUTPUT CONTRACT")

else:

    print("BLOCK 103 RUNTIME : FAILED")

    print("NEXT STEP : FIX TEST FIXTURE / UPSTREAM CONTRACT")

print("")
print("=" * 70)
print("BLOCK 106 DIAGNOSTIC COMPLETE")
print("=" * 70)
