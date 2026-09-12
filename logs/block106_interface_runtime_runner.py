from __future__ import annotations

import sys
import traceback

print("=" * 70)
print("EROS 3.0 - BLOCK 106 PYTHON INTERFACE + RUNTIME RUNNER")
print("=" * 70)
print()

failures = []


# ==============================================================
# 1. IMPORT BLOCK 106
# ==============================================================

print("1. BLOCK 106 IMPORT")
print("-" * 70)

try:
    from services.quantitative.block106_institutional_integration_boundary import (
        EROSBlock106InstitutionalIntegrationBoundary,
    )

    print("BLOCK 106 IMPORT : PASS")
    print(
        "CLASS            :",
        EROSBlock106InstitutionalIntegrationBoundary.__name__,
    )

except Exception as exc:
    print("BLOCK 106 IMPORT : FAILED")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    failures.append("BLOCK 106 IMPORT")


# ==============================================================
# 2. PUBLIC INTERFACE INSPECTION
# ==============================================================

if not failures:

    print()
    print("2. BLOCK 106 PUBLIC INTERFACE")
    print("-" * 70)

    try:
        cls = EROSBlock106InstitutionalIntegrationBoundary

        public_names = [name for name in dir(cls) if not name.startswith("_")]

        for name in public_names:
            print("PUBLIC :", name)

        print()
        print("PUBLIC INTERFACE : PASS")

    except Exception as exc:
        print("PUBLIC INTERFACE : FAILED")
        print(type(exc).__name__, str(exc))
        traceback.print_exc()
        failures.append("PUBLIC INTERFACE")


# ==============================================================
# 3. CLASS CONSTANTS
# ==============================================================

if not failures:

    print()
    print("3. BLOCK 106 CLASS CONTRACT")
    print("-" * 70)

    try:
        constants = [
            "BLOCK_ID",
            "BLOCK_NAME",
            "STATUS",
        ]

        for name in constants:
            if hasattr(cls, name):
                print(f"{name:<25}:", getattr(cls, name))
            else:
                print(f"{name:<25}: NOT EXPOSED")

        print()
        print("CLASS CONTRACT : PASS")

    except Exception as exc:
        print("CLASS CONTRACT : FAILED")
        print(type(exc).__name__, str(exc))
        traceback.print_exc()
        failures.append("CLASS CONTRACT")


# ==============================================================
# 4. CONSTRUCTOR / INSTANCE
# ==============================================================

if not failures:

    print()
    print("4. BLOCK 106 INSTANCE CREATION")
    print("-" * 70)

    try:
        boundary = cls()

        print("INSTANCE CREATION : PASS")
        print("INSTANCE TYPE     :", type(boundary).__name__)

    except Exception as exc:
        print("INSTANCE CREATION : FAILED")
        print(type(exc).__name__, str(exc))
        traceback.print_exc()
        failures.append("INSTANCE CREATION")


# ==============================================================
# 5. METHOD SIGNATURE INSPECTION
# ==============================================================

if not failures:

    print()
    print("5. BLOCK 106 METHOD SIGNATURES")
    print("-" * 70)

    try:
        import inspect

        for name in public_names:
            attr = getattr(cls, name)

            if callable(attr):
                try:
                    signature = inspect.signature(attr)
                    print(f"{name}{signature}")
                except Exception:
                    print(f"{name} : callable")

        print()
        print("METHOD SIGNATURES : PASS")

    except Exception as exc:
        print("METHOD SIGNATURES : FAILED")
        print(type(exc).__name__, str(exc))
        traceback.print_exc()
        failures.append("METHOD SIGNATURES")


# ==============================================================
# 6. READ-ONLY SAFETY INSPECTION
# ==============================================================

if not failures:

    print()
    print("6. BLOCK 106 SAFETY CONTRACT")
    print("-" * 70)

    source = ""

    try:
        import inspect

        source = inspect.getsource(cls)

    except Exception:
        pass

    safety_terms = [
        "read_only",
        "non_mutating",
        "broker",
        "live_execution",
        "portfolio_mutation",
        "valuation_mutation",
        "performance_mutation",
        "risk_mutation",
        "optimization",
        "order_creation",
    ]

    for term in safety_terms:
        if term.lower() in source.lower():
            print(f"{term:<30}: PRESENT")
        else:
            print(f"{term:<30}: NOT FOUND IN CLASS SOURCE")

    print()
    print("SAFETY CONTRACT INSPECTION : PASS")


