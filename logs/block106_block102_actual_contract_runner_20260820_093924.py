from __future__ import annotations

import inspect
import json
from pprint import pprint

print("=" * 70)
print("EROS 3.0 - BLOCK 102 ACTUAL CONTRACT INSPECTION")
print("=" * 70)
print("READ / VERIFY ONLY")
print("NO SOURCE CHANGES")
print("NO GIT COMMIT")
print("NO GIT PUSH")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print()

from services.quantitative.block102_frontend_contract import (
    EROSBlock102FrontendContract,
)

print("1. IMPORT")
print("-" * 70)
print("BLOCK 102 IMPORT : PASS")
print()

block102 = EROSBlock102FrontendContract()

print("2. CLASS")
print("-" * 70)
print("TYPE :", type(block102))
print("BLOCK_ID :", getattr(block102, "BLOCK_ID", None))
print("ENGINE_VERSION :", getattr(block102, "ENGINE_VERSION", None))
print()

print("3. BUILD SIGNATURE")
print("-" * 70)
print(inspect.signature(block102.build))
print()

print("4. PREPARE UPSTREAM OBJECTS")
print("-" * 70)

# Minimal read-only upstream contracts.
# These are deliberately structural and contain no broker/live execution.
block94 = {
    "status": "CERTIFIED",
    "block_id": 94,
}

block95 = {
    "status": "CERTIFIED",
    "block_id": 95,
}

block96 = {
    "status": "CERTIFIED",
    "block_id": 96,
}

block97 = {
    "status": "CERTIFIED",
    "block_id": 97,
}

block98 = {
    "status": "APPROVED",
    "block_id": 98,
}

block99 = {
    "status": "CERTIFIED",
    "block_id": 99,
    "authorization": "AUTHORIZED",
}

block100 = {
    "status": "CERTIFIED",
    "execution_status": "SIMULATED",
    "block_id": 100,
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "quantity": 100.0,
    "reference_price": 2500.0,
}

block101 = {
    "status": "CERTIFIED",
    "block_id": 101,
    "reconciliation": "RECONCILED",
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "quantity": 100.0,
    "reference_price": 2500.0,
}

print("BLOCK 94 : READY")
print("BLOCK 95 : READY")
print("BLOCK 96 : READY")
print("BLOCK 97 : READY")
print("BLOCK 98 : READY")
print("BLOCK 99 : READY")
print("BLOCK 100: READY")
print("BLOCK 101: READY")
print()

print("5. BUILD ACTUAL BLOCK 102")
print("-" * 70)

try:
    result = block102.build(
        block94=block94,
        block95=block95,
        block96=block96,
        block97=block97,
        block98=block98,
        block99=block99,
        block100=block100,
        block101=block101,
    )
except Exception as exc:
    print("BLOCK 102 BUILD : FAILED")
    print("EXCEPTION TYPE  :", type(exc).__name__)
    print("EXCEPTION       :", str(exc))
    raise

print("BLOCK 102 BUILD : PASS")
print()

print("6. ACTUAL RETURN TYPE")
print("-" * 70)
print("TYPE :", type(result))
print()

print("7. ACTUAL TOP-LEVEL KEYS")
print("-" * 70)

if isinstance(result, dict):
    for key in result.keys():
        print(repr(key))
else:
    print("RESULT IS NOT A DICT")

print()

print("8. ACTUAL BLOCK 102 PAYLOAD")
print("-" * 70)

try:
    print(json.dumps(result, indent=2, default=str))
except Exception:
    pprint(result)

print()

print("9. TOP-LEVEL FIELD INSPECTION")
print("-" * 70)

if isinstance(result, dict):
    for key in [
        "status",
        "block_id",
        "engine_version",
        "pipeline",
        "pipeline_count",
        "safety",
        "governance",
        "intent",
        "execution",
        "reconciliation",
        "lineage",
    ]:
        value = result.get(key, "<MISSING>")
        print(f"{key:25} : {value!r}")

print()

print("10. POSSIBLE NESTED CONTRACT FIELDS")
print("-" * 70)

if isinstance(result, dict):
    for key, value in result.items():
        print()
        print("KEY :", key)
        print("TYPE:", type(value).__name__)

        if isinstance(value, dict):
            print("NESTED KEYS:")
            for nested_key in value.keys():
                print("   ", repr(nested_key))

print()

print("11. BLOCK 102 OBJECT STATE")
print("-" * 70)

try:
    public_members = [name for name in dir(block102) if not name.startswith("_")]

    for name in public_members:
        try:
            value = getattr(block102, name)
            if not callable(value):
                print(f"{name:30} : {value!r}")
        except Exception:
            pass
except Exception as exc:
    print("PUBLIC MEMBER INSPECTION ERROR:", exc)

print()

print("=" * 70)
print("BLOCK 102 ACTUAL CONTRACT INSPECTION COMPLETE")
print("=" * 70)
print("IMPORTANT:")
print("This diagnostic does NOT modify Block 102.")
print("This diagnostic does NOT modify Block 103.")
print("This diagnostic does NOT modify Block 106.")
print("This diagnostic does NOT contact a broker.")
print("This diagnostic does NOT create an order.")
print("=" * 70)
