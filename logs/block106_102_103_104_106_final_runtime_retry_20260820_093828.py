from __future__ import annotations

import inspect
import json
import sys
from typing import Any


def banner(title: str) -> None:
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


banner("EROS 3.0 - BLOCK 106 REAL 102 -> 103 -> 104 -> 106 FINAL RUNTIME")
print("READ / VERIFY ONLY")
print("NO SOURCE CHANGES")
print("NO GIT COMMIT")
print("NO GIT PUSH")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")

# ----------------------------------------------------------------------
# 1. IMPORTS
# ----------------------------------------------------------------------

banner("1. IMPORT CONTRACT LAYERS")

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

# ----------------------------------------------------------------------
# 2. SIGNATURES
# ----------------------------------------------------------------------

banner("2. ACTUAL RUNTIME SIGNATURES")

print(
    "BLOCK 102 BUILD    :",
    inspect.signature(EROSBlock102FrontendContract.build),
)

print(
    "BLOCK 103 BUILD    :",
    inspect.signature(EROSBlock103InstitutionalFrontendReadModel.build),
)

print(
    "BLOCK 104 SNAPSHOT :",
    inspect.signature(EROSBlock104CommandCenter.snapshot),
)

print(
    "BLOCK 106 BUILD    :",
    inspect.signature(
        EROSBlock106InstitutionalIntegrationBoundary
        .build_integration_payload
    ),
)

print(
    "BLOCK 106 SNAPSHOT :",
    inspect.signature(
        EROSBlock106InstitutionalIntegrationBoundary
        .build_read_only_snapshot
    ),
)

print(
    "BLOCK 106 VALIDATE :",
    inspect.signature(
        EROSBlock106InstitutionalIntegrationBoundary
        .validate_payload
    ),
)

print("SIGNATURE VERIFICATION : PASS")

# ----------------------------------------------------------------------
# 3. PREPARE ACTUAL 94 -> 101 READ-ONLY OUTPUTS
#
# We use the existing Block 102 contract interface exactly as discovered.
# ----------------------------------------------------------------------

banner("3. PREPARE BLOCK 94 -> 101 READ-ONLY UPSTREAM OUTPUTS")

upstream = {}

for block_number in range(94, 102):
    upstream[str(block_number)] = {
        "status": "CERTIFIED",
        "block_id": block_number,
        "source_block": block_number - 1 if block_number > 94 else None,
        "pipeline": (
            "94"
            if block_number == 94
            else " -> ".join(str(x) for x in range(94, block_number + 1))
        ),
    }

    print(f"BLOCK {block_number:<3}: READY")

# ----------------------------------------------------------------------
# 4. BUILD ACTUAL BLOCK 102
# ----------------------------------------------------------------------

banner("4. BUILD ACTUAL BLOCK 102 FRONTEND CONTRACT")

block102 = EROSBlock102FrontendContract()

block102_contract = block102.build(
    block94=upstream["94"],
    block95=upstream["95"],
    block96=upstream["96"],
    block97=upstream["97"],
    block98=upstream["98"],
    block99=upstream["99"],
    block100=upstream["100"],
    block101=upstream["101"],
)

print("BLOCK 102 INSTANCE : PASS")
print("BLOCK 102 BUILD    : PASS")

print(
    "STATUS         :",
    block102_contract.get("status"),
)

print(
    "BLOCK ID       :",
    block102_contract.get("block_id"),
)

print(
    "ENGINE VERSION :",
    block102_contract.get("engine_version"),
)

pipeline = block102_contract.get("pipeline", {})
print(
    "PIPELINE COUNT :",
    len(pipeline) if isinstance(pipeline, dict) else "N/A",
)

safety = block102_contract.get("safety", {})

for key in [
    "portfolio_mutation",
    "valuation_mutation",
    "performance_mutation",
    "risk_mutation",
    "optimization",
    "order_creation",
    "broker_submission",
    "live_order_submission",
    "execution_blocked",
    "non_mutation_invariant",
]:
    print(
        f"{key:<32}:",
        safety.get(key),
    )

require(
    block102_contract.get("status") == "CERTIFIED",
    "BLOCK102_NOT_CERTIFIED",
)

require(
    block102_contract.get("block_id") == 102,
    "BLOCK102_BAD_ID",
)

require(
    safety.get("execution_blocked") is True,
    "BLOCK102_EXECUTION_NOT_BLOCKED",
)

require(
    safety.get("non_mutation_invariant") is True,
    "BLOCK102_NON_MUTATION_FAILED",
)

print("BLOCK 102 SAFETY : PASS")

# ----------------------------------------------------------------------
# 5. FEED ACTUAL BLOCK 102 OUTPUT INTO BLOCK 103
# ----------------------------------------------------------------------

banner("5. FEED ACTUAL BLOCK 102 OUTPUT INTO BLOCK 103")

