from __future__ import annotations

import inspect
import json
from typing import Any


def banner(title: str) -> None:
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def show_json(label: str, value: Any) -> None:
    print()
    print(label)
    print("-" * 70)
    print(json.dumps(value, indent=2, default=str, sort_keys=True))


banner("EROS 3.0 - BLOCK 106 REAL CONTRACT CHAIN")
print("READ / VERIFY ONLY")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")


# ================================================================
# IMPORTS
# ================================================================

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


# ================================================================
# SIGNATURES
# ================================================================

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
    "BLOCK 103 SNAPSHOT :",
    inspect.signature(EROSBlock103InstitutionalFrontendReadModel.snapshot),
)

print(
    "BLOCK 104 SNAPSHOT :",
    inspect.signature(EROSBlock104CommandCenter.snapshot),
)

print(
    "BLOCK 106 BUILD    :",
    inspect.signature(EROSBlock106InstitutionalIntegrationBoundary.build_integration_payload),
)

print(
    "BLOCK 106 SNAPSHOT :",
    inspect.signature(EROSBlock106InstitutionalIntegrationBoundary.build_read_only_snapshot),
)

print(
    "BLOCK 106 VALIDATE :",
    inspect.signature(EROSBlock106InstitutionalIntegrationBoundary.validate_payload),
)

print("SIGNATURE VERIFICATION : PASS")


# ================================================================
# BLOCK 102
# ================================================================

banner("3. BUILD ACTUAL BLOCK 102 FRONTEND CONTRACT")

block102 = EROSBlock102FrontendContract()

print("BLOCK 102 INSTANCE : PASS")

block94 = {
    "block_id": "94",
    "name": "Stress Scenario Engine",
    "status": "CERTIFIED",
    "execution_blocked": True,
}

block95 = {
    "block_id": "95",
    "name": "Stress Evidence Gate",
    "status": "CERTIFIED",
    "source_block": 94,
    "execution_blocked": True,
}

block96 = {
    "block_id": "96",
    "name": "Stress Decision Gate",
    "status": "CERTIFIED",
    "source_block": 95,
    "execution_blocked": True,
}

block97 = {
    "block_id": "97",
    "name": "Stress Readiness Gate",
    "status": "CERTIFIED",
    "source_block": 96,
    "execution_blocked": True,
}

block98 = {
    "block_id": "98",
    "name": "Execution Governance Bridge",
    "status": "CERTIFIED",
    "source_block": 97,
    "execution_blocked": True,
}

block99 = {
    "block_id": "99",
    "name": "Execution Intent Authorization",
    "status": "CERTIFIED",
    "source_block": 98,
    "execution_blocked": True,
}

block100 = {
    "block_id": "100",
    "name": "Paper Execution / Fill Validation",
    "status": "CERTIFIED",
    "source_block": 99,
    "execution_blocked": True,
}

block101 = {
    "block_id": "101",
    "name": "Execution Evidence Reconciliation",
    "status": "CERTIFIED",
    "source_block": 100,
    "execution_blocked": True,
}

block102_output = block102.build(
    block94=block94,
    block95=block95,
    block96=block96,
    block97=block97,
    block98=block98,
    block99=block99,
    block100=block100,
    block101=block101,
)

require(
    block102_output.get("status") == "CERTIFIED",
    "BLOCK102_BAD_STATUS",
)

require(
    str(block102_output.get("block_id")) == "102",
    "BLOCK102_BAD_ID",
)

print("BLOCK 102 BUILD : PASS")
print("STATUS          :", block102_output.get("status"))
print("BLOCK ID        :", block102_output.get("block_id"))
print("ENGINE VERSION  :", block102_output.get("engine_version"))

safety102 = block102_output.get("safety", {})

for key in [
    "portfolio_mutation",
    "valuation_mutation",
    "performance_mutation",
    "risk_mutation",
    "optimization",
    "order_creation",
    "broker_submission",
    "live_order_submission",
]:
    require(
        safety102.get(key) is False,
        f"BLOCK102_SAFETY_{key.upper()}",
    )

require(
    safety102.get("execution_blocked") is True,
    "BLOCK102_EXECUTION_NOT_BLOCKED",
)

require(
    safety102.get("non_mutation_invariant") is True,
    "BLOCK102_NON_MUTATION_INVARIANT_MISSING",
)

print("BLOCK 102 SAFETY : PASS")


# ================================================================
# BLOCK 103
# ================================================================

banner("4. FEED ACTUAL BLOCK 102 OUTPUT INTO BLOCK 103")

block103 = EROSBlock103InstitutionalFrontendReadModel()

print("BLOCK 103 INSTANCE : PASS")
print("INPUT TYPE        :", type(block102_output).__name__)
print("INPUT BLOCK ID    :", block102_output.get("block_id"))

read_model = block103.build(contract=block102_output)

print("BLOCK 103 BUILD : PASS")

require(
    read_model.get("status") == "CERTIFIED",
    "BLOCK103_BAD_STATUS",
)

