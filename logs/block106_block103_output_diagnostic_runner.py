from __future__ import annotations

import inspect
import json

from services.quantitative.block102_frontend_contract import (
    EROSBlock102FrontendContract,
)
from services.quantitative.block103_institutional_frontend_read_model import (
    EROSBlock103InstitutionalFrontendReadModel,
)

print("=" * 70)
print("EROS 3.0 - BLOCK 103 ACTUAL OUTPUT DIAGNOSTIC")
print("=" * 70)
print("READ ONLY")
print("NO SOURCE CHANGES")
print("NO GIT COMMIT")
print("NO GIT PUSH")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print()

# ------------------------------------------------------------------
# 1. IMPORTS
# ------------------------------------------------------------------

print("=" * 70)
print("1. IMPORT VERIFICATION")
print("=" * 70)

print("BLOCK 102 IMPORT : PASS")
print("BLOCK 103 IMPORT : PASS")
print()

# ------------------------------------------------------------------
# 2. SIGNATURES
# ------------------------------------------------------------------

print("=" * 70)
print("2. ACTUAL SIGNATURES")
print("=" * 70)

print("BLOCK 102 BUILD:")
print(inspect.signature(EROSBlock102FrontendContract.build))
print()

print("BLOCK 103 BUILD:")
print(inspect.signature(EROSBlock103InstitutionalFrontendReadModel.build))
print()

# ------------------------------------------------------------------
# 3. BUILD REAL BLOCK 102 CONTRACT
# ------------------------------------------------------------------

print("=" * 70)
print("3. BUILD BLOCK 102")
print("=" * 70)

block102 = EROSBlock102FrontendContract()

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
    "status": "APPROVED",
    "block_id": 98,
    "engine_version": "EROS-3.0-BLOCK-98",
}

block99 = {
    "status": "CERTIFIED",
    "block_id": 99,
    "engine_version": "EROS-3.0-BLOCK-99",
    "authorization": "AUTHORIZED",
}

block100 = {
    "status": "CERTIFIED",
    "block_id": 100,
    "execution_status": "SIMULATED",
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "requested_quantity": 100.0,
    "filled_quantity": 100.0,
    "reference_price": 2500.0,
    "fill_price": 2501.25,
    "fill_status": "FILLED",
}

block101 = {
    "status": "CERTIFIED",
    "block_id": 101,
    "source_block": 100,
    "reconciliation": "RECONCILED",
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "quantity_reconciled": True,
    "price_reconciled": True,
    "value_reconciled": True,
    "cost_reconciled": True,
    "lineage_reconciled": True,
}

contract = block102.build(
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

print("BLOCK 102 TOP LEVEL:")
for key, value in contract.items():
    print(f"  {key!r}: {type(value).__name__} = {value!r}")

print()

print("BLOCK 102 COMPLETE JSON:")
print(json.dumps(contract, indent=2, default=str))

# ------------------------------------------------------------------
# 4. BLOCK 103
# ------------------------------------------------------------------

print("=" * 70)
print("4. BUILD BLOCK 103 FROM ACTUAL BLOCK 102 OUTPUT")
print("=" * 70)

block103 = EROSBlock103InstitutionalFrontendReadModel()

print("BLOCK 103 INSTANCE : PASS")
print()

try:
    read_model = block103.build(contract=contract)

    print("BLOCK 103 BUILD : PASS")
    print()

except Exception as exc:
    print("BLOCK 103 BUILD : FAILED")
    print()
    print("EXCEPTION TYPE:")
    print(type(exc).__name__)
    print()
    print("EXCEPTION:")
    print(str(exc))
    print()

    print("=" * 70)
    print("BLOCK 103 SOURCE VALIDATION DIAGNOSTIC")
    print("=" * 70)

    source_validator = getattr(
        block103,
        "_validate_source",
        None,
    )

    print("VALIDATOR PRESENT :", source_validator is not None)

    if source_validator is not None:
        print()
        print("CALLING _validate_source(contract)...")

        try:
            source_validator(contract)
            print("SOURCE VALIDATION : PASS")
        except Exception as validator_exc:
            print("SOURCE VALIDATION : FAILED")
            print("TYPE :", type(validator_exc).__name__)
            print("ERROR:", str(validator_exc))

    print()
    print("=" * 70)
    print("BLOCK 103 DIAGNOSTIC TERMINATED")
    print("=" * 70)

    raise

# ------------------------------------------------------------------
# 5. ACTUAL BLOCK 103 OUTPUT
# ------------------------------------------------------------------

print("=" * 70)
print("5. ACTUAL BLOCK 103 OUTPUT")
print("=" * 70)

print("OUTPUT TYPE:")
print(type(read_model).__name__)
print()

print("TOP LEVEL KEYS:")
for key in read_model.keys():
    print("  ", repr(key))

print()

print("TOP LEVEL VALUES / TYPES:")
for key, value in read_model.items():
    print(f"  {key!r}: " f"type={type(value).__name__}, " f"value={value!r}")

print()

print("=" * 70)
print("6. BLOCK 103 IDENTITY CHECK")
print("=" * 70)

print("read_model.get('status')    :", repr(read_model.get("status")))
print("read_model.get('block_id')  :", repr(read_model.get("block_id")))
print("read_model.get('block_id') type:", type(read_model.get("block_id")).__name__)

print()

print("EXPECTED:")
print("  status   = CERTIFIED")
print("  block_id = 103")

print()

print("ACTUAL:")
print("  status   =", repr(read_model.get("status")))
print("  block_id =", repr(read_model.get("block_id")))

print()

# ------------------------------------------------------------------
# 7. IMPORTANT NESTED STRUCTURES
# ------------------------------------------------------------------

print("=" * 70)
print("7. BLOCK 103 NESTED STRUCTURE")
print("=" * 70)

for section in [
    "dashboard",
    "pipeline",
    "risk",
    "governance",
    "intent",
    "execution",
    "reconciliation",
    "lineage",
    "safety",
]:
    print()
    print(f"--- {section.upper()} ---")

    value = read_model.get(section)

    if isinstance(value, dict):
        for key, item in value.items():
            print(f"  {key!r}: {item!r}")
    else:
        print("  TYPE :", type(value).__name__)
        print("  VALUE:", repr(value))

# ------------------------------------------------------------------
# 8. COMPLETE READ MODEL JSON
# ------------------------------------------------------------------

print()
print("=" * 70)
print("8. COMPLETE BLOCK 103 JSON")
print("=" * 70)

print(
    json.dumps(
        read_model,
        indent=2,
        default=str,
    )
)

# ------------------------------------------------------------------
# 9. CONTRACT COMPARISON
# ------------------------------------------------------------------

print()
print("=" * 70)
print("9. CONTRACT COMPARISON")
print("=" * 70)

print("BLOCK 102 block_id :", repr(contract.get("block_id")))
print("BLOCK 103 block_id :", repr(read_model.get("block_id")))

print()

if read_model.get("block_id") == 103:
    print("BLOCK 103 ID CONTRACT : PASS")
else:
    print("BLOCK 103 ID CONTRACT : FAIL")
    print("IMPORTANT: DO NOT MODIFY SOURCE YET.")

print()

# ------------------------------------------------------------------
# 10. FINAL
# ------------------------------------------------------------------

print("=" * 70)
print("BLOCK 103 ACTUAL OUTPUT DIAGNOSTIC COMPLETE")
print("=" * 70)