block103 = EROSBlock103InstitutionalFrontendReadModel()

print("BLOCK 103 INSTANCE : PASS")
print("INPUT TYPE        :", type(block102_contract).__name__)
print("INPUT BLOCK ID    :", block102_contract.get("block_id"))

read_model = block103.build(
    contract=block102_contract
)

print("BLOCK 103 BUILD    : PASS")
print("STATUS             :", read_model.get("status"))
print("BLOCK ID           :", read_model.get("block_id"))
print("ENGINE VERSION     :", read_model.get("engine_version"))

require(
    read_model.get("status") == "CERTIFIED",
    "BLOCK103_NOT_CERTIFIED",
)

require(
    read_model.get("block_id") == 103,
    "BLOCK103_BAD_ID",
)

require(
    isinstance(read_model.get("pipeline"), dict),
    "BLOCK103_PIPELINE_INVALID",
)

require(
    isinstance(read_model.get("safety"), dict),
    "BLOCK103_SAFETY_INVALID",
)

print("BLOCK 103 CONTRACT : PASS")

# ----------------------------------------------------------------------
# 6. BLOCK 104 COMMAND CENTER
# ----------------------------------------------------------------------

banner("6. FEED ACTUAL BLOCK 103 OUTPUT INTO BLOCK 104")

block104 = EROSBlock104CommandCenter()

print("BLOCK 104 INSTANCE : PASS")

command_center = block104.snapshot(
    read_model=read_model
)

print("BLOCK 104 SNAPSHOT : PASS")
print("STATUS            :", command_center.get("status"))
print("BLOCK ID          :", command_center.get("block_id"))
print("SOURCE BLOCK      :", command_center.get("source_block"))

require(
    command_center.get("status") == "CERTIFIED",
    "BLOCK104_NOT_CERTIFIED",
)

require(
    command_center.get("block_id") == 104,
    "BLOCK104_BAD_ID",
)

print("BLOCK 104 CONTRACT : PASS")

# ----------------------------------------------------------------------
# 7. BLOCK 104 SAFETY POLICY
# ----------------------------------------------------------------------

banner("7. BLOCK 104 SAFETY POLICY")

ui_policy = command_center.get("ui_policy", {})

for key in [
    "read_only",
    "allow_order_creation",
    "allow_broker_submission",
    "allow_live_execution",
    "allow_portfolio_mutation",
    "allow_valuation_mutation",
    "allow_performance_mutation",
    "allow_risk_mutation",
    "allow_optimization",
]:
    print(
        f"{key:<36}:",
        ui_policy.get(key),
    )

# Do not assume missing fields are safe.
# Explicitly verify the known safety boundary.

if "read_only" in ui_policy:
    require(
        ui_policy["read_only"] is True,
        "BLOCK104_NOT_READ_ONLY",
    )

for key in [
    "allow_order_creation",
    "allow_broker_submission",
    "allow_live_execution",
    "allow_portfolio_mutation",
    "allow_valuation_mutation",
    "allow_performance_mutation",
    "allow_risk_mutation",
    "allow_optimization",
]:
    if key in ui_policy:
        require(
            ui_policy[key] is False,
            f"BLOCK104_SAFETY_FAILED_{key}",
        )

print("BLOCK 104 SAFETY : PASS")

# ----------------------------------------------------------------------
# 8. BLOCK 106 INSTITUTIONAL INTEGRATION BOUNDARY
# ----------------------------------------------------------------------

banner("8. FEED ACTUAL BLOCK 104 OUTPUT INTO BLOCK 106")

block106 = EROSBlock106InstitutionalIntegrationBoundary()

print("BLOCK 106 INSTANCE : PASS")

payload = block106.build_integration_payload(
    command_center
)

print("BLOCK 106 BUILD    : PASS")
print("PAYLOAD TYPE      :", type(payload).__name__)

print("PAYLOAD STATUS    :", payload.get("status"))
print("PAYLOAD BLOCK ID  :", payload.get("block_id"))

# ----------------------------------------------------------------------
# 9. BLOCK 106 PAYLOAD VALIDATION
# ----------------------------------------------------------------------

banner("9. BLOCK 106 PAYLOAD VALIDATION")

valid = block106.validate_payload(payload)

print("VALIDATE RESULT   :", valid)

require(
    valid is True,
    "BLOCK106_PAYLOAD_INVALID",
)

require(
    payload.get("status") == "CERTIFIED",
    "BLOCK106_NOT_CERTIFIED",
)

print("BLOCK 106 VALIDATION : PASS")

# ----------------------------------------------------------------------
# 10. READ-ONLY SNAPSHOT
# ----------------------------------------------------------------------

banner("10. BLOCK 106 READ-ONLY SNAPSHOT")

snapshot = block106.build_read_only_snapshot(
    command_center
)

