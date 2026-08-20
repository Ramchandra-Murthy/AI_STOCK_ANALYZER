from __future__ import annotations

import inspect
import json
import os
import sys
from pprint import pprint


ROOT = r"D:\Users\User\Desktop\AI_STOCK_ANALYZER"

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def section(title: str) -> None:
    print("")
    print("=" * 70)
    print(title)
    print("=" * 70)


def show_mapping(label: str, value):
    print("")
    print(f"--- {label} TYPE ---")
    print(type(value))

    if isinstance(value, dict):
        print(f"--- {label} KEYS ---")
        for key in value.keys():
            print(repr(key))

        print("")
        print(f"--- {label} COMPLETE REPRESENTATION ---")
        pprint(value, width=160, sort_dicts=False)

        print("")
        print(f"--- {label} JSON ---")
        try:
            print(
                json.dumps(
                    value,
                    indent=2,
                    default=str,
                    sort_keys=False,
                )
            )
        except Exception as exc:
            print(f"JSON REPRESENTATION FAILED: {exc}")

    else:
        print(f"{label} VALUE:")
        pprint(value, width=160)


def require_imports():
    section("1. IMPORT CONTRACT LAYERS")

    from services.quantitative.block102_frontend_contract import (
        EROSBlock102FrontendContract,
    )

    from services.quantitative.block103_institutional_frontend_read_model import (
        EROSBlock103InstitutionalFrontendReadModel,
    )

    from services.quantitative.block104_eros_command_center import (
        EROSBlock104CommandCenter,
    )

    from services.quantitative.block106_institutional_integration_boundary import (
        EROSBlock106InstitutionalIntegrationBoundary,
    )

    print("BLOCK 102 IMPORT : PASS")
    print("BLOCK 103 IMPORT : PASS")
    print("BLOCK 104 IMPORT : PASS")
    print("BLOCK 106 IMPORT : PASS")

    return (
        EROSBlock102FrontendContract,
        EROSBlock103InstitutionalFrontendReadModel,
        EROSBlock104CommandCenter,
        EROSBlock106InstitutionalIntegrationBoundary,
    )


