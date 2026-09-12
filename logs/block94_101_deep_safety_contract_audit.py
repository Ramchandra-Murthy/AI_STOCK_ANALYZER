import ast
import importlib
from pathlib import Path

ROOT = Path.cwd()

MODULES = [
    (
        "94",
        "services.quantitative.block94_portfolio_stress_scenario_engine",
        ROOT / "services/quantitative/block94_portfolio_stress_scenario_engine.py",
    ),
    (
        "95",
        "services.quantitative.block95_stress_evidence_gate",
        ROOT / "services/quantitative/block95_stress_evidence_gate.py",
    ),
    (
        "96",
        "services.quantitative.block96_stress_decision_gate",
        ROOT / "services/quantitative/block96_stress_decision_gate.py",
    ),
    (
        "97",
        "services.quantitative.block97_stress_readiness_gate",
        ROOT / "services/quantitative/block97_stress_readiness_gate.py",
    ),
    (
        "98",
        "services.quantitative.block98_execution_governance_bridge",
        ROOT / "services/quantitative/block98_execution_governance_bridge.py",
    ),
    (
        "99",
        "services.quantitative.block99_execution_intent_authorization_gate",
        ROOT / "services/quantitative/block99_execution_intent_authorization_gate.py",
    ),
    (
        "100",
        "services.quantitative.block100_paper_execution_fill_gate",
        ROOT / "services/quantitative/block100_paper_execution_fill_gate.py",
    ),
    (
        "101",
        "services.quantitative.block101_execution_evidence_reconciliation",
        ROOT / "services/quantitative/block101_execution_evidence_reconciliation.py",
    ),
]

EXPECTED_SAFETY_KEYS = [
    "execution_blocked",
    "non_mutation_invariant",
    "broker_submission",
    "live_order_submission",
    "portfolio_mutation",
    "valuation_mutation",
    "performance_mutation",
    "risk_mutation",
    "optimization",
    "order_creation",
]

print("=" * 90)
print("EROS 3.0 - BLOCK 94-101 DEEP SAFETY CONTRACT AUDIT")
print("=" * 90)

overall_imports = True
overall_ast = True
overall_safety_mentions = True

