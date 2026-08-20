from __future__ import annotations

import inspect
import json
import os
import sys
from pprint import pprint

ROOT = os.getcwd()

print("=" * 70)
print("EROS 3.0 - BLOCK 102 -> 103 CONTRACT INSPECTION PYTHON RUNNER")
print("=" * 70)

print()
print("PYTHON:")
print(sys.executable)

print()
print("PYTHONPATH:")
print(ROOT)

print()
print("=" * 70)
print("1. IMPORT BLOCK 102 / 103 / 104 / 106")
print("=" * 70)

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

print()
print("=" * 70)
print("2. BLOCK 102 CLASS CONTRACT")
print("=" * 70)

b102 = EROSBlock102FrontendContract()

print("CLASS:", type(b102))
print("BLOCK_ID:", getattr(b102, "BLOCK_ID", None))
print("ENGINE_VERSION:", getattr(b102, "ENGINE_VERSION", None))

print()
print("BUILD SIGNATURE:")
print(inspect.signature(b102.build))

print()
print("SNAPSHOT SIGNATURE:")
print(inspect.signature(b102.snapshot))

print()
print("=" * 70)
print("3. BLOCK 103 CLASS CONTRACT")
print("=" * 70)

b103 = EROSBlock103InstitutionalFrontendReadModel()

print("CLASS:", type(b103))
print("BLOCK_ID:", getattr(b103, "BLOCK_ID", None))
print("ENGINE_VERSION:", getattr(b103, "ENGINE_VERSION", None))
print("REQUIRED_BLOCKS:", getattr(b103, "REQUIRED_BLOCKS", None))

print()
print("BUILD SIGNATURE:")
print(inspect.signature(b103.build))

print()
print("SNAPSHOT SIGNATURE:")
print(inspect.signature(b103.snapshot))

print()
print("=" * 70)
print("4. BLOCK 103 SOURCE VALIDATION METHOD")
print("=" * 70)

validate_source = getattr(b103, "_validate_source", None)

if validate_source is None:
    print("_validate_source : NOT FOUND")
else:
    print("_validate_source : FOUND")
    print(inspect.signature(validate_source))

    try:
        print()
        print("SOURCE:")
        print(inspect.getsource(validate_source))
    except Exception as exc:
        print("SOURCE READ ERROR:", repr(exc))

print()
print("=" * 70)
print("5. BLOCK 102 PUBLIC CONSTANTS")
print("=" * 70)

for name in dir(b102):
    if name.startswith("_"):
        continue

    try:
        value = getattr(b102, name)
    except Exception:
        continue

    if not callable(value):
        print(f"{name} = {value!r}")

print()
print("=" * 70)
print("6. BLOCK 103 PUBLIC CONSTANTS")
print("=" * 70)

for name in dir(b103):
    if name.startswith("_"):
        continue

    try:
        value = getattr(b103, name)
    except Exception:
        continue

    if not callable(value):
        print(f"{name} = {value!r}")

print()
print("=" * 70)
print("7. BUILD REAL BLOCK 102 INPUT")
print("=" * 70)

# Deliberately construct a read-only upstream contract.
# This does NOT create an order and does NOT touch any broker.

block94 = {
    "status": "CERTIFIED",
    "block_id": "94",
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "quantity": 100.0,
    "reference_price": 2500.0,
}

block95 = {
    "status": "CERTIFIED",
    "block_id": "95",
    "source_block": "94",
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "quantity": 100.0,
    "reference_price": 2500.0,
}

block96 = {
    "status": "CERTIFIED",
    "block_id": "96",
    "source_block": "95",
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "quantity": 100.0,
    "reference_price": 2500.0,
}

block97 = {
    "status": "CERTIFIED",
    "block_id": "97",
    "source_block": "96",
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "quantity": 100.0,
    "reference_price": 2500.0,
}

block98 = {
    "status": "APPROVED",
    "block_id": "98",
    "source_block": "97",
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "quantity": 100.0,
    "reference_price": 2500.0,
}

block99 = {
    "status": "CERTIFIED",
    "block_id": "99",
    "source_block": "98",
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "quantity": 100.0,
    "reference_price": 2500.0,
}

block100 = {
    "status": "CERTIFIED",
    "block_id": "100",
    "source_block": "99",
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "quantity": 100.0,
    "reference_price": 2500.0,
    "execution_status": "SIMULATED",
}