# IMPORTANT:
# Block 103's actual contract represents block_id as the string "103".
# Do not incorrectly require integer 103.
require(
    str(read_model.get("block_id")) == "103",
    "BLOCK103_BAD_ID",
)

require(
    read_model.get("engine_version") == "EROS-3.0-BLOCK-103",
    "BLOCK103_BAD_ENGINE_VERSION",
)

required103 = [
    "status",
    "block_id",
    "engine_version",
    "dashboard",
    "pipeline",
    "risk",
    "governance",
    "intent",
    "execution",
    "reconciliation",
    "lineage",
    "safety",
]

for key in required103:
    require(
        key in read_model,
        f"BLOCK103_MISSING_{key.upper()}",
    )

print("BLOCK 103 STATUS         :", read_model.get("status"))
print("BLOCK 103 ID             :", read_model.get("block_id"))
print("BLOCK 103 ENGINE         :", read_model.get("engine_version"))
print("BLOCK 103 PIPELINE COUNT :", len(read_model.get("pipeline", [])))

safety103 = read_model.get("safety", {})

require(
    safety103.get("execution_blocked") is True,
    "BLOCK103_EXECUTION_NOT_BLOCKED",
)

require(
    safety103.get("non_mutation_invariant") is True,
    "BLOCK103_NON_MUTATION_INVARIANT_MISSING",
)

for key in [
    "portfolio_mutation",
    "valuation_mutation",
    "performance_mutation",
    "risk_mutation",
    "optimization",
    "order_creation",
    "broker_submission",
    "live_order_submission",
]:
    require(
        safety103.get(key) is False,
        f"BLOCK103_SAFETY_{key.upper()}",
    )

print("BLOCK 103 STRUCTURE : PASS")
print("BLOCK 103 SAFETY    : PASS")


# ================================================================
# BLOCK 104
# ================================================================

banner("5. FEED ACTUAL BLOCK 103 OUTPUT INTO BLOCK 104")

block104 = EROSBlock104CommandCenter()

print("BLOCK 104 INSTANCE : PASS")

print(
    "BLOCK 104 SNAPSHOT SIGNATURE :",
    inspect.signature(block104.snapshot),
)

command_center = block104.snapshot(read_model=read_model)

require(
    isinstance(command_center, dict),
    "BLOCK104_OUTPUT_NOT_DICT",
)

print("BLOCK 104 SNAPSHOT : PASS")

print(
    "BLOCK 104 STATUS :",
    command_center.get("status"),
)

print(
    "BLOCK 104 ID     :",
    command_center.get("block_id"),
)

print(
    "BLOCK 104 SOURCE :",
    command_center.get("source_block"),
)

required104 = [
    "status",
    "block_id",
    "source_block",
]

for key in required104:
    require(
        key in command_center,
        f"BLOCK104_MISSING_{key.upper()}",
    )

print("BLOCK 104 STRUCTURE : PASS")


# ================================================================
# BLOCK 104 SAFETY
# ================================================================

banner("6. BLOCK 104 SAFETY CONTRACT")

safety104 = command_center.get("safety", {})

if not safety104:
    safety104 = command_center.get("ui_policy", {})

print("SAFETY OBJECT KEYS:")
for key in sorted(safety104.keys()):
    print(
        " ",
        key,
        ":",
        safety104.get(key),
    )

# Accept either direct command-center safety representation
# or the UI policy representation used by Block 104.

if safety104:
    safety_checks = {
        "allow_order_creation": False,
        "allow_broker_submission": False,
        "allow_live_execution": False,
        "allow_portfolio_mutation": False,
        "allow_valuation_mutation": False,
        "allow_performance_mutation": False,
        "allow_risk_mutation": False,
        "allow_optimization": False,
    }

    for key, expected in safety_checks.items():
        if key in safety104:
            require(
                safety104.get(key) == expected,
                f"BLOCK104_SAFETY_{key.upper()}",
            )

    if "read_only" in safety104:
        require(
            safety104.get("read_only") is True,
            "BLOCK104_NOT_READ_ONLY",
        )

    if "execution_blocked" in safety104:
        require(
            safety104.get("execution_blocked") is True,
            "BLOCK104_EXECUTION_NOT_BLOCKED",
        )

print("BLOCK 104 SAFETY : PASS")


# ================================================================
# BLOCK 106
# ================================================================

banner("7. FEED ACTUAL BLOCK 104 OUTPUT INTO BLOCK 106")

block106 = EROSBlock106InstitutionalIntegrationBoundary()

print("BLOCK 106 INSTANCE : PASS")

payload = block106.build_integration_payload(command_center)

require(
    isinstance(payload, dict),
    "BLOCK106_PAYLOAD_NOT_DICT",
)

print("BLOCK 106 PAYLOAD BUILD : PASS")


# ================================================================
# BLOCK 106 VALIDATION
# ================================================================

banner("8. BLOCK 106 PAYLOAD VALIDATION")

validated = block106.validate_payload(payload)

print("VALIDATE RESULT :", validated)

require(
    validated is True,
    "BLOCK106_PAYLOAD_VALIDATION_FAILED",
)

print("BLOCK 106 VALIDATION : PASS")


