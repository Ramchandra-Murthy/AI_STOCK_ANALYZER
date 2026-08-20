from __future__ import annotations

import json
import inspect
import sys
from pprint import pprint

print("=" * 70)
print("EROS 3.0 - BLOCK 102 -> BLOCK 103 ACTUAL OUTPUT")
print("=" * 70)

print()
print("1. IMPORTS")
print("-" * 70)

from services.quantitative.block102_frontend_contract import (
    EROSBlock102FrontendContract,
)

from services.quantitative.block103_institutional_frontend_read_model import (
    EROSBlock103InstitutionalFrontendReadModel,
)

print("BLOCK 102 IMPORT : PASS")
print("BLOCK 103 IMPORT : PASS")

print()
print("2. SIGNATURES")
print("-" * 70)

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

print()
print("3. BUILD REAL BLOCK 102 CONTRACT")
print("-" * 70)

block102 = EROSBlock102FrontendContract()

print("BLOCK 102 INSTANCE : PASS")

upstream = {}

for block_id in range(94, 102):
    upstream[str(block_id)] = {
        "status": "CERTIFIED",
        "block_id": block_id,
        "source_block": block_id - 1 if block_id > 94 else None,
        "pipeline": list(range(94, block_id + 1)),
        "symbol": "RELIANCE.NS",
        "action": "BUY",
        "quantity": 100.0,
        "reference_price": 2500.0,
        "execution_status": (
            "SIMULATED"
            if block_id >= 100
            else "CERTIFIED"
        ),
        "reconciliation": (
            "RECONCILED"
            if block_id >= 101
            else "PENDING"
        ),
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

block102_result = block102.build(
    block94=upstream["94"],
    block95=upstream["95"],
    block96=upstream["96"],
    block97=upstream["97"],
    block98=upstream["98"],
    block99=upstream["99"],
    block100=upstream["100"],
    block101=upstream["101"],
)

print("BLOCK 102 BUILD : PASS")
print()
print("BLOCK 102 TOP-LEVEL KEYS:")
print(sorted(block102_result.keys()))

print()
print("BLOCK 102 COMPLETE OUTPUT:")
print(json.dumps(block102_result, indent=2, default=str))

print()
print("4. FEED ACTUAL BLOCK 102 OUTPUT INTO BLOCK 103")
print("-" * 70)

block103 = EROSBlock103InstitutionalFrontendReadModel()

print("BLOCK 103 INSTANCE : PASS")
print("INPUT TYPE        :", type(block102_result).__name__)

try:
    read_model = block103.build(
        contract=block102_result
    )
except Exception as exc:
    print()
    print("BLOCK 103 BUILD : FAILED")
    print("EXCEPTION TYPE  :", type(exc).__name__)
    print("EXCEPTION       :", str(exc))
    raise

print()
print("BLOCK 103 BUILD : PASS")

print()
print("5. BLOCK 103 ACTUAL TOP-LEVEL KEYS")
print("-" * 70)

print(sorted(read_model.keys()))

print()
print("6. BLOCK 103 ACTUAL CORE VALUES")
print("-" * 70)

print("status          :", repr(read_model.get("status")))
print("block_id        :", repr(read_model.get("block_id")))
print("engine_version  :", repr(read_model.get("engine_version")))

print()
print("dashboard       :")
pprint(read_model.get("dashboard"))

print()
print("pipeline        :")
pprint(read_model.get("pipeline"))

print()
print("governance      :")
pprint(read_model.get("governance"))

print()
print("intent          :")
pprint(read_model.get("intent"))

print()
print("execution       :")
pprint(read_model.get("execution"))

print()
print("reconciliation  :")
pprint(read_model.get("reconciliation"))

print()
print("lineage         :")
pprint(read_model.get("lineage"))

print()
print("safety          :")
pprint(read_model.get("safety"))

print()
print("7. BLOCK 103 COMPLETE JSON")
print("-" * 70)

print(json.dumps(read_model, indent=2, default=str))

print()
print("8. BLOCK 103 ID DIAGNOSTIC")
print("-" * 70)

print("EXPECTED BLOCK ID : 103")
print("ACTUAL BLOCK ID   :", repr(read_model.get("block_id")))

if read_model.get("block_id") == 103:
    print("BLOCK 103 ID : PASS")
else:
    print("BLOCK 103 ID : MISMATCH")

print()
print("EXPECTED STATUS   : CERTIFIED")
print("ACTUAL STATUS     :", repr(read_model.get("status")))

if read_model.get("status") == "CERTIFIED":
    print("BLOCK 103 STATUS : PASS")
else:
    print("BLOCK 103 STATUS : MISMATCH")

print()
print("9. STRUCTURAL DIAGNOSTIC")
print("-" * 70)

required_keys = [
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

for key in required_keys:
    print(
        f"{key:<20} : "
        f"{'PRESENT' if key in read_model else 'MISSING'}"
    )

print()
print("10. SAFETY DIAGNOSTIC")
print("-" * 70)

safety = read_model.get("safety", {})

if isinstance(safety, dict):
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
        "execution_blocked",
        "non_mutation_invariant",
    ]:
        print(f"{key:<32} : {safety.get(key)!r}")
else:
    print("SAFETY OBJECT TYPE :", type(safety).__name__)

print()
print("11. BLOCK 103 ACTUAL OUTPUT COMPLETE")
print("=" * 70)

print()
print("PYTHON EXIT STATUS : PASS")
