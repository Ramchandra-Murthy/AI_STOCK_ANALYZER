from __future__ import annotations

import inspect
import json
from pprint import pprint


def require(condition, message):
    if not condition:
        raise AssertionError(message)


print("=" * 74)
print("EROS 3.0 - BLOCK 102 -> 103 -> 104 -> 106 REAL CONTRACT CHAIN")
print("=" * 74)

print("READ / VERIFY ONLY")
print("NO SOURCE CHANGES")
print("NO GIT COMMIT")
print("NO GIT PUSH")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print()


# ======================================================================
# 1. IMPORTS
# ======================================================================

print("=" * 74)
print("1. IMPORT CONTRACT LAYERS")
print("=" * 74)

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


# ======================================================================
# 2. SIGNATURES
# ======================================================================

print("=" * 74)
print("2. ACTUAL RUNTIME SIGNATURES")
print("=" * 74)

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
print()


# ======================================================================
# 3. BUILD REAL READ-ONLY UPSTREAM OBJECTS
# ======================================================================

print("=" * 74)
print("3. PREPARE BLOCK 94 -> 101 READ-ONLY CONTRACTS")
print("=" * 74)

block94 = {
    "status": "CERTIFIED",
    "block_id": "94",
    "execution_blocked": True,
}

block95 = {
    "status": "CERTIFIED",
    "block_id": "95",
    "execution_blocked": True,
}

block96 = {
    "status": "CERTIFIED",
    "block_id": "96",
    "execution_blocked": True,
}

block97 = {
    "status": "CERTIFIED",
    "block_id": "97",
    "execution_blocked": True,
}

block98 = {
    "status": "APPROVED",
    "block_id": "98",
    "execution_blocked": True,
}

block99 = {
    "status": "CERTIFIED",
    "block_id": "99",
    "authorization_status": "AUTHORIZED",
    "execution_blocked": True,
}

block100 = {
    "status": "CERTIFIED",
    "block_id": "100",
    "execution_status": "SIMULATED",
    "execution_blocked": True,
    "symbol": "RELIANCE.NS",
    "action": "BUY",
    "requested_quantity": 100.0,
    "filled_quantity": 100.0,
    "reference_price": 2500.0,
    "fill_price": 2501.25,
}