def main():
    section("EROS 3.0 - BLOCK 106 ACTUAL CONTRACT DIAGNOSTIC")

    print("PYTHON EXECUTABLE:")
    print(sys.executable)

    print("")
    print("PYTHON VERSION:")
    print(sys.version)

    print("")
    print("PROJECT ROOT:")
    print(ROOT)

    (
        Block102,
        Block103,
        Block104,
        Block106,
    ) = require_imports()

    section("2. ACTUAL RUNTIME SIGNATURES")

    print("BLOCK 102 BUILD:")
    print(inspect.signature(Block102.build))

    print("")
    print("BLOCK 102 SNAPSHOT:")
    print(inspect.signature(Block102.snapshot))

    print("")
    print("BLOCK 103 BUILD:")
    print(inspect.signature(Block103.build))

    print("")
    print("BLOCK 103 SNAPSHOT:")
    print(inspect.signature(Block103.snapshot))

    print("")
    print("BLOCK 104 SNAPSHOT:")
    print(inspect.signature(Block104.snapshot))

    print("")
    print("BLOCK 106 BUILD:")
    print(inspect.signature(Block106.build_integration_payload))

    print("")
    print("BLOCK 106 SNAPSHOT:")
    print(inspect.signature(Block106.build_read_only_snapshot))

    print("")
    print("BLOCK 106 VALIDATE:")
    print(inspect.signature(Block106.validate_payload))

    section("3. BUILD REAL BLOCK 94 -> 101 INPUTS")

    # These are intentionally read-only contract dictionaries.
    block94 = {
        "status": "CERTIFIED",
        "block_id": 94,
        "symbol": "RELIANCE.NS",
        "action": "BUY",
        "quantity": 100.0,
        "reference_price": 2500.0,
    }

    block95 = {
        "status": "CERTIFIED",
        "block_id": 95,
        "source_block": 94,
    }

    block96 = {
        "status": "CERTIFIED",
        "block_id": 96,
        "source_block": 95,
    }

    block97 = {
        "status": "CERTIFIED",
        "block_id": 97,
        "source_block": 96,
    }

    block98 = {
        "status": "APPROVED",
        "block_id": 98,
        "source_block": 97,
        "governance": "APPROVED",
    }

    block99 = {
        "status": "CERTIFIED",
        "block_id": 99,
        "source_block": 98,
        "authorization": "AUTHORIZED",
    }

    block100 = {
        "status": "CERTIFIED",
        "block_id": 100,
        "source_block": 99,
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
        "source_block": 100,
        "reconciliation": "RECONCILED",
        "quantity_reconciled": True,
        "price_reconciled": True,
        "value_reconciled": True,
        "cost_reconciled": True,
        "lineage_reconciled": True,
    }

    print("BLOCK 94 : READY")
    print("BLOCK 95 : READY")
    print("BLOCK 96 : READY")
    print("BLOCK 97 : READY")
    print("BLOCK 98 : READY")
    print("BLOCK 99 : READY")
    print("BLOCK 100: READY")
    print("BLOCK 101: READY")

    section("4. BUILD ACTUAL BLOCK 102")

    block102 = Block102()

    print("BLOCK 102 INSTANCE:")
    print(type(block102))

    frontend_contract = block102.build(
        block94=block94,
        block95=block95,
        block96=block96,
        block97=block97,
        block98=block98,
        block99=block99,
        block100=block100,
        block101=block101,
    )

    show_mapping(
        "BLOCK 102 ACTUAL OUTPUT",
        frontend_contract,
    )

    print("")
    print("BLOCK 102 OUTPUT BLOCK_ID:")
    print(repr(frontend_contract.get("block_id")))

    print("")
    print("BLOCK 102 OUTPUT STATUS:")
    print(repr(frontend_contract.get("status")))

    section("5. FEED ACTUAL BLOCK 102 OUTPUT INTO BLOCK 103")

    block103 = Block103()

    print("BLOCK 103 INSTANCE:")
    print(type(block103))

    print("")
    print("CALL:")
    print("block103.build(contract=frontend_contract)")

    read_model = block103.build(
        contract=frontend_contract
    )

    print("")
    print("BLOCK 103 BUILD : PASS")

    show_mapping(
        "BLOCK 103 ACTUAL OUTPUT",
        read_model,
    )

    print("")
    print("***** BLOCK 103 ID DIAGNOSTIC *****")

    print("EXPECTED BLOCK 103 ID : 103")
    print("ACTUAL BLOCK 103 ID   :", repr(read_model.get("block_id")))

    if read_model.get("block_id") == 103:
        print("BLOCK 103 ID CHECK     : PASS")
    else:
        print("BLOCK 103 ID CHECK     : FAIL")

    print("")
    print("STATUS:")
    print(repr(read_model.get("status")))

    print("")
    print("ENGINE VERSION:")
    print(repr(read_model.get("engine_version")))

    print("")
    print("PIPELINE:")
    pprint(
        read_model.get("pipeline"),
        width=160,
        sort_dicts=False,
    )

    print("")
    print("GOVERNANCE:")
    pprint(
        read_model.get("governance"),
        width=160,
        sort_dicts=False,
    )

    print("")
    print("INTENT:")
    pprint(
        read_model.get("intent"),
        width=160,
        sort_dicts=False,
    )

    print("")
    print("EXECUTION:")
    pprint(
        read_model.get("execution"),
        width=160,
        sort_dicts=False,
    )

    print("")
    print("RECONCILIATION:")
    pprint(
        read_model.get("reconciliation"),
        width=160,
        sort_dicts=False,
    )

    print("")
    print("SAFETY:")
    pprint(
        read_model.get("safety"),
        width=160,
        sort_dicts=False,
    )

    section("6. BLOCK 103 INTERNAL CONSTANTS")

    print("BLOCK_ID:")
    print(repr(getattr(block103, "BLOCK_ID", None)))

    print("")
    print("ENGINE_VERSION:")
    print(repr(getattr(block103, "ENGINE_VERSION", None)))

    print("")
    print("REQUIRED_BLOCKS:")
    print(repr(getattr(block103, "REQUIRED_BLOCKS", None)))

    section("7. BLOCK 104 COMMAND CENTER")

    block104 = Block104()

    print("BLOCK 104 INSTANCE:")
    print(type(block104))

    print("")
    print("CALL:")
    print("block104.snapshot(read_model=read_model)")

    command_center = block104.snapshot(
        read_model=read_model
    )

    print("")
    print("BLOCK 104 SNAPSHOT : PASS")

    show_mapping(
        "BLOCK 104 ACTUAL OUTPUT",
        command_center,
    )

    print("")
    print("BLOCK 104 ID:")
    print(repr(command_center.get("block_id")))

    print("")
    print("BLOCK 104 STATUS:")
    print(repr(command_center.get("status")))

    section("8. BLOCK 106 INSTITUTIONAL INTEGRATION")

    block106 = Block106()

    print("BLOCK 106 INSTANCE:")
    print(type(block106))

    print("")
    print("CALL:")
    print("block106.build_integration_payload(command_center)")

    integration_payload = block106.build_integration_payload(
        command_center
    )

    print("")
    print("BLOCK 106 BUILD : PASS")

    show_mapping(
        "BLOCK 106 ACTUAL OUTPUT",
        integration_payload,
    )

    print("")
    print("BLOCK 106 VALIDATION:")
    try:
        valid = block106.validate_payload(
            integration_payload
        )
        print("VALIDATE RESULT:", repr(valid))

        if valid:
            print("BLOCK 106 VALIDATION : PASS")
        else:
            print("BLOCK 106 VALIDATION : FAIL")

    except Exception as exc:
        print("BLOCK 106 VALIDATION : ERROR")
        print(type(exc).__name__)
        print(str(exc))

    section("9. BLOCK 106 SAFETY POLICY")

    print("SAFETY POLICY:")
    pprint(
        getattr(block106, "SAFETY_POLICY", None),
        width=160,
        sort_dicts=False,
    )

    section("10. END-TO-END KEY SUMMARY")

    summary = {
        "block102_status": frontend_contract.get("status"),
        "block102_id": frontend_contract.get("block_id"),
        "block103_status": read_model.get("status"),
        "block103_id": read_model.get("block_id"),
        "block103_engine_version": read_model.get("engine_version"),
        "block104_status": command_center.get("status"),
        "block104_id": command_center.get("block_id"),
        "block106_status": integration_payload.get("status"),
        "block106_id": integration_payload.get("block_id"),
    }

    pprint(
        summary,
        width=160,
        sort_dicts=False,
    )

    section("11. DIAGNOSTIC CONCLUSION")

    if read_model.get("block_id") == 103:
        print("BLOCK 103 ID : CORRECT")
    else:
        print("BLOCK 103 ID : INCORRECT")
        print("")
        print(
            "IMPORTANT: The actual Block 103 output does not expose "
            "block_id=103."
        )
        print(
            "We must inspect the Block 103 contract before modifying "
            "anything."
        )

    if command_center.get("block_id") == 104:
        print("BLOCK 104 ID : CORRECT")
    else:
        print(
            "BLOCK 104 ID : NOT 104 / REQUIRES CONTRACT INSPECTION"
        )

    if integration_payload.get("block_id") == 106:
        print("BLOCK 106 ID : CORRECT")
    else:
        print(
            "BLOCK 106 ID : NOT 106 / REQUIRES CONTRACT INSPECTION"
        )

    print("")
    print("NO SOURCE FILES WERE MODIFIED BY THIS RUNNER.")
    print("NO GIT COMMIT WAS PERFORMED.")
    print("NO GIT PUSH WAS PERFORMED.")
    print("NO BROKER WAS CONTACTED.")
    print("NO LIVE EXECUTION WAS PERFORMED.")


if __name__ == "__main__":
    main()
