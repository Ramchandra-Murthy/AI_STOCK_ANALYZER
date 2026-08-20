from __future__ import annotations

from pprint import pprint
from typing import Any

from services.quantitative.block102_frontend_contract import (
    EROSBlock102FrontendContract,
)
from services.quantitative.block103_institutional_frontend_read_model import (
    EROSBlock103InstitutionalFrontendReadModel,
)


def show(label: str, value: Any) -> None:
    print(f"{label}")
    print("-" * 70)
    print(f"value       : {value!r}")
    print(f"type        : {type(value).__name__}")
    print(f"type repr   : {type(value)!r}")
    print()


print("=" * 70)
print("EROS 3.0 - BLOCK 102 -> BLOCK 103 ID TYPE DIAGNOSTIC")
print("=" * 70)
print()

print("1. IMPORTS")
print("-" * 70)

print("BLOCK 102 IMPORT : PASS")
print("BLOCK 103 IMPORT : PASS")
print()

print("=" * 70)
print("2. CLASS CONSTANT TYPES")
print("=" * 70)
print()

show(
    "BLOCK 102 CLASS BLOCK_ID",
    EROSBlock102FrontendContract.BLOCK_ID,
)

show(
    "BLOCK 103 CLASS BLOCK_ID",
    EROSBlock103InstitutionalFrontendReadModel.BLOCK_ID,
)

print("=" * 70)
print("3. BUILD BLOCK 102")
print("=" * 70)
print()

block102 = EROSBlock102FrontendContract()

block102_output = block102.build()

print("BLOCK 102 BUILD : PASS")
print()

show(
    "BLOCK 102 OUTPUT block_id",
    block102_output.get("block_id"),
)

show(
    "BLOCK 102 OUTPUT status",
    block102_output.get("status"),
)

print("=" * 70)
print("4. BLOCK 102 OUTPUT KEY TYPES")
print("=" * 70)
print()

for key in sorted(block102_output.keys()):
    value = block102_output.get(key)

    print(
        f"{key:<25} "
        f"type={type(value).__name__:<15} "
        f"value={value!r}"
    )

print()

print("=" * 70)
print("5. BUILD BLOCK 103 FROM ACTUAL BLOCK 102 OUTPUT")
print("=" * 70)
print()

block103 = EROSBlock103InstitutionalFrontendReadModel()

read_model = block103.build(
    contract=block102_output
)

print("BLOCK 103 BUILD : PASS")
print()

show(
    "BLOCK 103 OUTPUT block_id",
    read_model.get("block_id"),
)

show(
    "BLOCK 103 OUTPUT status",
    read_model.get("status"),
)

show(
    "BLOCK 103 OUTPUT engine_version",
    read_model.get("engine_version"),
)

print("=" * 70)
print("6. EXACT ID COMPARISONS")
print("=" * 70)
print()

actual = read_model.get("block_id")
class_id = EROSBlock103InstitutionalFrontendReadModel.BLOCK_ID

print(f"actual value              : {actual!r}")
print(f"actual type               : {type(actual).__name__}")
print()

print(f"class BLOCK_ID value      : {class_id!r}")
print(f"class BLOCK_ID type       : {type(class_id).__name__}")
print()

print(f"actual == 103             : {actual == 103}")
print(f"actual == '103'           : {actual == '103'}")
print(f"actual == class_id        : {actual == class_id}")
print(f"type(actual) is int       : {type(actual) is int}")
print(f"type(actual) is str       : {type(actual) is str}")
print()

print("=" * 70)
print("7. ASSERTION MATRIX")
print("=" * 70)
print()

tests = {
    "actual == 103": actual == 103,
    "actual == '103'": actual == "103",
    "actual == class_id": actual == class_id,
    "str(actual) == '103'": str(actual) == "103",
    "int(actual) == 103": (
        isinstance(actual, (int, float, str))
        and int(actual) == 103
    ),
}

for name, result in tests.items():
    print(f"{name:<35} : {'PASS' if result else 'FAIL'}")

print()

print("=" * 70)
print("8. BLOCK 103 TOP-LEVEL CONTRACT")
print("=" * 70)
print()

for key in read_model:
    value = read_model[key]

    print(
        f"{key:<20} "
        f"type={type(value).__name__:<15} "
        f"value={value!r}"
    )

print()

print("=" * 70)
print("9. CONTRACT CONCLUSION")
print("=" * 70)
print()

if actual == class_id:
    print("BLOCK 103 INTERNAL ID CONSISTENCY : PASS")
else:
    print("BLOCK 103 INTERNAL ID CONSISTENCY : FAIL")

if actual == 103:
    print("INTEGER BLOCK ID CONTRACT          : PASS")
else:
    print("INTEGER BLOCK ID CONTRACT          : FAIL")

if actual == "103":
    print("STRING BLOCK ID CONTRACT           : PASS")
else:
    print("STRING BLOCK ID CONTRACT           : FAIL")

if actual == class_id:
    print()
    print("CONCLUSION:")
    print("Block 103 produces the same ID as its class constant.")
    print("The previous failure is therefore almost certainly")
    print("a test expectation/type normalization problem.")
else:
    print()
    print("CONCLUSION:")
    print("Block 103 class ID and output ID differ.")
    print("SOURCE INSPECTION REQUIRED.")

print()

print("=" * 70)
print("10. NO MUTATION CHECK")
print("=" * 70)
print()

safety = read_model.get("safety")

if isinstance(safety, dict):
    safety_checks = {
        "portfolio_mutation": safety.get("portfolio_mutation"),
        "valuation_mutation": safety.get("valuation_mutation"),
        "performance_mutation": safety.get("performance_mutation"),
        "risk_mutation": safety.get("risk_mutation"),
        "optimization": safety.get("optimization"),
        "order_creation": safety.get("order_creation"),
        "broker_submission": safety.get("broker_submission"),
        "live_order_submission": safety.get("live_order_submission"),
        "execution_blocked": safety.get("execution_blocked"),
        "non_mutation_invariant": safety.get("non_mutation_invariant"),
    }

    for key, value in safety_checks.items():
        print(f"{key:<30} : {value!r}")

print()

print("=" * 70)
print(" BLOCK 102 -> BLOCK 103 ID TYPE DIAGNOSTIC COMPLETE")
print("=" * 70)
