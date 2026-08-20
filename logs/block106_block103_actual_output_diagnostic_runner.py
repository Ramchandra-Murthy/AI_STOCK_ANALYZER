from __future__ import annotations

import json
import inspect
from pprint import pprint

from services.quantitative.block102_frontend_contract import (
    EROSBlock102FrontendContract,
)

from services.quantitative.block103_institutional_frontend_read_model import (
    EROSBlock103InstitutionalFrontendReadModel,
)


def section(title: str) -> None:
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def safe_json(value):
    try:
        return json.dumps(
            value,
            indent=2,
            sort_keys=True,
            default=str,
        )
    except Exception as exc:
        return f"<JSON ERROR: {exc}>"


section("EROS 3.0 - BLOCK 103 ACTUAL OUTPUT DIAGNOSTIC")

print("READ ONLY")
print("NO SOURCE CHANGES")
print("NO COMMIT")
print("NO PUSH")
print("NO BROKER")
print("NO LIVE EXECUTION")


section("1. IMPORTS")

print("BLOCK 102 IMPORT : PASS")
print("BLOCK 103 IMPORT : PASS")


section("2. ACTUAL CLASS INFORMATION")

print("BLOCK 102 CLASS:")
print(EROSBlock102FrontendContract)

print()
print("BLOCK 103 CLASS:")
print(EROSBlock103InstitutionalFrontendReadModel)


section("3. ACTUAL METHOD SIGNATURES")

print(
    "BLOCK 102 BUILD    :",
    inspect.signature(EROSBlock102FrontendContract.build),
)

print(
    "BLOCK 103 BUILD    :",
    inspect.signature(EROSBlock103InstitutionalFrontendReadModel.build),
)

print(
    "BLOCK 103 SNAPSHOT :",
    inspect.signature(EROSBlock103InstitutionalFrontendReadModel.snapshot),
)


section("4. BUILD ACTUAL BLOCK 102 CONTRACT")

block102 = EROSBlock102FrontendContract()

print("BLOCK 102 INSTANCE : PASS")

# ------------------------------------------------------------
# Create the actual upstream layers expected by Block 102.
# These are read-only diagnostic contracts only.
# ------------------------------------------------------------

block94 = {
    "status": "CERTIFIED",
    "block_id": 94,
    "engine_version": "EROS-3.0-BLOCK-94",
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "quantity": 100.0,
    "reference_price": 2500.0,
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
    "status": "APPROVED",
    "block_id": 98,
    "engine_version": "EROS-3.0-BLOCK-98",
}

block99 = {
    "status": "CERTIFIED",
    "block_id": 99,
    "engine_version": "EROS-3.0-BLOCK-99",
}

block100 = {
    "status": "CERTIFIED",
    "execution_status": "SIMULATED",
    "block_id": 100,
    "engine_version": "EROS-3.0-BLOCK-100",
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "requested_quantity": 100.0,
    "filled_quantity": 100.0,
    "reference_price": 2500.0,
    "fill_price": 2501.25,
}