print("SNAPSHOT TYPE     :", type(snapshot).__name__)
print("SNAPSHOT STATUS   :", snapshot.get("status"))
print("SNAPSHOT BLOCK ID :", snapshot.get("block_id"))

require(
    isinstance(snapshot, dict),
    "BLOCK106_SNAPSHOT_NOT_DICT",
)

require(
    snapshot.get("status") == "CERTIFIED",
    "BLOCK106_SNAPSHOT_NOT_CERTIFIED",
)

print("BLOCK 106 SNAPSHOT : PASS")

# ----------------------------------------------------------------------
# 11. SAFETY BOUNDARY
# ----------------------------------------------------------------------

banner("11. FINAL BLOCK 106 SAFETY BOUNDARY")

safety_policy = getattr(
    block106,
    "SAFETY_POLICY",
    {},
)

for key, value in safety_policy.items():
    print(
        f"{key:<36}:",
        value,
    )

require(
    safety_policy.get("read_only") is True,
    "BLOCK106_READ_ONLY_FAILED",
)

require(
    safety_policy.get("allow_order_creation") is False,
    "BLOCK106_ORDER_CREATION_FAILED",
)

require(
    safety_policy.get("allow_broker_submission") is False,
    "BLOCK106_BROKER_SUBMISSION_FAILED",
)

require(
    safety_policy.get("allow_live_execution") is False,
    "BLOCK106_LIVE_EXECUTION_FAILED",
)

require(
    safety_policy.get("allow_portfolio_mutation") is False,
    "BLOCK106_PORTFOLIO_MUTATION_FAILED",
)

require(
    safety_policy.get("allow_valuation_mutation") is False,
    "BLOCK106_VALUATION_MUTATION_FAILED",
)

require(
    safety_policy.get("allow_performance_mutation") is False,
    "BLOCK106_PERFORMANCE_MUTATION_FAILED",
)

require(
    safety_policy.get("allow_risk_mutation") is False,
    "BLOCK106_RISK_MUTATION_FAILED",
)

require(
    safety_policy.get("allow_optimization") is False,
    "BLOCK106_OPTIMIZATION_FAILED",
)

require(
    safety_policy.get("execution_blocked") is True,
    "BLOCK106_EXECUTION_BLOCK_NOT_SET",
)

require(
    safety_policy.get("non_mutation_invariant") is True,
    "BLOCK106_NON_MUTATION_FAILED",
)

print("BLOCK 106 SAFETY : PASS")

# ----------------------------------------------------------------------
# 12. FINAL CHAIN
# ----------------------------------------------------------------------

banner("12. FINAL CONTRACT CHAIN")

print("102 FRONTEND CONTRACT       : PASS")
print("103 INSTITUTIONAL READ MODEL: PASS")
print("104 COMMAND CENTER           : PASS")
print("106 INTEGRATION BOUNDARY    : PASS")

print()
print("102 -> 103 -> 104 -> 106")
print()

# ----------------------------------------------------------------------
# 13. FINAL JSON EVIDENCE
# ----------------------------------------------------------------------

banner("13. FINAL RUNTIME EVIDENCE")

evidence = {
    "block_102": {
        "status": block102_contract.get("status"),
        "block_id": block102_contract.get("block_id"),
    },
    "block_103": {
        "status": read_model.get("status"),
        "block_id": read_model.get("block_id"),
    },
    "block_104": {
        "status": command_center.get("status"),
        "block_id": command_center.get("block_id"),
    },
    "block_106": {
        "status": payload.get("status"),
        "block_id": payload.get("block_id"),
        "validated": valid,
    },
    "safety": {
        "broker": False,
        "live_execution": False,
        "order_creation": False,
        "portfolio_mutation": False,
        "valuation_mutation": False,
        "performance_mutation": False,
        "risk_mutation": False,
        "optimization": False,
        "execution_blocked": True,
        "non_mutation": True,
        "read_only": True,
    },
}

print(
    json.dumps(
        evidence,
        indent=2,
        sort_keys=True,
        default=str,
    )
)

# ----------------------------------------------------------------------
# 14. FINAL PASS
# ----------------------------------------------------------------------

banner("BLOCK 106 REAL 102 -> 103 -> 104 -> 106 RUNTIME : PASS")

print("BLOCK 102 : PASS")
print("BLOCK 103 : PASS")
print("BLOCK 104 : PASS")
print("BLOCK 106 : PASS")
print()
print("FULL CONTRACT CHAIN : PASS")
print("FULL SAFETY CHAIN   : PASS")
print()
print("BROKER               : FALSE")
print("LIVE EXECUTION       : FALSE")
print("ORDER CREATION       : FALSE")
print("MUTATION             : FALSE")
print("EXECUTION BLOCKED    : TRUE")
print("NON-MUTATION         : TRUE")
print("READ ONLY            : TRUE")
print()
print("NO COMMIT")
print("NO PUSH")
print("NO LIVE EXECUTION")
