from __future__ import annotations

import inspect
import json

from services.quantitative.block102_frontend_contract import (
    EROSBlock102FrontendContract,
)
from services.quantitative.block103_institutional_frontend_read_model import (
    EROSBlock103InstitutionalFrontendReadModel,
)
from services.quantitative.block104_eros_command_center import (
    EROSBlock104EROSCommandCenter,
)
from services.quantitative.block106_institutional_integration_boundary import (
    EROSBlock106InstitutionalIntegrationBoundary,
)


def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


section("EROS 3.0 - BLOCK 106 ACTUAL OUTPUT STRUCTURE")

print("READ ONLY")
print("NO SOURCE CHANGES")
print("NO COMMIT")
print("NO PUSH")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")

# ------------------------------------------------------------
# 1. BUILD 102
# ------------------------------------------------------------

section("1. BLOCK 102")

b102 = EROSBlock102FrontendContract()

c102 = b102.build()

print("TYPE :", type(c102))
print("TOP LEVEL KEYS :")
for key in c102:
    print(" ", repr(key), "->", type(c102[key]).__name__)

print("\nBLOCK ID :", repr(c102.get("block_id")))
print("STATUS   :", repr(c102.get("status")))
print("ENGINE   :", repr(c102.get("engine_version")))

# ------------------------------------------------------------
# 2. BUILD 103
# ------------------------------------------------------------

section("2. BLOCK 103")

b103 = EROSBlock103InstitutionalFrontendReadModel()

c103 = b103.build(contract=c102)

print("TYPE :", type(c103))
print("BLOCK ID :", repr(c103.get("block_id")))
print("STATUS   :", repr(c103.get("status")))
print("ENGINE   :", repr(c103.get("engine_version")))

# ------------------------------------------------------------
# 3. BUILD 104
# ------------------------------------------------------------

section("3. BLOCK 104")

b104 = EROSBlock104EROSCommandCenter()

c104 = b104.snapshot(read_model=c103)

print("TYPE :", type(c104))
print("BLOCK ID :", repr(c104.get("block_id")))
print("STATUS   :", repr(c104.get("status")))
print("ENGINE :", repr(c104.get("engine_version")))
print("SOURCE BLOCK :", repr(c104.get("source_block")))

# ------------------------------------------------------------
# 4. BUILD 106
# ------------------------------------------------------------

section("4. BLOCK 106")

b106 = EROSBlock106InstitutionalIntegrationBoundary()

print("CLASS :", type(b106))
print("BUILD SIGNATURE :", inspect.signature(b106.build))
print("SNAPSHOT SIGNATURE :", inspect.signature(b106.snapshot))
print("VALIDATE SIGNATURE :", inspect.signature(b106.validate_payload))

c106 = b106.build(c104)

print("\nTYPE :", type(c106))

print("\nTOP LEVEL KEYS:")
for key in c106:
    print(" ", repr(key), "->", type(c106[key]).__name__)

print("\nTOP LEVEL VALUES:")
print(json.dumps(c106, indent=2, default=str))

# ------------------------------------------------------------
# 5. VALIDATION
# ------------------------------------------------------------

section("5. BLOCK 106 VALIDATION")

valid = b106.validate_payload(c106)

print("VALIDATE RESULT :", valid)

# ------------------------------------------------------------
# 6. STRUCTURAL INSPECTION
# ------------------------------------------------------------

section("6. BLOCK 106 STRUCTURAL CONTRACT")

for key in (
    "schema",
    "integration",
    "command_center",
    "safety",
    "lineage",
    "integrity",
):
    value = c106.get(key)

    print("\nFIELD :", key)
    print("TYPE  :", type(value).__name__)

    if isinstance(value, dict):
        print("KEYS  :", list(value.keys()))
    else:
        print("VALUE :", repr(value))

# ------------------------------------------------------------
# 7. SAFETY
# ------------------------------------------------------------

section("7. BLOCK 106 SAFETY")

safety = c106.get("safety")

print(json.dumps(safety, indent=2, default=str))

# ------------------------------------------------------------
# 8. FINAL
# ------------------------------------------------------------

section("FINAL RESULT")

print("BLOCK 102 : BUILT")
print("BLOCK 103 : BUILT")
print("BLOCK 104 : BUILT")
print("BLOCK 106 : BUILT")
print("BLOCK 106 VALIDATION :", valid)

print("\nNO SOURCE CHANGES")
print("NO COMMIT")
print("NO PUSH")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")

if not valid:
    raise AssertionError("BLOCK106_VALIDATION_FAILED")

print("\nBLOCK 106 ACTUAL OUTPUT STRUCTURE : PASS")
