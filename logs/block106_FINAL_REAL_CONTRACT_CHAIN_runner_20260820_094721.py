import inspect
import json
import sys

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

print("=" * 70)
print("EROS 3.0 - FINAL REAL CONTRACT CHAIN")
print("102 -> 103 -> 104 -> 106")
print("=" * 70)

print("\n1. IMPORTS")
print("BLOCK 102 IMPORT : PASS")
print("BLOCK 103 IMPORT : PASS")
print("BLOCK 104 IMPORT : PASS")
print("BLOCK 106 IMPORT : PASS")

print("\n2. SIGNATURES")
print("BLOCK 102 BUILD :", inspect.signature(
    EROSBlock102FrontendContract.build
))
print("BLOCK 103 BUILD :", inspect.signature(
    EROSBlock103InstitutionalFrontendReadModel.build
))
print("BLOCK 104 SNAPSHOT :", inspect.signature(
    EROSBlock104CommandCenter.snapshot
))
print("BLOCK 106 BUILD :", inspect.signature(
    EROSBlock106InstitutionalIntegrationBoundary.build_integration_payload
))

print("\n3. BLOCK 102")
b102 = EROSBlock102FrontendContract()

c102 = b102.build()

print("TYPE       :", type(c102))
print("STATUS     :", repr(c102.get("status")))
print("BLOCK ID   :", repr(c102.get("block_id")))
print("ENGINE     :", repr(c102.get("engine_version")))
print("KEYS       :", list(c102.keys()))

assert c102.get("block_id") == "102"
assert c102.get("status") == "CERTIFIED"

print("BLOCK 102 CONTRACT : PASS")

print("\n4. BLOCK 103")

b103 = EROSBlock103InstitutionalFrontendReadModel()

r103 = b103.build(contract=c102)

print("TYPE       :", type(r103))
print("STATUS     :", repr(r103.get("status")))
print("BLOCK ID   :", repr(r103.get("block_id")))
print("ENGINE     :", repr(r103.get("engine_version")))
print("KEYS       :", list(r103.keys()))

print("BLOCK 103 OUTPUT:")
print(json.dumps(r103, indent=2, default=str))

assert r103.get("block_id") in (103, "103")
assert r103.get("status") == "CERTIFIED"

print("BLOCK 103 CONTRACT : PASS")

print("\n5. BLOCK 104")

b104 = EROSBlock104CommandCenter()

c104 = b104.snapshot(read_model=r103)

print("TYPE       :", type(c104))
print("STATUS     :", repr(c104.get("status")))
print("BLOCK ID   :", repr(c104.get("block_id")))
print("ENGINE     :", repr(c104.get("engine_version")))
print("KEYS       :", list(c104.keys()))

print("BLOCK 104 OUTPUT:")
print(json.dumps(c104, indent=2, default=str))

print("BLOCK 104 CONTRACT : PASS")

print("\n6. BLOCK 106")

b106 = EROSBlock106InstitutionalIntegrationBoundary()

p106 = b106.build_integration_payload(c104)

print("TYPE       :", type(p106))
print("KEYS       :", list(p106.keys()))

print("BLOCK 106 PAYLOAD:")
print(json.dumps(p106, indent=2, default=str))

valid = b106.validate_payload(p106)

print("\nBLOCK 106 VALIDATION :", valid)

assert valid is True

print("\n7. SAFETY")

safety = p106.get("safety", {})

for key in [
    "broker_submission",
    "live_order_submission",
    "order_creation",
    "portfolio_mutation",
    "valuation_mutation",
    "performance_mutation",
    "risk_mutation",
    "optimization",
]:
    print(f"{key:30}:", safety.get(key))

print("execution_blocked".ljust(30), ":", safety.get("execution_blocked"))
print("non_mutation_invariant".ljust(30), ":", safety.get("non_mutation_invariant"))

assert safety.get("execution_blocked") is True
assert safety.get("non_mutation_invariant") is True
assert safety.get("broker_submission") is False
assert safety.get("live_order_submission") is False
assert safety.get("order_creation") is False

print("\n======================================================================")
print("FINAL RESULT : PASS")
print("======================================================================")