block101 = {
    "status": "CERTIFIED",
    "block_id": 101,
    "engine_version": "EROS-3.0-BLOCK-101",
    "reconciliation": "RECONCILED",
    "symbol": "RELIANCE.NS",
    "action": "BUY",
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


section("5. CALL ACTUAL BLOCK 102 BUILD")

contract102 = block102.build(
    block94=block94,
    block95=block95,
    block96=block96,
    block97=block97,
    block98=block98,
    block99=block99,
    block100=block100,
    block101=block101,
)

print("BLOCK 102 BUILD : PASS")
print()
print("BLOCK 102 TOP LEVEL KEYS:")
print(list(contract102.keys()))

print()
print("BLOCK 102 STATUS:")
print(repr(contract102.get("status")))

print()
print("BLOCK 102 BLOCK_ID:")
print(repr(contract102.get("block_id")))

print()
print("BLOCK 102 ENGINE_VERSION:")
print(repr(contract102.get("engine_version")))

print()
print("BLOCK 102 FULL OUTPUT:")
print(safe_json(contract102))


section("6. CALL ACTUAL BLOCK 103 BUILD")

block103 = EROSBlock103InstitutionalFrontendReadModel()

print("BLOCK 103 INSTANCE : PASS")

print()
print("BLOCK 103 EXPECTED BLOCK_ID:")
print(repr(block103.BLOCK_ID))

print()
print("BLOCK 103 REQUIRED_BLOCKS:")
print(repr(block103.REQUIRED_BLOCKS))

print()
print("FEEDING BLOCK 102 OUTPUT DIRECTLY INTO BLOCK 103:")
print("contract = contract102")


try:
    read_model = block103.build(
        contract=contract102
    )

    print()
    print("BLOCK 103 BUILD : PASS")

except Exception as exc:
    print()
    print("BLOCK 103 BUILD : FAILED")
    print("EXCEPTION TYPE :", type(exc).__name__)
    print("EXCEPTION      :", str(exc))

    section("7. BLOCK 103 FAILURE DIAGNOSTIC")

    print("BLOCK 102 ACTUAL BLOCK_ID:")
    print(repr(contract102.get("block_id")))

    print()
    print("BLOCK 102 ACTUAL STATUS:")
    print(repr(contract102.get("status")))

    print()
    print("BLOCK 102 ACTUAL ENGINE VERSION:")
    print(repr(contract102.get("engine_version")))

    print()
    print("BLOCK 102 TOP LEVEL KEYS:")
    for key in contract102.keys():
        print("  -", key)

    print()
    print("BLOCK 103 EXPECTS:")
    print("  BLOCK_ID       =", repr(block103.BLOCK_ID))
    print("  REQUIRED_BLOCKS=", repr(block103.REQUIRED_BLOCKS))

    print()
    print("BLOCK 103 SOURCE VALIDATION:")
    try:
        block103._validate_source(contract102)
        print("VALIDATION : PASS")
    except Exception as validation_exc:
        print("VALIDATION : FAILED")
        print("TYPE       :", type(validation_exc).__name__)
        print("MESSAGE    :", str(validation_exc))

    print()
    print("BLOCK 103 SOURCE VALIDATION CODE:")
    try:
        print(
            inspect.getsource(
                EROSBlock103InstitutionalFrontendReadModel._validate_source
            )
        )
    except Exception as source_exc:
        print("SOURCE INSPECTION ERROR:", source_exc)

    print()
    print("DIAGNOSTIC RESULT:")
    print("BLOCK 103 ACTUAL OUTPUT : NOT CREATED")
    print("ROOT CAUSE MUST BE IDENTIFIED FROM THE ABOVE CONTRACT DATA")

    raise SystemExit(1)


section("8. ACTUAL BLOCK 103 OUTPUT")

print("TOP LEVEL KEYS:")
print(list(read_model.keys()))

print()
print("STATUS:")
print(repr(read_model.get("status")))

print()
print("BLOCK_ID:")
print(repr(read_model.get("block_id")))

print()
print("ENGINE_VERSION:")
print(repr(read_model.get("engine_version")))

print()
print("DASHBOARD:")
pprint(read_model.get("dashboard"))

print()
print("PIPELINE:")
pprint(read_model.get("pipeline"))

print()
print("GOVERNANCE:")
pprint(read_model.get("governance"))

print()
print("INTENT:")
pprint(read_model.get("intent"))

print()
print("EXECUTION:")
pprint(read_model.get("execution"))

print()
print("RECONCILIATION:")
pprint(read_model.get("reconciliation"))

print()
print("LINEAGE:")
pprint(read_model.get("lineage"))

print()
print("SAFETY:")
pprint(read_model.get("safety"))

print()
print("FULL BLOCK 103 JSON:")
print(safe_json(read_model))


section("9. BLOCK 103 CONTRACT ASSERTIONS")

checks = {
    "status_is_certified": read_model.get("status") == "CERTIFIED",
    "block_id_is_103": read_model.get("block_id") == 103,
    "engine_version_present": bool(read_model.get("engine_version")),
    "pipeline_present": "pipeline" in read_model,
    "risk_present": "risk" in read_model,
    "governance_present": "governance" in read_model,
    "intent_present": "intent" in read_model,
    "execution_present": "execution" in read_model,
    "reconciliation_present": "reconciliation" in read_model,
    "lineage_present": "lineage" in read_model,
    "safety_present": "safety" in read_model,
}

all_pass = True

for name, result in checks.items():
    state = "PASS" if result else "FAIL"
    print(f"{name:32} : {state}")
    if not result:
        all_pass = False


section("10. FINAL DIAGNOSTIC RESULT")

if all_pass:
    print("BLOCK 103 ACTUAL OUTPUT : PASS")
    print("BLOCK 103 CONTRACT       : PASS")
    print("NEXT STEP               : PROCEED TO BLOCK 104 -> BLOCK 106")
    raise SystemExit(0)

print("BLOCK 103 ACTUAL OUTPUT : FAILED")
print("BLOCK 103 CONTRACT       : FAILED")
raise SystemExit(1)