for block_id, module_name, source_path in MODULES:

    print()
    print("=" * 90)
    print(f"BLOCK {block_id}")
    print("=" * 90)

    print("MODULE :", module_name)
    print("FILE   :", source_path)
    print("EXISTS :", source_path.exists())

    if not source_path.exists():
        print("SOURCE : FAIL - FILE NOT FOUND")
        overall_ast = False
        continue

    # ------------------------------------------------------------
    # IMPORT TEST
    # ------------------------------------------------------------
    try:
        module = importlib.import_module(module_name)
        print("IMPORT : PASS")
    except Exception as exc:
        print("IMPORT : FAIL")
        print(type(exc).__name__, str(exc))
        overall_imports = False
        continue

    # ------------------------------------------------------------
    # SOURCE READ
    # ------------------------------------------------------------
    try:
        raw_text = source_path.read_text(encoding="utf-8-sig")

        print("SOURCE READ : PASS")
        print("SOURCE SIZE :", len(raw_text))

    except Exception as exc:
        print("SOURCE READ : FAIL")
        print(type(exc).__name__, str(exc))
        overall_ast = False
        continue

    # ------------------------------------------------------------
    # BOM CHECK
    # ------------------------------------------------------------
    try:
        raw_bytes = source_path.read_bytes()

        if raw_bytes.startswith(b"\xef\xbb\xbf"):
            print("UTF-8 BOM : PRESENT")
            print("AST MODE  : BOM STRIPPED IN MEMORY ONLY")
        else:
            print("UTF-8 BOM : NOT PRESENT")

    except Exception as exc:
        print("BOM CHECK ERROR")
        print(type(exc).__name__, str(exc))

    # ------------------------------------------------------------
    # AST PARSE
    # ------------------------------------------------------------
    try:
        tree = ast.parse(raw_text)
        print("AST PARSE : PASS")
    except Exception as exc:
        print("AST PARSE : FAIL")
        print(type(exc).__name__, str(exc))
        overall_ast = False
        continue

    # ------------------------------------------------------------
    # SAFETY KEY SEARCH
    # ------------------------------------------------------------
    print()
    print("SAFETY KEY SOURCE TRACE")
    print("-" * 90)

    missing_keys = []

    for key in EXPECTED_SAFETY_KEYS:

        found = key in raw_text

        print(f"{key:28} : " f"{'FOUND' if found else 'ABSENT'}")

        if not found:
            missing_keys.append(key)

    if missing_keys:
        overall_safety_mentions = False

    # ------------------------------------------------------------
    # CLASS INSPECTION
    # ------------------------------------------------------------
    print()
    print("EROS CLASSES")
    print("-" * 90)

    found_class = False

    for class_name, cls in vars(module).items():

        if not isinstance(cls, type):
            continue

        if getattr(cls, "__module__", None) != module_name:
            continue

        if not class_name.startswith("EROSBlock"):
            continue

        found_class = True

        print()
        print("CLASS :", class_name)

        try:
            instance = cls()
            print("INSTANCE : PASS")
        except Exception as exc:
            print("INSTANCE : FAIL")
            print(type(exc).__name__, str(exc))
            continue

        # --------------------------------------------------------
        # SNAPSHOT
        # --------------------------------------------------------
        if hasattr(instance, "snapshot"):

            try:
                snapshot = instance.snapshot()

                print()
                print("SNAPSHOT : PASS")
                print("TYPE     :", type(snapshot))

                if isinstance(snapshot, dict):
                    print("SNAPSHOT KEYS:")

                    for key in snapshot.keys():
                        print("  ", key)

                    print()
                    print("SAFETY FIELDS IN SNAPSHOT:")

                    for key in EXPECTED_SAFETY_KEYS:
                        if key in snapshot:
                            print(f"  {key:26} : " f"{snapshot[key]!r}")
                        else:
                            print(f"  {key:26} : <ABSENT>")

                    if isinstance(snapshot.get("safety"), dict):

                        print()
                        print("NESTED SAFETY OBJECT:")

                        for key, value in snapshot["safety"].items():
                            print(f"  {key:26} : {value!r}")

            except Exception as exc:

                print()
                print("SNAPSHOT : ERROR")
                print(type(exc).__name__, str(exc))

    if not found_class:
        print("NO EROS CLASS FOUND")

    # ------------------------------------------------------------
    # AST CONSTANT / STRING TRACE
    # ------------------------------------------------------------
    print()
    print("SAFETY-RELATED AST STRING LITERALS")
    print("-" * 90)

    safety_literals = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Constant):
            value = node.value

            if isinstance(value, str):

                if any(key.lower() in value.lower() for key in EXPECTED_SAFETY_KEYS):
                    safety_literals.append(value)

    unique_literals = list(dict.fromkeys(safety_literals))

    if unique_literals:

        for value in unique_literals[:100]:
            print(" ", repr(value))

    else:
        print("NONE FOUND")

    # ------------------------------------------------------------
    # BLOCK SUMMARY
    # ------------------------------------------------------------
    print()
    print("BLOCK SUMMARY")
    print("-" * 90)
    print("IMPORT              : PASS")
    print("AST                 : PASS")
    print("SAFETY KEY MENTIONS : " + ("PASS" if not missing_keys else "INCOMPLETE"))

    if missing_keys:
        print("MISSING SOURCE KEYS :", missing_keys)
    else:
        print("MISSING SOURCE KEYS : NONE")


# ==================================================================
# FINAL SUMMARY
# ==================================================================

print()
print("=" * 90)
print("FINAL EROS 3.0 SAFETY CONTRACT AUDIT")
print("=" * 90)

print("IMPORTS              : " + ("PASS" if overall_imports else "FAIL"))

print("AST PARSING          : " + ("PASS" if overall_ast else "FAIL"))

print("SAFETY KEY PRESENCE  : " + ("PASS" if overall_safety_mentions else "INCOMPLETE"))

print()
print("EXPECTED HARD SAFETY SCHEMA")
print("-" * 90)

for key in EXPECTED_SAFETY_KEYS:
    print(" ", key)

print()
print("SAFETY BOUNDARY")
print("-" * 90)
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO PORTFOLIO MUTATION")
print("NO VALUATION MUTATION")
print("NO PERFORMANCE MUTATION")
print("NO RISK MUTATION")
print("NO OPTIMIZATION")
print("READ ONLY AUDIT")
print("NO SOURCE CHANGES")

print()
print("=" * 90)
print("DEEP SAFETY CONTRACT AUDIT COMPLETE")
print("=" * 90)
