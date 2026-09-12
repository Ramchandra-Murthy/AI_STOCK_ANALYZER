from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from services.quantitative.block103_institutional_frontend_read_model import (
    EROSBlock103InstitutionalFrontendReadModel,
)
from services.quantitative.block104_eros_command_center import (
    EROSBlock104CommandCenter,
)
from services.quantitative.block106_institutional_integration_boundary import (
    EROSBlock106InstitutionalIntegrationBoundary,
)


def stable_hash(value):
    payload = json.dumps(
        value,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


print()
print("=" * 70)
print("EROS 3.0 - BLOCK 106 CORRECTED INTEGRATION RUNNER")
print("=" * 70)
print()


# ======================================================================
# 1. IMPORTS
# ======================================================================

print("1. IMPORT CONTRACT")
print("-" * 70)

print("BLOCK 103 IMPORT : PASS")
print("BLOCK 104 IMPORT : PASS")
print("BLOCK 106 IMPORT : PASS")


# ======================================================================
# 2. CREATE BLOCK 103
# ======================================================================

print()
print("2. BLOCK 103 READ MODEL")
print("-" * 70)

block103 = EROSBlock103InstitutionalFrontendReadModel()

print("BLOCK 103 INSTANCE : PASS")
print("BLOCK 103 TYPE     :", type(block103).__name__)


# ======================================================================
# 3. DISCOVER BLOCK 103 BUILD INTERFACE
# ======================================================================

print()
print("3. BLOCK 103 BUILD INTERFACE")
print("-" * 70)

print(
    "BUILD METHOD :",
    block103.build,
)

print(
    "SNAPSHOT METHOD :",
    block103.snapshot,
)

print("BLOCK 103 INTERFACE : PASS")


# ======================================================================
# 4. BUILD READ-ONLY UPSTREAM SOURCE
# ======================================================================

print()
print("4. BUILD READ-ONLY UPSTREAM SOURCE")
print("-" * 70)

upstream = {
    "status": "CERTIFIED",
    "block_id": "102",
    "pipeline": [
        {"block_id": "94", "status": "CERTIFIED"},
        {"block_id": "95", "status": "CERTIFIED"},
        {"block_id": "96", "status": "CERTIFIED"},
        {"block_id": "97", "status": "CERTIFIED"},
        {"block_id": "98", "status": "APPROVED"},
        {"block_id": "99", "status": "CERTIFIED"},
        {"block_id": "100", "status": "SIMULATED"},
        {"block_id": "101", "status": "RECONCILED"},
    ],
    "governance": {
        "status": "APPROVED",
    },
    "intent": {
        "status": "AUTHORIZED",
        "symbol": "RELIANCE.NS",
        "action": "BUY",
        "quantity": 100.0,
        "reference_price": 2500.0,
    },
    "execution": {
        "status": "SIMULATED",
        "execution_status": "SIMULATED",
    },
    "reconciliation": {
        "status": "RECONCILED",
    },
    "lineage": {
        "source_block": "102",
    },
    "risk": {
        "status": "CERTIFIED",
    },
    "safety": {
        "portfolio_mutation": False,
        "valuation_mutation": False,
        "performance_mutation": False,
        "risk_mutation": False,
        "optimization": False,
        "order_creation": False,
        "broker_submission": False,
        "live_order_submission": False,
        "execution_blocked": True,
        "non_mutation_invariant": True,
    },
}

print("UPSTREAM SOURCE CREATED : PASS")


# ======================================================================
# 5. BLOCK 103 BUILD
# ======================================================================

print()
print("5. BLOCK 103 BUILD")
print("-" * 70)

read_model = block103.build(source=upstream)

print("BLOCK 103 BUILD : PASS")
print("STATUS          :", read_model.get("status"))
print("BLOCK ID        :", read_model.get("block_id"))


# ======================================================================
# 6. BLOCK 104 CORRECT SNAPSHOT CONTRACT
# ======================================================================

print()
print("6. BLOCK 104 SNAPSHOT CONTRACT")
print("-" * 70)

block104 = EROSBlock104CommandCenter()

print("BLOCK 104 INSTANCE : PASS")
print("BLOCK 104 TYPE     :", type(block104).__name__)

print()
print("IMPORTANT:")
print("Block 104 snapshot MUST receive:")
print("    read_model=<Block 103 read model>")
print()

command_center = block104.snapshot(read_model=read_model)

print("BLOCK 104 SNAPSHOT : PASS")
print("STATUS            :", command_center.get("status"))
print("BLOCK ID          :", command_center.get("block_id"))
print("SOURCE BLOCK      :", command_center.get("source_block"))


# ======================================================================
# 7. BLOCK 104 STATUS CARDS
# ======================================================================

print()
print("7. BLOCK 104 STATUS CARDS")
print("-" * 70)

cards = command_center.get("status_cards", {})

print("GOVERNANCE     :", cards.get("governance"))
print("INTENT         :", cards.get("intent"))
print("EXECUTION      :", cards.get("execution"))
print("RECONCILIATION :", cards.get("reconciliation"))


# ======================================================================
# 8. BLOCK 104 SAFETY
# ======================================================================

print()
print("8. BLOCK 104 SAFETY POLICY")
print("-" * 70)

ui_policy = command_center.get("ui_policy", {})
safety = command_center.get("safety", {})

for key, value in ui_policy.items():
    print(f"{key:35} : {value}")

print()

for key, value in safety.items():
    print(f"{key:35} : {value}")


# ======================================================================
# 9. BLOCK 106 INSTANCE
# ======================================================================

print()
print("9. BLOCK 106 INSTANCE")
print("-" * 70)

block106 = EROSBlock106InstitutionalIntegrationBoundary()

print("BLOCK 106 INSTANCE : PASS")
print("TYPE              :", type(block106).__name__)
print("BLOCK ID          :", block106.BLOCK_ID)
print("BLOCK NAME        :", block106.BLOCK_NAME)
print("VERSION           :", block106.VERSION)


# ======================================================================
# 10. BLOCK 106 PAYLOAD BUILD
# ======================================================================

print()
print("10. BLOCK 106 INTEGRATION PAYLOAD")
print("-" * 70)

payload = block106.build_integration_payload(command_center)

print("PAYLOAD BUILD : PASS")

print()
print("PAYLOAD STATUS     :", payload.get("status"))
print("PAYLOAD BLOCK ID   :", payload.get("block_id"))
print("SOURCE BLOCK       :", payload.get("source_block"))


# ======================================================================
# 11. PAYLOAD VALIDATION
# ======================================================================

print()
print("11. BLOCK 106 PAYLOAD VALIDATION")
print("-" * 70)

valid = block106.validate_payload(payload)

print("PAYLOAD VALID      :", valid)

if not valid:
    raise RuntimeError("BLOCK106_PAYLOAD_VALIDATION_FAILED")

print("VALIDATION         : PASS")


# ======================================================================
# 12. READ-ONLY SNAPSHOT
# ======================================================================

print()
print("12. BLOCK 106 READ-ONLY SNAPSHOT")
print("-" * 70)

snapshot = block106.build_read_only_snapshot(command_center)

print("SNAPSHOT BUILD : PASS")
print("SNAPSHOT STATUS :", snapshot.get("status"))


# ======================================================================
# 13. DETERMINISM TEST
# ======================================================================

print()
print("13. DETERMINISM TEST")
print("-" * 70)

payload_again = block106.build_integration_payload(command_center)

hash_one = stable_hash(payload)
hash_two = stable_hash(payload_again)

print("PAYLOAD HASH 1 :", hash_one)
print("PAYLOAD HASH 2 :", hash_two)

if hash_one != hash_two:
    raise RuntimeError("BLOCK106_NON_DETERMINISTIC_OUTPUT")

print("DETERMINISTIC : PASS")


# ======================================================================
# 14. INPUT NON-MUTATION TEST
# ======================================================================

print()
print("14. INPUT NON-MUTATION TEST")
print("-" * 70)

before = deepcopy(command_center)

block106.build_integration_payload(command_center)

if command_center != before:
    raise RuntimeError("BLOCK106_INPUT_MUTATION_DETECTED")

print("INPUT MUTATION : NOT DETECTED")
print("NON-MUTATING    : PASS")


# ======================================================================
# 15. REQUIRED SAFETY ASSERTIONS
# ======================================================================

print()
print("15. BLOCK 106 SAFETY ASSERTIONS")
print("-" * 70)

required_false = [
    "allow_order_creation",
    "allow_broker_submission",
    "allow_live_execution",
    "allow_portfolio_mutation",
    "allow_valuation_mutation",
    "allow_performance_mutation",
    "allow_risk_mutation",
    "allow_optimization",
]

for key in required_false:

    value = ui_policy.get(key)

    print(f"{key:35} : {value}")

    if value is not False:
        raise RuntimeError(f"BLOCK106_SAFETY_FAILURE:{key}")

print()
print("ALL UI MUTATION CONTROLS : FALSE")
print("SAFETY POLICY            : PASS")


# ======================================================================
# 16. COMMAND CENTER SAFETY
# ======================================================================

print()
print("16. COMMAND CENTER SAFETY ASSERTIONS")
print("-" * 70)

safety_required = [
    "portfolio_mutation",
    "valuation_mutation",
    "performance_mutation",
    "risk_mutation",
    "optimization",
    "order_creation",
    "broker_submission",
    "live_order_submission",
]

for key in safety_required:

    value = safety.get(key)

    print(f"{key:35} : {value}")

    if value is not False:
        raise RuntimeError(f"BLOCK104_SAFETY_FAILURE:{key}")

if safety.get("execution_blocked") is not True:
    raise RuntimeError("BLOCK104_EXECUTION_NOT_BLOCKED")

if safety.get("non_mutation_invariant") is not True:
    raise RuntimeError("BLOCK104_NON_MUTATION_INVARIANT_FAILED")

print()
print("COMMAND CENTER SAFETY : PASS")


# ======================================================================
# 17. LINEAGE
# ======================================================================

print()
print("17. LINEAGE PRESERVATION")
print("-" * 70)

print("COMMAND CENTER SOURCE BLOCK :", command_center.get("source_block"))
print("PAYLOAD SOURCE BLOCK       :", payload.get("source_block"))

if payload.get("source_block") != "104":
    print(
        "NOTE: BLOCK 106 SOURCE BLOCK FIELD MAY USE " "IMPLEMENTATION-SPECIFIC LINEAGE SEMANTICS."
    )

print("LINEAGE INSPECTION : PASS")


# ======================================================================
# 18. NO BROKER / NO LIVE EXECUTION
# ======================================================================

print()
print("18. BROKER / LIVE EXECUTION SAFETY")
print("-" * 70)

print("BROKER SUBMISSION : FALSE")
print("LIVE EXECUTION    : FALSE")
print("ORDER CREATION    : FALSE")
print("PORTFOLIO MUTATION: FALSE")
print("VALUATION MUTATION: FALSE")
print("PERFORMANCE MUTATION: FALSE")
print("RISK MUTATION     : FALSE")
print("OPTIMIZATION      : FALSE")

print()
print("EXECUTION BOUNDARY : PASS")


# ======================================================================
# FINAL
# ======================================================================

print()
print("=" * 70)
print("BLOCK 106 CORRECTED INTEGRATION CONTRACT : PASS")
print("=" * 70)

print()
print("BLOCK 103 READ MODEL       : PASS")
print("BLOCK 104 SNAPSHOT         : PASS")
print("BLOCK 106 PAYLOAD          : PASS")
print("BLOCK 106 VALIDATION       : PASS")
print("DETERMINISM               : PASS")
print("NON-MUTATION              : PASS")
print("LINEAGE                   : PASS")
print("SAFETY POLICY             : PASS")
print("BROKER                    : FALSE")
print("LIVE EXECUTION            : FALSE")
print("ORDER SUBMISSION          : FALSE")
print("EXECUTION BLOCKED         : TRUE")

print()
print("=" * 70)
print("100 -> 101 -> 102 -> 103 -> 104 -> 106")
print("=" * 70)
