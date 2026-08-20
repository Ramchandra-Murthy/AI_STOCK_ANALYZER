from __future__ import annotations

import inspect
import json
import os
import sys
from typing import Any, Dict


print("")
print("=" * 70)
print("EROS 3.0 - BLOCK 103 SOURCE CONTRACT DIAGNOSTIC")
print("=" * 70)
print("")


# ======================================================================
# 1. IMPORT BLOCK 103
# ======================================================================

print("1. IMPORT BLOCK 103")
print("-" * 70)

from services.quantitative.block103_institutional_frontend_read_model import (
    EROSBlock103InstitutionalFrontendReadModel,
)

print("BLOCK 103 IMPORT : PASS")
print("")


# ======================================================================
# 2. CLASS INFORMATION
# ======================================================================

print("2. BLOCK 103 CLASS INFORMATION")
print("-" * 70)

cls = EROSBlock103InstitutionalFrontendReadModel

print("CLASS:")
print(cls)

print("")
print("MODULE:")
print(cls.__module__)

print("")
print("FILE:")
print(inspect.getfile(cls))

print("")


# ======================================================================
# 3. CONSTANTS
# ======================================================================

print("3. BLOCK 103 CONTRACT CONSTANTS")
print("-" * 70)

for name in dir(cls):

    if name.startswith("_"):
        continue

    try:
        value = getattr(cls, name)

        if not callable(value):

            print(f"{name} = {value!r}")

    except Exception as exc:

        print(f"{name} = <ERROR READING: {exc}>")


print("")


# ======================================================================
# 4. BUILD / SNAPSHOT SIGNATURES
# ======================================================================

print("4. BLOCK 103 PUBLIC METHOD SIGNATURES")
print("-" * 70)

print(
    "BUILD:",
    inspect.signature(cls.build)
)

print(
    "SNAPSHOT:",
    inspect.signature(cls.snapshot)
)

print("")


# ======================================================================
# 5. VALIDATION METHODS
# ======================================================================

print("5. BLOCK 103 VALIDATION METHODS")
print("-" * 70)

validation_methods = [
    "_validate_source",
    "_build_pipeline",
    "_build_risk",
    "_build_governance",
    "_build_intent",
    "_build_execution",
    "_build_reconciliation",
    "_build_lineage",
    "_build_safety",
]

for method_name in validation_methods:

    method = getattr(cls, method_name, None)

    if method is None:

        print(f"{method_name} : NOT FOUND")

    else:

        print("")
        print(f"{method_name} : FOUND")
        print("-" * 50)

        try:
            print(inspect.getsource(method))
        except Exception as exc:
            print(f"SOURCE ERROR: {exc}")


print("")


# ======================================================================
# 6. CONSTRUCTOR
# ======================================================================

print("6. BLOCK 103 INSTANCE CREATION")
print("-" * 70)

block103 = cls()

print("INSTANCE : PASS")
print("TYPE     :", type(block103).__name__)
print("")


# ======================================================================
# 7. CREATE MINIMAL CONTRACT CANDIDATES
# ======================================================================

print("7. SOURCE CONTRACT CANDIDATES")
print("-" * 70)

#
# Candidate A:
# The contract we previously attempted.
#

candidate_a: Dict[str, Any] = {

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


print("CANDIDATE A")
print(json.dumps(candidate_a, indent=2, sort_keys=True))
print("")


# ======================================================================
# 8. DIRECT SOURCE VALIDATION
# ======================================================================

print("8. DIRECT BLOCK 103 SOURCE VALIDATION")
print("-" * 70)

print("")
print("Testing Candidate A against _validate_source()")
print("")

try:

    validator = getattr(block103, "_validate_source")

    validator(candidate_a)

    print("CANDIDATE A VALIDATION : PASS")

except Exception as exc:

    print("CANDIDATE A VALIDATION : FAIL")
    print("EXCEPTION TYPE          :", type(exc).__name__)
    print("EXCEPTION MESSAGE       :", str(exc))

print("")


# ======================================================================
# 9. DIAGNOSTIC FIELD PROBE
# ======================================================================

print("9. BLOCK 103 SOURCE FIELD PROBE")
print("-" * 70)

print("")

for key in sorted(candidate_a.keys()):

    value = candidate_a[key]

    print(
        f"FIELD {key:<20} TYPE={type(value).__name__}"
    )

    if isinstance(value, dict):

        print(
            " " * 4,
            "SUBFIELDS:",
            ", ".join(sorted(value.keys()))
        )

print("")


# ======================================================================
# 10. TRY POSSIBLE SOURCE BLOCK REPRESENTATIONS
# ======================================================================

print("10. SOURCE BLOCK REPRESENTATION DIAGNOSTIC")
print("-" * 70)

source_block_values = [
    100,
    101,
    102,
    103,
    "100",
    "101",
    "102",
    "103",
]

for source_value in source_block_values:

    test_contract = dict(candidate_a)

    test_contract["block_id"] = 102

    lineage = dict(candidate_a["lineage"])
    lineage["source_block"] = source_value

    test_contract["lineage"] = lineage

    try:

        validator(test_contract)

        print(
            f"source_block={source_value!r:<8} -> VALID"
        )

    except Exception as exc:

        print(
            f"source_block={source_value!r:<8} -> "
            f"{type(exc).__name__}: {exc}"
        )

print("")


# ======================================================================
# 11. TRY TOP-LEVEL BLOCK ID REPRESENTATIONS
# ======================================================================

print("11. TOP-LEVEL BLOCK ID DIAGNOSTIC")
print("-" * 70)

for block_value in [
    100,
    101,
    102,
    103,
    "100",
    "101",
    "102",
    "103",
]:

    test_contract = dict(candidate_a)

    test_contract["block_id"] = block_value

    try:

        validator(test_contract)

        print(
            f"block_id={block_value!r:<8} -> VALID"
        )

    except Exception as exc:

        print(
            f"block_id={block_value!r:<8} -> "
            f"{type(exc).__name__}: {exc}"
        )

print("")


# ======================================================================
# 12. VALIDATION SOURCE CODE AGAIN
# ======================================================================

print("12. EXACT _validate_source IMPLEMENTATION")
print("-" * 70)

try:

    print(
        inspect.getsource(
            getattr(cls, "_validate_source")
        )
    )

except Exception as exc:

    print("UNABLE TO READ SOURCE:", exc)

print("")


# ======================================================================
# 13. BLOCK 103 BUILD ATTEMPT
# ======================================================================

print("13. BLOCK 103 BUILD ATTEMPT")
print("-" * 70)

try:

    result = block103.build(
        contract=candidate_a
    )

    print("BLOCK 103 BUILD : PASS")

    print("")
    print("RESULT STATUS   :", result.get("status"))
    print("RESULT BLOCK ID :", result.get("block_id"))

except Exception as exc:

    print("BLOCK 103 BUILD : FAIL")
    print("EXCEPTION TYPE  :", type(exc).__name__)
    print("EXCEPTION       :", str(exc))


print("")


# ======================================================================
# 14. FINAL DIAGNOSTIC
# ======================================================================

print("=" * 70)
print("BLOCK 103 SOURCE CONTRACT DIAGNOSTIC COMPLETE")
print("=" * 70)
print("")

print("IMPORTANT:")
print("This diagnostic does NOT modify Block 103.")
print("This diagnostic does NOT modify Block 106.")
print("No broker was contacted.")
print("No live execution occurred.")
print("No order was created.")
print("No commit was performed.")
print("No push was performed.")

print("")
print("RESULT : DIAGNOSTIC COMPLETE")
print("")

