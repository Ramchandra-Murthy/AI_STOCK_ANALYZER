import importlib
import inspect
import ast
import textwrap
from pathlib import Path

BASE = Path.cwd()

modules = [
    (
        94,
        "services.quantitative.block94_portfolio_stress_scenario_engine",
        "block94_portfolio_stress_scenario_engine.py",
    ),
    (
        95,
        "services.quantitative.block95_stress_evidence_gate",
        "block95_stress_evidence_gate.py",
    ),
    (
        96,
        "services.quantitative.block96_stress_decision_gate",
        "block96_stress_decision_gate.py",
    ),
    (
        97,
        "services.quantitative.block97_stress_readiness_gate",
        "block97_stress_readiness_gate.py",
    ),
    (
        98,
        "services.quantitative.block98_execution_governance_bridge",
        "block98_execution_governance_bridge.py",
    ),
    (
        99,
        "services.quantitative.block99_execution_intent_authorization_gate",
        "block99_execution_intent_authorization_gate.py",
    ),
    (
        100,
        "services.quantitative.block100_paper_execution_fill_gate",
        "block100_paper_execution_fill_gate.py",
    ),
    (
        101,
        "services.quantitative.block101_execution_evidence_reconciliation.py",
        "block101_execution_evidence_reconciliation.py",
    ),
]

SAFETY_FIELDS = [
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

METHOD_NAMES = [
    "certify",
    "gate",
    "decide",
    "evaluate",
    "govern",
    "authorize",
    "stress_portfolio",
    "run_scenario",
    "run_scenarios",
]

def print_source_context(path, method_name, cls_name):
    print()
    print("-" * 80)
    print(f"SOURCE CONTEXT : {path}")
    print(f"CLASS          : {cls_name}")
    print(f"METHOD         : {method_name}")
    print("-" * 80)

    try:
        source = path.read_text(encoding="utf-8")
    except Exception as exc:
        print("SOURCE READ : FAIL")
        print(type(exc).__name__, str(exc))
        return

    try:
        tree = ast.parse(source)
    except Exception as exc:
        print("AST PARSE : FAIL")
        print(type(exc).__name__, str(exc))
        return

    target = None

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name != method_name:
                continue

            # Keep only the requested class method where possible.
            target = node
            break

    if target is None:
        print("METHOD SOURCE : NOT FOUND")
        return

    lines = source.splitlines()

    start = max(0, target.lineno - 8)
    end = min(len(lines), getattr(target, "end_lineno", target.lineno) + 8)

    print()
    print(f"SOURCE LINES {start + 1} -> {end}")
    print()

    for number in range(start, end):
        print(f"{number + 1:5} | {lines[number]}")

def inspect_ast_safety(path):
    print()
    print("-" * 80)
    print("AST SAFETY KEY ANALYSIS")
    print("-" * 80)

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as exc:
        print("AST ANALYSIS : FAIL")
        print(type(exc).__name__, str(exc))
        return

    discovered = {}

    for field in SAFETY_FIELDS:
        discovered[field] = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Dict):

            for key_node, value_node in zip(node.keys, node.values):

                if isinstance(key_node, ast.Constant):
                    key = key_node.value

                    if key in SAFETY_FIELDS:
                        try:
                            value_repr = ast.unparse(value_node)
                        except Exception:
                            value_repr = "<unavailable>"

                        discovered[key].append(value_repr)

    for field in SAFETY_FIELDS:
        values = discovered[field]

        if values:
            print(f"{field:28} : FOUND")
            for value in values:
                print(f"    VALUE EXPRESSION          : {value}")
        else:
            print(f"{field:28} : NOT FOUND")