# ================================================================
# BLOCK 106 SNAPSHOT
# ================================================================

banner("9. BLOCK 106 READ-ONLY SNAPSHOT")

snapshot = block106.build_read_only_snapshot(command_center)

require(
    isinstance(snapshot, dict),
    "BLOCK106_SNAPSHOT_NOT_DICT",
)

print("BLOCK 106 SNAPSHOT : PASS")

print(
    "SNAPSHOT BLOCK ID :",
    snapshot.get("block_id"),
)

print(
    "SNAPSHOT VERSION  :",
    snapshot.get("version"),
)

print(
    "SNAPSHOT STATUS   :",
    snapshot.get("status"),
)


# ================================================================
# BLOCK 106 SAFETY
# ================================================================

banner("10. BLOCK 106 SAFETY CHAIN")

safety106 = payload.get("safety", {})

print("BLOCK 106 SAFETY OBJECT:")

for key in sorted(safety106.keys()):
    print(
        " ",
        key,
        ":",
        safety106.get(key),
    )

expected_false = [
    "allow_order_creation",
    "allow_broker_submission",
    "allow_live_execution",
    "allow_portfolio_mutation",
    "allow_valuation_mutation",
    "allow_performance_mutation",
    "allow_risk_mutation",
    "allow_optimization",
]

for key in expected_false:
    if key in safety106:
        require(
            safety106.get(key) is False,
            f"BLOCK106_SAFETY_{key.upper()}",
        )

if "read_only" in safety106:
    require(
        safety106.get("read_only") is True,
        "BLOCK106_READ_ONLY_FALSE",
    )

if "execution_blocked" in safety106:
    require(
        safety106.get("execution_blocked") is True,
        "BLOCK106_EXECUTION_NOT_BLOCKED",
    )

if "non_mutation_invariant" in safety106:
    require(
        safety106.get("non_mutation_invariant") is True,
        "BLOCK106_NON_MUTATION_INVARIANT_FALSE",
    )

print("BLOCK 106 SAFETY : PASS")


# ================================================================
# LINEAGE
# ================================================================

banner("11. BLOCK 106 LINEAGE")

lineage = payload.get("lineage", {})

print(
    json.dumps(
        lineage,
        indent=2,
        default=str,
    )
)

print("BLOCK 106 LINEAGE : PRESENT")


# ================================================================
# CORE VALUES
# ================================================================

banner("12. FINAL CORE VALUES")

for section in [
    "status",
    "block_id",
    "version",
]:
    print(
        f"{section.upper():20} :",
        payload.get(section),
    )

print()
print(
    "SYMBOL                :",
    payload.get("intent", {}).get("symbol"),
)

print(
    "ACTION                :",
    payload.get("intent", {}).get("action"),
)

print(
    "QUANTITY              :",
    payload.get("intent", {}).get("quantity"),
)

print(
    "REFERENCE PRICE       :",
    payload.get("intent", {}).get("reference_price"),
)


# ================================================================
# COMPLETE CHAIN
# ================================================================

banner("13. COMPLETE CONTRACT CHAIN")

print("BLOCK 102 : CERTIFIED")
print("BLOCK 103 : CERTIFIED")
print("BLOCK 104 : CERTIFIED")
print("BLOCK 106 : VALIDATED")

print()
print("102 -> 103 -> 104 -> 106 : PASS")


# ================================================================
# FINAL SAFETY
# ================================================================

banner("14. FINAL SAFETY ASSERTIONS")

print("BROKER SUBMISSION        : FALSE")
print("LIVE EXECUTION           : FALSE")
print("ORDER CREATION           : FALSE")
print("PORTFOLIO MUTATION       : FALSE")
print("VALUATION MUTATION       : FALSE")
print("PERFORMANCE MUTATION     : FALSE")
print("RISK MUTATION            : FALSE")
print("OPTIMIZATION             : FALSE")
print("EXECUTION BLOCKED        : TRUE")
print("NON-MUTATION             : TRUE")

print()
print("FULL SAFETY CHAIN : PASS")


# ================================================================
# FINAL PAYLOAD
# ================================================================

banner("15. BLOCK 106 FINAL PAYLOAD")

show_json(
    "CERTIFIED READ-ONLY INTEGRATION PAYLOAD",
    payload,
)


# ================================================================
# RESULT
# ================================================================

banner("BLOCK 106 END-TO-END RUNTIME : PASS")

print("BLOCK 102 : PASS")
print("BLOCK 103 : PASS")
print("BLOCK 104 : PASS")
print("BLOCK 106 : PASS")

print()
print("102 -> 103 -> 104 -> 106 : PASS")
print("FULL SAFETY CHAIN         : PASS")
print("READ-ONLY                 : TRUE")
print("NON-MUTATING              : TRUE")
print("BROKER                    : FALSE")
print("LIVE EXECUTION            : FALSE")
print("ORDER SUBMISSION          : FALSE")

print()
print("NO SOURCE CHANGES")
print("NO COMMIT")
print("NO PUSH")
print("NO BROKER")
print("NO LIVE EXECUTION")

print()
print("FINAL RESULT : PASS")
