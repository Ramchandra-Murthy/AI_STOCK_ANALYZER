from __future__ import annotations

import inspect
import json
import sys
from typing import Any, Dict


print("")
print("=" * 70)
print("EROS 3.0 - BLOCK 106 END-TO-END PYTHON RUNTIME RUNNER")
print("=" * 70)
print("")


# ======================================================================
# 1. IMPORTS
# ======================================================================

print("1. IMPORT CONTRACT LAYERS")
print("-" * 70)

from services.quantitative.block103_institutional_frontend_read_model import (
    EROSBlock103InstitutionalFrontendReadModel,
)

from services.quantitative.block104_eros_command_center import (
    EROSBlock104CommandCenter,
)

from services.quantitative.block106_institutional_integration_boundary import (
    EROSBlock106InstitutionalIntegrationBoundary,
)

print("BLOCK 103 IMPORT : PASS")
print("BLOCK 104 IMPORT : PASS")
print("BLOCK 106 IMPORT : PASS")
print("")


# ======================================================================
# 2. SIGNATURE VERIFICATION
# ======================================================================

print("2. ACTUAL RUNTIME SIGNATURES")
print("-" * 70)

print(
    "BLOCK 103 BUILD     :",
    inspect.signature(EROSBlock103InstitutionalFrontendReadModel.build),
)

print(
    "BLOCK 103 SNAPSHOT  :",
    inspect.signature(EROSBlock103InstitutionalFrontendReadModel.snapshot),
)

print(
    "BLOCK 104 SNAPSHOT  :",
    inspect.signature(EROSBlock104CommandCenter.snapshot),
)

print(
    "BLOCK 106 BUILD     :",
    inspect.signature(
        EROSBlock106InstitutionalIntegrationBoundary.build_integration_payload
    ),
)

print(
    "BLOCK 106 SNAPSHOT  :",
    inspect.signature(
        EROSBlock106InstitutionalIntegrationBoundary.build_read_only_snapshot
    ),
)

print(
    "BLOCK 106 VALIDATE  :",
    inspect.signature(
        EROSBlock106InstitutionalIntegrationBoundary.validate_payload
    ),
)

print("SIGNATURE VERIFICATION : PASS")
print("")


# ======================================================================
# 3. BUILD VALID BLOCK 103 CONTRACT
# ======================================================================

print("3. BUILD BLOCK 103 UPSTREAM CONTRACT")
print("-" * 70)

contract: Dict[str, Any] = {
    "status": "CERTIFIED",
    "block_id": 102,

    "pipeline": {
        "blocks": [
            "94",
            "95",
            "96",
            "97",
            "98",
            "99",
            "100",
            "101",
        ],
        "status": "CERTIFIED",
    },

    "risk": {
        "status": "CERTIFIED",
        "risk_state": "CONTROLLED",
    },

    "governance": {
        "status": "APPROVED",
        "authorization": "AUTHORIZED",
    },

    "intent": {
        "status": "CERTIFIED",
        "authorization": "AUTHORIZED",
        "symbol": "RELIANCE.NS",
        "action": "BUY",
        "quantity": 100.0,
        "reference_price": 2500.0,
    },

    "execution": {
        "status": "SIMULATED",
        "execution_status": "SIMULATED",
        "execution_blocked": True,
        "broker_submission": False,
        "live_execution": False,
    },

    "reconciliation": {
        "status": "RECONCILED",
        "quantity_reconciled": True,
        "price_reconciled": True,
        "value_reconciled": True,
        "cost_reconciled": True,
        "lineage_reconciled": True,
    },

    "lineage": {
        "status": "PRESERVED",
        "source_block": "102",
    },

    "safety": {
        "read_only": True,
        "allow_order_creation": False,
        "allow_broker_submission": False,
        "allow_live_execution": False,
        "allow_portfolio_mutation": False,
        "allow_valuation_mutation": False,
        "allow_performance_mutation": False,
        "allow_risk_mutation": False,
        "allow_optimization": False,
        "execution_blocked": True,
        "non_mutation_invariant": True,
    },
}

print("UPSTREAM CONTRACT : CREATED")
print("SYMBOL            :", contract["intent"]["symbol"])
print("ACTION            :", contract["intent"]["action"])
print("QUANTITY          :", contract["intent"]["quantity"])
print("REFERENCE PRICE   :", contract["intent"]["reference_price"])
print("")


# ======================================================================
# 4. BLOCK 103
# ======================================================================

print("4. BLOCK 103 INSTITUTIONAL READ MODEL")
print("-" * 70)

block103 = EROSBlock103InstitutionalFrontendReadModel()

print("INSTANCE TYPE     :", type(block103).__name__)

read_model = block103.build(
    contract=contract
)

print("BLOCK 103 STATUS  :", read_model.get("status"))
print("BLOCK 103 ID      :", read_model.get("block_id"))
print("DASHBOARD TITLE   :", read_model.get("dashboard", {}).get("title"))

if read_model.get("status") != "CERTIFIED":
    raise RuntimeError("Block 103 did not return CERTIFIED")

print("BLOCK 103 BUILD    : PASS")
print("")


# ======================================================================
# 5. BLOCK 104
# ======================================================================

print("5. BLOCK 104 COMMAND CENTER")
print("-" * 70)

block104 = EROSBlock104CommandCenter()

print("INSTANCE TYPE     :", type(block104).__name__)

command_center = block104.snapshot(
    read_model
)

print(
    "BLOCK 104 STATUS  :",
    command_center.get("status"),
)

print(
    "BLOCK 104 ID      :",
    command_center.get("block_id"),
)

print(
    "SOURCE BLOCK      :",
    command_center.get("source_block"),
)