def inspect_method_returns(cls, instance):
    print()
    print("-" * 80)
    print("RUNTIME METHOD RETURN INSPECTION")
    print("-" * 80)

    for method_name in METHOD_NAMES:

        if not hasattr(instance, method_name):
            continue

        method = getattr(instance, method_name)

        print()
        print("METHOD :", method_name)

        try:
            signature = inspect.signature(method)
            print("SIGNATURE :", signature)
        except Exception:
            print("SIGNATURE : <unavailable>")

        # We deliberately do NOT invoke methods requiring business inputs.
        if method_name not in ["snapshot", "certificate_history", "scenario_history"]:
            print("INVOCATION : SKIPPED")
            print("REASON     : requires contract/business input")
            continue

        try:
            result = method()

            print("INVOCATION : PASS")
            print("RETURN TYPE:", type(result))

            if isinstance(result, dict):

                print("TOP LEVEL KEYS:")
                for key in result.keys():
                    print(f"  {key}")

                print()
                print("SAFETY FIELDS:")

                for field in SAFETY_FIELDS:
                    if field in result:
                        print(
                            f"  {field:28} : "
                            f"{result[field]!r}"
                        )
                    else:
                        print(
                            f"  {field:28} : "
                            "<ABSENT>"
                        )

                if isinstance(result.get("safety"), dict):

                    print()
                    print("NESTED safety OBJECT:")

                    for key, value in result["safety"].items():
                        print(f"  {key:28} : {value!r}")

        except Exception as exc:
            print("INVOCATION : ERROR")
            print(type(exc).__name__, str(exc))

def inspect_module(block_number, module_name, filename):

    print()
    print("=" * 80)
    print(f"BLOCK {block_number}")
    print("=" * 80)

    print("MODULE :", module_name)
    print("FILE   :", filename)

    path = BASE / "services" / "quantitative" / filename

    print("PATH   :", path)

    if not path.exists():
        print("SOURCE FILE : NOT FOUND")
        return

    print("SOURCE FILE : FOUND")
    print("SOURCE SIZE :", path.stat().st_size)

    try:
        module = importlib.import_module(module_name)
        print("IMPORT      : PASS")
    except Exception as exc:
        print("IMPORT      : FAIL")
        print(type(exc).__name__, str(exc))
        return

    classes = [
        cls
        for name, cls in vars(module).items()
        if isinstance(cls, type)
        and getattr(cls, "__module__", None) == module_name
        and name.startswith("EROSBlock")
    ]

    if not classes:
        print("EROS CLASS  : NOT FOUND")
        return

    for cls in classes:

        print()
        print("CLASS :", cls.__name__)

        try:
            instance = cls()
            print("INSTANCE : PASS")
        except Exception as exc:
            print("INSTANCE : FAIL")
            print(type(exc).__name__, str(exc))
            continue

        inspect_method_returns(cls, instance)

        inspect_ast_safety(path)

        for method_name in METHOD_NAMES:

            if not hasattr(cls, method_name):
                continue

            try:
                method = getattr(cls, method_name)

                if not inspect.isfunction(method):
                    continue

                print_source_context(
                    path,
                    method_name,
                    cls.__name__,
                )

            except Exception as exc:
                print()
                print(
                    f"SOURCE CONTEXT ERROR : "
                    f"{method_name}"
                )
                print(type(exc).__name__, str(exc))

print("=" * 80)
print("EROS 3.0 - BLOCK 94-101 SAFETY CONTRACT CONSTRUCTION AUDIT")
print("=" * 80)

for block_number, module_name, filename in modules:
    inspect_module(
        block_number,
        module_name,
        filename,
    )

print()
print("=" * 80)
print("FINAL CONTRACT COMPARISON")
print("=" * 80)

print()
print("EXPECTED HARD SAFETY SCHEMA")
print()

for field in SAFETY_FIELDS:
    print(f"  {field}")

print()
print("INTERPRETATION")
print()
print("94-97 : currently diagnostic targets")
print("98-101: currently known-good safety contract pattern")
print()
print("This audit identifies where the safety contract is constructed.")
print("It does NOT modify any source file.")
print()
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print()
print("=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
