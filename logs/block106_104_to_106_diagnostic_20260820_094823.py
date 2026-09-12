import inspect
import json
import sys
import traceback

sys.path.insert(0, r"D:\Users\User\Desktop\AI_STOCK_ANALYZER")

print("=" * 70)
print("EROS 3.0 - BLOCK 104 -> 106 EXACT FAILURE DIAGNOSTIC")
print("=" * 70)
print("READ ONLY")
print("NO SOURCE CHANGES")
print("NO COMMIT")
print("NO PUSH")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print()

try:
    from services.quantitative.block102_frontend_contract import EROSBlock102FrontendContract
    from services.quantitative.block103_institutional_frontend_read_model import (
        EROSBlock103InstitutionalFrontendReadModel,
    )
    from services.quantitative.block104_eros_command_center import EROSBlock104CommandCenter
    from services.quantitative.block106_institutional_integration_boundary import (
        EROSBlock106InstitutionalIntegrationBoundary,
    )

    print("1. IMPORTS")
    print("-" * 70)
    print("BLOCK 102 IMPORT : PASS")
    print("BLOCK 103 IMPORT : PASS")
    print("BLOCK 104 IMPORT : PASS")
    print("BLOCK 106 IMPORT : PASS")
    print()

    b102 = EROSBlock102FrontendContract()
    b103 = EROSBlock103InstitutionalFrontendReadModel()
    b104 = EROSBlock104CommandCenter()
    b106 = EROSBlock106InstitutionalIntegrationBoundary()

    print("2. SIGNATURES")
    print("-" * 70)
    print("BLOCK 102 BUILD :", inspect.signature(b102.build))
    print("BLOCK 103 BUILD :", inspect.signature(b103.build))
    print("BLOCK 104 SNAPSHOT :", inspect.signature(b104.snapshot))
    print("BLOCK 106 BUILD :", inspect.signature(b106.build_integration_payload))
    print()

    # ----------------------------------------------------------
    # BLOCK 102
    # ----------------------------------------------------------
    print("3. BLOCK 102 ACTUAL OUTPUT")
    print("-" * 70)

    c102 = b102.build()

    print("TYPE :", type(c102))
    print("BLOCK ID :", repr(c102.get("block_id")))
    print("STATUS :", repr(c102.get("status")))
    print("ENGINE :", repr(c102.get("engine_version")))
    print("KEYS :", list(c102.keys()))

    # IMPORTANT: Block 102 uses string IDs.
    if c102.get("block_id") != "102":
        raise AssertionError("BLOCK102_BAD_ID: expected '102', got " + repr(c102.get("block_id")))

    print("BLOCK 102 : PASS")
    print()

    # ----------------------------------------------------------
    # BLOCK 103
    # ----------------------------------------------------------
    print("4. BLOCK 103 ACTUAL OUTPUT")
    print("-" * 70)

    c103 = b103.build(contract=c102)

    print("TYPE :", type(c103))
    print("BLOCK ID :", repr(c103.get("block_id")))
    print("STATUS :", repr(c103.get("status")))
    print("ENGINE :", repr(c103.get("engine_version")))
    print("KEYS :", list(c103.keys()))

    if c103.get("block_id") != "103":
        raise AssertionError("BLOCK103_BAD_ID: expected '103', got " + repr(c103.get("block_id")))

    print("BLOCK 103 : PASS")
    print()

    # ----------------------------------------------------------
    # BLOCK 104
    # ----------------------------------------------------------
    print("5. BLOCK 104 ACTUAL OUTPUT")
    print("-" * 70)

    c104 = b104.snapshot(read_model=c103)

    print("TYPE :", type(c104))
    print("BLOCK ID :", repr(c104.get("block_id")))
    print("STATUS :", repr(c104.get("status")))
    print("ENGINE :", repr(c104.get("engine_version")))
    print("SOURCE BLOCK :", repr(c104.get("source_block")))
    print("KEYS :", list(c104.keys()))

    if c104.get("block_id") != "104":
        raise AssertionError("BLOCK104_BAD_ID: expected '104', got " + repr(c104.get("block_id")))

    if c104.get("source_block") != "103":
        raise AssertionError(
            "BLOCK104_BAD_SOURCE: expected '103', got " + repr(c104.get("source_block"))
        )

    print()
    print("BLOCK 104 OUTPUT JSON")
    print("-" * 70)
    print(json.dumps(c104, indent=2, default=str))

    print()
    print("BLOCK 104 : PASS")
    print()

    # ----------------------------------------------------------
    # BLOCK 106
    # ----------------------------------------------------------
    print("6. BLOCK 106 INPUT INSPECTION")
    print("-" * 70)

    print("INPUT TYPE :", type(c104))
    print("INPUT BLOCK ID :", repr(c104.get("block_id")))
    print("INPUT STATUS :", repr(c104.get("status")))
    print("INPUT KEYS :", list(c104.keys()))

    print()
    print("BLOCK 106 REQUIRED SOURCE FIELDS")
    print("-" * 70)

    for field in b106.REQUIRED_SOURCE_FIELDS:
        print("{:<20} : {}".format(field, "PRESENT" if field in c104 else "MISSING"))

    print()
    print("7. BLOCK 106 BUILD")
    print("-" * 70)

    payload = b106.build_integration_payload(c104)

    print("BLOCK 106 BUILD : PASS")
    print("TYPE :", type(payload))
    print("BLOCK ID :", repr(payload.get("block_id")))
    print("STATUS :", repr(payload.get("status")))
    print("VERSION :", repr(payload.get("version")))
    print("KEYS :", list(payload.keys()))

    print()
    print("8. BLOCK 106 VALIDATION")
    print("-" * 70)

    valid = b106.validate_payload(payload)

    print("VALIDATE RESULT :", repr(valid))

    if valid is not True:
        raise AssertionError("BLOCK106_VALIDATION_FAILED")

    print("BLOCK 106 VALIDATION : PASS")
    print()

    print("=" * 70)
    print("BLOCK 106 104->106 DIAGNOSTIC : PASS")
    print("=" * 70)

except Exception as exc:
    print()
    print("=" * 70)
    print("!!! EXACT PYTHON EXCEPTION !!!")
    print("=" * 70)
    print("EXCEPTION TYPE :", type(exc).__name__)
    print("EXCEPTION       :", str(exc))
    print()
    print("FULL TRACEBACK")
    print("-" * 70)
    traceback.print_exc()
    print()
    print("=" * 70)
    print("BLOCK 104 -> 106 DIAGNOSTIC : FAILED")
    print("=" * 70)
    sys.exit(1)