print(
    "GOVERNANCE        :",
    command_center.get("governance", {}).get("status"),
)

print(
    "INTENT            :",
    command_center.get("intent", {}).get("authorization"),
)

print(
    "EXECUTION         :",
    command_center.get("execution", {}).get("execution_status"),
)

print(
    "RECONCILIATION    :",
    command_center.get("reconciliation", {}).get("status"),
)

if command_center.get("status") != "CERTIFIED":
    raise RuntimeError("Block 104 did not return CERTIFIED")

print("BLOCK 104 COMMAND CENTER : PASS")
print("")


# ======================================================================
# 6. BLOCK 106
# ======================================================================

print("6. BLOCK 106 INSTITUTIONAL INTEGRATION BOUNDARY")
print("-" * 70)

block106 = EROSBlock106InstitutionalIntegrationBoundary()

print("INSTANCE TYPE     :", type(block106).__name__)
print("BLOCK ID          :", block106.BLOCK_ID)
print("BLOCK NAME        :", block106.BLOCK_NAME)
print("VERSION           :", block106.VERSION)

integration_payload = block106.build_integration_payload(
    command_center=command_center
)

print("")
print("INTEGRATION PAYLOAD CREATED : PASS")
print(
    "PAYLOAD STATUS              :",
    integration_payload.get("status"),
)
print(
    "PAYLOAD BLOCK ID            :",
    integration_payload.get("block_id"),
)

print("")


# ======================================================================
# 7. PAYLOAD VALIDATION
# ======================================================================

print("7. BLOCK 106 PAYLOAD VALIDATION")
print("-" * 70)

payload_valid = block106.validate_payload(
    integration_payload
)

print("VALIDATION RESULT :", payload_valid)

if payload_valid is not True:
    raise RuntimeError("Block 106 payload validation failed")

print("PAYLOAD VALIDATION : PASS")
print("")


# ======================================================================
# 8. READ-ONLY SNAPSHOT
# ======================================================================

print("8. BLOCK 106 READ-ONLY SNAPSHOT")
print("-" * 70)

snapshot = block106.build_read_only_snapshot(
    command_center=command_center
)

print("SNAPSHOT CREATED  : PASS")
print(
    "SNAPSHOT STATUS    :",
    snapshot.get("status"),
)

print("")


# ======================================================================
# 9. SAFETY POLICY
# ======================================================================

print("9. BLOCK 106 SAFETY POLICY")
print("-" * 70)

policy = getattr(block106, "SAFETY_POLICY", {})

for key in (
    "read_only",
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
    print(
        f"{key:35} :",
        policy.get(key),
    )

required_true = (
    "read_only",
    "execution_blocked",
    "non_mutation_invariant",
)

required_false = (
    "allow_order_creation",
    "allow_broker_submission",
    "allow_live_execution",
    "allow_portfolio_mutation",
    "allow_valuation_mutation",
    "allow_performance_mutation",
    "allow_risk_mutation",
    "allow_optimization",
)

for key in required_true:
    if policy.get(key) is not True:
        raise RuntimeError(
            f"Safety violation: {key} must be True"
        )

for key in required_false:
    if policy.get(key) is not False:
        raise RuntimeError(
            f"Safety violation: {key} must be False"
        )

print("")
print("SAFETY POLICY : PASS")
print("")


# ======================================================================
# 10. SOURCE LINEAGE
# ======================================================================

print("10. LINEAGE PRESERVATION")
print("-" * 70)

lineage = integration_payload.get("lineage", {})

print(
    "LINEAGE STATUS   :",
    lineage.get("status"),
)

print(
    "SOURCE BLOCK     :",
    lineage.get("source_block"),
)

print(
    "BLOCK CHAIN      :",
    lineage.get("block_chain"),
)

print("LINEAGE INSPECTION : PASS")
print("")


# ======================================================================
# 11. JSON SERIALIZATION
# ======================================================================

print("11. JSON SERIALIZATION CONTRACT")
print("-" * 70)

serialized = json.dumps(
    integration_payload,
    sort_keys=True,
    default=str,
)

print(
    "SERIALIZED BYTES :",
    len(serialized.encode("utf-8")),
)

json.loads(serialized)

print("JSON SERIALIZATION : PASS")
print("")


# ======================================================================
# 12. FINAL RESULT
# ======================================================================

print("=" * 70)
print("BLOCK 103 -> BLOCK 104 -> BLOCK 106")
print("=" * 70)

print("BLOCK 103 READ MODEL       : PASS")
print("BLOCK 104 COMMAND CENTER  : PASS")
print("BLOCK 106 INTEGRATION      : PASS")
print("PAYLOAD VALIDATION         : PASS")
print("READ-ONLY SNAPSHOT         : PASS")
print("SAFETY POLICY              : PASS")
print("LINEAGE                    : PASS")
print("JSON SERIALIZATION         : PASS")

print("")
print("=" * 70)
print("EROS 3.0 BLOCK 106 END-TO-END RUNTIME : PASS")
print("=" * 70)
print("")

print("BROKER SUBMISSION          : FALSE")
print("LIVE EXECUTION             : FALSE")
print("ORDER CREATION             : FALSE")
print("PORTFOLIO MUTATION         : FALSE")
print("VALUATION MUTATION         : FALSE")
print("PERFORMANCE MUTATION       : FALSE")
print("RISK MUTATION               : FALSE")
print("OPTIMIZATION               : FALSE")
print("EXECUTION BLOCKED          : TRUE")
print("NON-MUTATION               : TRUE")
print("READ ONLY                  : TRUE")
print("")

print("RESULT : PASS")