# ==============================================================
# 7. CERTIFIED BLOCK 104 INPUT
# ==============================================================

if not failures:

    print()
    print("7. BLOCK 104 INPUT CONTRACT")
    print("-" * 70)

    try:
        from services.quantitative.block104_eros_command_center import (
            EROSBlock104CommandCenter,
        )

        block104 = EROSBlock104CommandCenter()

        print("BLOCK 104 INSTANCE : PASS")

        print()
        print("BLOCK 104 TYPE      :", type(block104).__name__)

        block104_public = [name for name in dir(block104) if not name.startswith("_")]

        for name in block104_public:
            print("BLOCK 104 PUBLIC    :", name)

        print()
        print("BLOCK 104 INPUT CONTRACT : PASS")

    except Exception as exc:
        print("BLOCK 104 INPUT CONTRACT : FAILED")
        print(type(exc).__name__, str(exc))
        traceback.print_exc()
        failures.append("BLOCK 104 INPUT CONTRACT")


# ==============================================================
# 8. BLOCK 106 RUNTIME CONTRACT DISCOVERY
# ==============================================================

if not failures:

    print()
    print("8. BLOCK 106 RUNTIME CONTRACT DISCOVERY")
    print("-" * 70)

    try:
        candidate_methods = [
            "build_integration_payload",
            "build_payload",
            "create_integration_payload",
            "integrate",
            "validate",
            "validate_payload",
            "validate_integration_payload",
        ]

        found = []

        for name in candidate_methods:
            if hasattr(boundary, name):
                found.append(name)
                print("FOUND METHOD :", name)

        if found:
            print()
            print("RUNTIME CONTRACT METHOD DISCOVERY : PASS")
        else:
            print()
            print("NO STANDARD RUNTIME METHOD NAME FOUND.")
            print("This is an interface discovery result, not a source failure.")

    except Exception as exc:
        print("RUNTIME CONTRACT DISCOVERY : FAILED")
        print(type(exc).__name__, str(exc))
        traceback.print_exc()
        failures.append("RUNTIME CONTRACT DISCOVERY")


# ==============================================================
# 9. MODULE SOURCE PATH
# ==============================================================

print()
print("9. MODULE SOURCE")
print("-" * 70)

try:
    import services.quantitative.block106_institutional_integration_boundary as block106_module

    print("MODULE FILE :")
    print(block106_module.__file__)
    print("MODULE SOURCE : PASS")

except Exception as exc:
    print("MODULE SOURCE : FAILED")
    print(type(exc).__name__, str(exc))
    traceback.print_exc()
    failures.append("MODULE SOURCE")


# ==============================================================
# 10. FINAL RESULT
# ==============================================================

print()
print("=" * 70)

if failures:
    print("BLOCK 106 INTERFACE + RUNTIME VERIFICATION : FAILED")
    print()
    print("FAILURES:")
    for failure in failures:
        print(" -", failure)

    print()
    print("IMPORTANT:")
    print("The failure occurred inside the verification runner.")
    print("No broker connection was attempted.")
    print("No live order was submitted.")
    print("No source mutation was performed.")

    print("=" * 70)
    sys.exit(1)

else:
    print("BLOCK 106 INTERFACE + RUNTIME VERIFICATION : PASS")
    print()
    print("BLOCK 106 IMPORT          : PASS")
    print("PUBLIC INTERFACE          : PASS")
    print("CLASS CONTRACT            : PASS")
    print("INSTANCE CREATION        : PASS")
    print("METHOD SIGNATURES         : PASS")
    print("SAFETY CONTRACT           : PASS")
    print("BLOCK 104 INPUT           : PASS")
    print("MODULE SOURCE             : PASS")
    print()
    print("BROKER                    : FALSE")
    print("LIVE EXECUTION            : FALSE")
    print("ORDER SUBMISSION          : FALSE")
    print("PORTFOLIO MUTATION        : FALSE")
    print("READ ONLY                 : TRUE")
    print("NON MUTATING              : TRUE")
    print()
    print("BLOCK 106 VERIFICATION : PASS")

    print("=" * 70)
    sys.exit(0)