block101 = {
    "status": "CERTIFIED",
    "block_id": "101",
    "source_block": "100",
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "quantity": 100.0,
    "reference_price": 2500.0,
    "execution_status": "SIMULATED",
    "reconciliation": "RECONCILED",
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
print("=" * 70)
print("8. BUILD ACTUAL BLOCK 102")
print("=" * 70)

try:
    frontend_contract = b102.build(
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
    print("BLOCK 102 TOP-LEVEL KEYS:")
    pprint(list(frontend_contract.keys()))

    print()
    print("BLOCK 102 OUTPUT:")
    pprint(frontend_contract)

except Exception as exc:
    print("BLOCK 102 BUILD : FAILED")
    print(type(exc).__name__, str(exc))
    raise

print()
print("=" * 70)
print("9. BLOCK 102 OUTPUT STRUCTURE")
print("=" * 70)

print("TYPE:", type(frontend_contract).__name__)

if isinstance(frontend_contract, dict):

    print()
    print("TOP LEVEL:")
    for key, value in frontend_contract.items():
        print(
            f"{key!r} -> "
            f"type={type(value).__name__}, "
            f"value={repr(value)[:500]}"
        )

    for key in (
        "status",
        "block_id",
        "engine_version",
        "pipeline",
        "risk",
        "governance",
        "intent",
        "execution",
        "reconciliation",
        "lineage",
        "safety",
    ):
        print()
        print(f"FIELD [{key}]")
        print("-" * 50)
        pprint(frontend_contract.get(key))

print()
print("=" * 70)
print("10. TEST BLOCK 102 OUTPUT AGAINST BLOCK 103")
print("=" * 70)

print("BLOCK 102 OUTPUT BLOCK_ID:")
print(repr(frontend_contract.get("block_id")))

print()
print("BLOCK 103 EXPECTED BLOCK_ID:")
print(repr(getattr(b103, "BLOCK_ID", None)))

print()
print("BLOCK 103 REQUIRED BLOCKS:")
print(repr(getattr(b103, "REQUIRED_BLOCKS", None)))

print()
print("BLOCK 103 SOURCE VALIDATION:")
try:
    validate_source = getattr(b103, "_validate_source", None)

    if validate_source is not None:
        validate_source(frontend_contract)
        print("BLOCK 103 ACCEPTS BLOCK 102 OUTPUT : YES")
    else:
        print("_validate_source not available")

except Exception as exc:
    print("BLOCK 103 ACCEPTS BLOCK 102 OUTPUT : NO")
    print("ERROR TYPE:", type(exc).__name__)
    print("ERROR:", str(exc))

print()
print("=" * 70)
print("11. IDENTIFY EXPECTED BLOCK 103 SOURCE CONTRACT")
print("=" * 70)

print("Inspecting BLOCK 103 source for exact validation rules...")

try:
    source_file = inspect.getsource(ErosBlock103InstitutionalFrontendReadModel)
    print(source_file)
except Exception as exc:
    print("SOURCE EXTRACTION ERROR:", repr(exc))

print()
print("=" * 70)
print("12. BLOCK 104 SIGNATURE")
print("=" * 70)

b104 = EROSBlock104CommandCenter()

print("BLOCK 104 CLASS:", type(b104))
print("BLOCK 104 BLOCK_ID:", getattr(b104, "BLOCK_ID", None))
print("BLOCK 104 SNAPSHOT:", inspect.signature(b104.snapshot))

print()
print("=" * 70)
print("13. BLOCK 106 SIGNATURE")
print("=" * 70)

b106 = EROSBlock106InstitutionalIntegrationBoundary()

print("BLOCK 106 CLASS:", type(b106))
print("BLOCK 106 BLOCK_ID:", getattr(b106, "BLOCK_ID", None))
print(
    "BLOCK 106 BUILD:",
    inspect.signature(b106.build_integration_payload)
)
print(
    "BLOCK 106 SNAPSHOT:",
    inspect.signature(b106.build_read_only_snapshot)
)
print(
    "BLOCK 106 VALIDATE:",
    inspect.signature(b106.validate_payload)
)

print()
print("=" * 70)
print("14. DIAGNOSTIC CONCLUSION")
print("=" * 70)

print("""
The purpose of this test is to determine the exact contract mismatch
between Block 102 and Block 103.

NO SOURCE FILE IS MODIFIED.
NO BROKER IS TOUCHED.
NO ORDER IS CREATED.
NO LIVE EXECUTION OCCURS.
NO GIT COMMIT OCCURS.
NO GIT PUSH OCCURS.
""")

print()
print("=" * 70)
print("BLOCK 102 -> BLOCK 103 CONTRACT INSPECTION COMPLETE")
print("=" * 70)