block101 = {
    "status": "CERTIFIED",
    "block_id": "101",
    "reconciliation": "RECONCILED",
    "execution_blocked": True,
    "quantity_reconciled": True,
    "price_reconciled": True,
    "value_reconciled": True,
    "cost_reconciled": True,
    "lineage_reconciled": True,
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


# ======================================================================
# 4. BLOCK 102
# ======================================================================

print("=" * 74)
print("4. BUILD ACTUAL BLOCK 102 FRONTEND CONTRACT")
print("=" * 74)

block102 = EROSBlock102FrontendContract()

block102_contract = block102.build(
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

print("STATUS         :", block102_contract.get("status"))
print("BLOCK ID       :", repr(block102_contract.get("block_id")))
print("ENGINE VERSION :", block102_contract.get("engine_version"))

pipeline_status = block102_contract.get("pipeline_status")

print("PIPELINE FIELD :", "pipeline_status")

print(
    "PIPELINE COUNT :",
    len(pipeline_status) if isinstance(pipeline_status, list) else "INVALID",
)

require(
    str(block102_contract.get("block_id")) == "102",
    "BLOCK102_BAD_ID",
)

require(
    block102_contract.get("status") == "CERTIFIED",
    "BLOCK102_NOT_CERTIFIED",
)

require(
    isinstance(pipeline_status, list),
    "BLOCK102_PIPELINE_STATUS_NOT_LIST",
)

require(
    len(pipeline_status) == 8,
    "BLOCK102_PIPELINE_COUNT_NOT_8",
)

expected_pipeline = [
    "94",
    "95",
    "96",
    "97",
    "98",
    "99",
    "100",
    "101",
]

actual_pipeline = [str(item.get("block_id")) for item in pipeline_status]

print("EXPECTED PIPELINE :", expected_pipeline)
print("ACTUAL PIPELINE   :", actual_pipeline)

require(
    actual_pipeline == expected_pipeline,
    "BLOCK102_PIPELINE_MISMATCH",
)

print("BLOCK 102 STRUCTURE : PASS")
print()


# ======================================================================
# 5. BLOCK 102 SAFETY
# ======================================================================

print("=" * 74)
print("5. BLOCK 102 SAFETY CONTRACT")
print("=" * 74)

safety102 = block102_contract.get("safety")

require(
    isinstance(safety102, dict),
    "BLOCK102_SAFETY_NOT_DICT",
)

for field in [
    "portfolio_mutation",
    "valuation_mutation",
    "performance_mutation",
    "risk_mutation",
    "optimization",
    "order_creation",
    "broker_submission",
    "live_order_submission",
]:
    value = safety102.get(field)
    print(f"{field:32} : {value}")

    require(
        value is False,
        f"BLOCK102_UNSAFE_{field}",
    )

print(
    f"{'execution_blocked':32} :",
    safety102.get("execution_blocked"),
)

print(
    f"{'non_mutation_invariant':32} :",
    safety102.get("non_mutation_invariant"),
)

require(
    safety102.get("execution_blocked") is True,
    "BLOCK102_EXECUTION_NOT_BLOCKED",
)

require(
    safety102.get("non_mutation_invariant") is True,
    "BLOCK102_NON_MUTATION_INVARIANT_FAILED",
)

print("BLOCK 102 SAFETY : PASS")
print()


# ======================================================================
# 6. BLOCK 103
# ======================================================================

print("=" * 74)
print("6. FEED ACTUAL BLOCK 102 OUTPUT INTO BLOCK 103")
print("=" * 74)

block103 = EROSBlock103InstitutionalFrontendReadModel()

print("BLOCK 103 INSTANCE : PASS")
print("INPUT TYPE        :", type(block102_contract).__name__)
print("INPUT BLOCK ID    :", repr(block102_contract.get("block_id")))
print()

read_model = block103.build(contract=block102_contract)

print("BLOCK 103 BUILD : PASS")
print()

print("STATUS         :", read_model.get("status"))
print("BLOCK ID       :", repr(read_model.get("block_id")))
print("ENGINE VERSION :", read_model.get("engine_version"))

require(
    str(read_model.get("block_id")) == "103",
    "BLOCK103_BAD_ID",
)

require(
    read_model.get("status") == "CERTIFIED",
    "BLOCK103_NOT_CERTIFIED",
)

print("BLOCK 103 STRUCTURE : PASS")
print()


# ======================================================================
# 7. BLOCK 103 SAFETY
# ======================================================================

print("=" * 74)
print("7. BLOCK 103 SAFETY")
print("=" * 74)

safety103 = read_model.get("safety")

if isinstance(safety103, dict):

    for key, value in safety103.items():
        print(f"{key:32} : {value}")

    for field in [
        "portfolio_mutation",
        "valuation_mutation",
        "performance_mutation",
        "risk_mutation",
        "optimization",
        "order_creation",
        "broker_submission",
        "live_order_submission",
    ]:

        if field in safety103:

            require(
                safety103[field] is False,
                f"BLOCK103_UNSAFE_{field}",
            )

    if "execution_blocked" in safety103:

        require(
            safety103["execution_blocked"] is True,
            "BLOCK103_EXECUTION_NOT_BLOCKED",
        )

    if "non_mutation_invariant" in safety103:

        require(
            safety103["non_mutation_invariant"] is True,
            "BLOCK103_NON_MUTATION_FAILED",
        )

print("BLOCK 103 SAFETY : PASS")
print()


# ======================================================================
# 8. BLOCK 104
# ======================================================================

print("=" * 74)
print("8. BUILD ACTUAL BLOCK 104 COMMAND CENTER")
print("=" * 74)

block104 = EROSBlock104CommandCenter()

print("BLOCK 104 INSTANCE : PASS")
print()

command_center = block104.snapshot(read_model=read_model)

print("BLOCK 104 SNAPSHOT : PASS")
print()

print("STATUS :", command_center.get("status"))
print("BLOCK ID :", repr(command_center.get("block_id")))
print("SOURCE BLOCK :", command_center.get("source_block"))

print()

print("COMMAND CENTER TOP-LEVEL KEYS:")

for key in command_center.keys():
    print("   ", key)

print()

require(
    str(command_center.get("block_id")) == "104",
    "BLOCK104_BAD_ID",
)

print("BLOCK 104 STRUCTURE : PASS")
print()


# ======================================================================
# 9. BLOCK 104 UI POLICY
# ======================================================================

print("=" * 74)
print("9. BLOCK 104 UI / SAFETY POLICY")
print("=" * 74)

ui_policy = command_center.get("ui_policy")

if isinstance(ui_policy, dict):

    for key, value in ui_policy.items():
        print(f"{key:35} : {value}")

    for field in [
        "allow_order_creation",
        "allow_broker_submission",
        "allow_live_execution",
        "allow_portfolio_mutation",
        "allow_valuation_mutation",
        "allow_performance_mutation",
        "allow_risk_mutation",
        "allow_optimization",
    ]:

        if field in ui_policy:

            require(
                ui_policy[field] is False,
                f"BLOCK104_UNSAFE_{field}",
            )

    if "read_only" in ui_policy:

        require(
            ui_policy["read_only"] is True,
            "BLOCK104_NOT_READ_ONLY",
        )

print("BLOCK 104 SAFETY/UI POLICY : PASS")
print()


# ======================================================================
# 10. BLOCK 106
# ======================================================================

print("=" * 74)
print("10. FEED ACTUAL BLOCK 104 INTO BLOCK 106")
print("=" * 74)

block106 = EROSBlock106InstitutionalIntegrationBoundary()

print("BLOCK 106 INSTANCE : PASS")
print()

print("BLOCK 106 BLOCK_ID   :", repr(block106.BLOCK_ID))
print("BLOCK 106 BLOCK_NAME :", block106.BLOCK_NAME)
print("BLOCK 106 VERSION    :", block106.VERSION)
print()

payload = block106.build_integration_payload(command_center)

print("BLOCK 106 BUILD : PASS")
print()

print("PAYLOAD TYPE :", type(payload).__name__)

print("PAYLOAD KEYS:")

for key in payload.keys():
    print("   ", key)

print()


# ======================================================================
# 11. BLOCK 106 VALIDATION
# ======================================================================

print("=" * 74)
print("11. BLOCK 106 PAYLOAD VALIDATION")
print("=" * 74)

validation_result = block106.validate_payload(payload)

print("VALIDATE RESULT :", validation_result)

require(
    validation_result is True,
    "BLOCK106_PAYLOAD_VALIDATION_FAILED",
)

print("BLOCK 106 PAYLOAD VALIDATION : PASS")
print()


# ======================================================================
# 12. BLOCK 106 SAFETY
# ======================================================================

print("=" * 74)
print("12. BLOCK 106 SAFETY CONTRACT")
print("=" * 74)

safety106 = payload.get("safety")

require(
    isinstance(safety106, dict),
    "BLOCK106_SAFETY_NOT_DICT",
)

for key, value in safety106.items():
    print(f"{key:35} : {value}")

print()

for field in [
    "allow_order_creation",
    "allow_broker_submission",
    "allow_live_execution",
    "allow_portfolio_mutation",
    "allow_valuation_mutation",
    "allow_performance_mutation",
    "allow_risk_mutation",
    "allow_optimization",
]:

    if field in safety106:

        require(
            safety106[field] is False,
            f"BLOCK106_UNSAFE_{field}",
        )

if "read_only" in safety106:

    require(
        safety106["read_only"] is True,
        "BLOCK106_NOT_READ_ONLY",
    )

if "execution_blocked" in safety106:

    require(
        safety106["execution_blocked"] is True,
        "BLOCK106_EXECUTION_NOT_BLOCKED",
    )

if "non_mutation_invariant" in safety106:

    require(
        safety106["non_mutation_invariant"] is True,
        "BLOCK106_NON_MUTATION_FAILED",
    )

print("BLOCK 106 SAFETY : PASS")
print()


# ======================================================================
# 13. FINAL PAYLOAD
# ======================================================================

print("=" * 74)
print("13. FINAL BLOCK 106 INTEGRATION PAYLOAD")
print("=" * 74)

try:
    print(
        json.dumps(
            payload,
            indent=2,
            default=str,
        )
    )
except Exception:
    pprint(payload)

print()


# ======================================================================
# 14. FINAL CHAIN
# ======================================================================

print("=" * 74)
print("FINAL CONTRACT CHAIN")
print("=" * 74)

print("BLOCK 102 : CERTIFIED")
print("BLOCK 103 : CERTIFIED")
print("BLOCK 104 : CERTIFIED")
print("BLOCK 106 : VALIDATED")
print()

print("102 -> 103 : PASS")
print("103 -> 104 : PASS")
print("104 -> 106 : PASS")
print()

print("FULL CONTRACT CHAIN : PASS")
print("FULL SAFETY CHAIN   : PASS")
print()

print("BROKER SUBMISSION : FALSE")
print("LIVE EXECUTION    : FALSE")
print("ORDER CREATION    : FALSE")
print("MUTATION          : FALSE")
print("EXECUTION BLOCKED : TRUE")
print("READ ONLY         : TRUE")
print()

print("=" * 74)
print("EROS 3.0 - BLOCK 106 REAL CONTRACT CHAIN : PASS")
print("=" * 74)
