from __future__ import annotations

import inspect
import py_compile

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


def require(condition, message):
    if not condition:
        raise AssertionError(message)


print("=" * 70)
print("EROS 3.0 - BLOCK 106 FINAL REAL CONTRACT CHAIN")
print("102 -> 103 -> 104 -> 106")
print("=" * 70)

print("\n1. IMPORTS")
print("-" * 70)
print("BLOCK 102 IMPORT : PASS")
print("BLOCK 103 IMPORT : PASS")
print("BLOCK 104 IMPORT : PASS")
print("BLOCK 106 IMPORT : PASS")

print("\n2. ACTUAL INTERFACES")
print("-" * 70)

print("BLOCK 102 BUILD :", inspect.signature(EROSBlock102FrontendContract.build))

print("BLOCK 103 BUILD :", inspect.signature(EROSBlock103InstitutionalFrontendReadModel.build))

print("BLOCK 104 SNAPSHOT :", inspect.signature(EROSBlock104CommandCenter.snapshot))

print("BLOCK 106 BUILD :", inspect.signature(EROSBlock106InstitutionalIntegrationBoundary.build))

print(
    "BLOCK 106 VALIDATE :",
    inspect.signature(EROSBlock106InstitutionalIntegrationBoundary.validate_payload),
)

print("INTERFACE CHECK : PASS")


print("\n3. BLOCK 102")
print("-" * 70)

b102 = EROSBlock102FrontendContract()

c102 = b102.build()

print("TYPE       :", type(c102))
print("STATUS     :", repr(c102.get("status")))
print("BLOCK ID   :", repr(c102.get("block_id")))
print("ENGINE     :", repr(c102.get("engine_version")))
print("KEYS       :", list(c102.keys()))

require(isinstance(c102, dict), "BLOCK102_NOT_DICT")
require(c102.get("block_id") == "102", "BLOCK102_BAD_ID")
require(c102.get("status") == "CERTIFIED", "BLOCK102_BAD_STATUS")
require(c102.get("engine_version") == "EROS-3.0-BLOCK-102", "BLOCK102_BAD_ENGINE")

print("BLOCK 102 CONTRACT : PASS")


print("\n4. BLOCK 103")
print("-" * 70)

b103 = EROSBlock103InstitutionalFrontendReadModel()

c103 = b103.build(contract=c102)

print("TYPE       :", type(c103))
print("STATUS     :", repr(c103.get("status")))
print("BLOCK ID   :", repr(c103.get("block_id")))
print("ENGINE     :", repr(c103.get("engine_version")))
print("KEYS       :", list(c103.keys()))

require(isinstance(c103, dict), "BLOCK103_NOT_DICT")
require(c103.get("block_id") == "103", "BLOCK103_BAD_ID")
require(c103.get("status") == "CERTIFIED", "BLOCK103_BAD_STATUS")
require(c103.get("engine_version") == "EROS-3.0-BLOCK-103", "BLOCK103_BAD_ENGINE")

print("BLOCK 103 CONTRACT : PASS")


print("\n5. BLOCK 104")
print("-" * 70)

b104 = EROSBlock104CommandCenter()

c104 = b104.snapshot(read_model=c103)

print("TYPE        :", type(c104))
print("STATUS      :", repr(c104.get("status")))
print("BLOCK ID    :", repr(c104.get("block_id")))
print("ENGINE      :", repr(c104.get("engine_version")))
print("SOURCE BLOCK:", repr(c104.get("source_block")))
print("KEYS        :", list(c104.keys()))

require(isinstance(c104, dict), "BLOCK104_NOT_DICT")
require(c104.get("block_id") == "104", "BLOCK104_BAD_ID")
require(c104.get("status") == "CERTIFIED", "BLOCK104_BAD_STATUS")
require(c104.get("engine_version") == "EROS-3.0-BLOCK-104", "BLOCK104_BAD_ENGINE")
require(c104.get("source_block") == "103", "BLOCK104_BAD_SOURCE")

print("BLOCK 104 CONTRACT : PASS")


print("\n6. BLOCK 106")
print("-" * 70)

b106 = EROSBlock106InstitutionalIntegrationBoundary()

c106 = b106.build(c104)

print("TYPE       :", type(c106))
print("TOP KEYS   :", list(c106.keys()))

require(isinstance(c106, dict), "BLOCK106_NOT_DICT")

print("\nBLOCK 106 STRUCTURE")
print("-" * 70)

for key in (
    "schema",
    "integration",
    "command_center",
    "safety",
    "lineage",
    "integrity",
):
    print(f"{key:20}:", "PRESENT" if key in c106 else "MISSING")

require("schema" in c106, "BLOCK106_SCHEMA_MISSING")
require("integration" in c106, "BLOCK106_INTEGRATION_MISSING")
require("command_center" in c106, "BLOCK106_COMMAND_CENTER_MISSING")
require("safety" in c106, "BLOCK106_SAFETY_MISSING")
require("lineage" in c106, "BLOCK106_LINEAGE_MISSING")
require("integrity" in c106, "BLOCK106_INTEGRITY_MISSING")


print("\n7. BLOCK 106 VALIDATION")
print("-" * 70)

valid = b106.validate_payload(c106)

print("VALIDATE RESULT :", valid)

require(valid is True, "BLOCK106_VALIDATION_FAILED")

print("BLOCK 106 VALIDATION : PASS")


print("\n8. SAFETY VERIFICATION")
print("-" * 70)

safety = c106.get("safety", {})

for key in (
    "allow_order_creation",
    "allow_broker_submission",
    "allow_live_execution",
    "allow_portfolio_mutation",
    "allow_valuation_mutation",
    "allow_performance_mutation",
    "allow_risk_mutation",
    "allow_optimization",
    "execution_blocked",
    "non_mutation_invariant",
):
    print(f"{key:30}:", safety.get(key))

require(safety.get("allow_order_creation") is False, "ORDER_CREATION_NOT_BLOCKED")

require(safety.get("allow_broker_submission") is False, "BROKER_SUBMISSION_NOT_BLOCKED")

require(safety.get("allow_live_execution") is False, "LIVE_EXECUTION_NOT_BLOCKED")

require(safety.get("execution_blocked") is True, "EXECUTION_NOT_BLOCKED")

require(safety.get("non_mutation_invariant") is True, "NON_MUTATION_INVARIANT_FAILED")

print("SAFETY BOUNDARY : PASS")


print("\n9. SOURCE COMPILE CHECK")
print("-" * 70)

files = [
    r"services\quantitative\block102_frontend_contract.py",
    r"services\quantitative\block103_institutional_frontend_read_model.py",
    r"services\quantitative\block104_eros_command_center.py",
    r"services\quantitative\block106_institutional_integration_boundary.py",
]

for path in files:
    py_compile.compile(path, doraise=True)
    print("COMPILE PASS :", path)


print("\n10. FINAL CONTRACT CHAIN")
print("-" * 70)

print("102 -> 103 : PASS")
print("103 -> 104 : PASS")
print("104 -> 106 : PASS")
print("106 VALIDATION : PASS")
print("SAFETY : PASS")

print("\n" + "=" * 70)
print("BLOCK 106 FINAL REAL CONTRACT CHAIN : PASS")
print("=" * 70)

print("READ ONLY            : TRUE")
print("ORDER CREATION       : FALSE")
print("BROKER SUBMISSION    : FALSE")
print("LIVE EXECUTION       : FALSE")
print("MUTATION             : FALSE")
print("EXECUTION BLOCKED    : TRUE")
print("NON-MUTATION         : TRUE")
print("=" * 70)
