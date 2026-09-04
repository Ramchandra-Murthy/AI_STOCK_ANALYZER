import ast
from pathlib import Path

SOURCE = Path(r"D:\Users\User\Desktop\AI_STOCK_ANALYZER\services\eros_frontend_adapter.py")

print("=" * 60)
print("EROS 3.0 - V3.7.2 RETURN STRUCTURE DIAGNOSTIC")
print("=" * 60)

source = SOURCE.read_text(encoding="utf-8")

print("\n1. SOURCE")
print("-" * 60)
print("SOURCE :", SOURCE)
print("LENGTH :", len(source))

print("\n2. AST PARSE")
print("-" * 60)

tree = ast.parse(source)

print("AST PARSE : PASS")

print("\n3. LOCATING CLASS")
print("-" * 60)

adapter_class = None

for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name == "EROSFrontendAdapter":
        adapter_class = node
        break

if adapter_class is None:
    raise RuntimeError("EROS_FRONTEND_ADAPTER_CLASS_NOT_FOUND")

print("CLASS : FOUND")
print("LINE  :", adapter_class.lineno)

print("\n4. LOCATING METHOD")
print("-" * 60)

method = None

for node in adapter_class.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name == "decision_traceability":
            method = node
            break

if method is None:
    raise RuntimeError("DECISION_TRACEABILITY_NOT_FOUND")

print("METHOD : FOUND")
print("START  :", method.lineno)
print("END    :", getattr(method, "end_lineno", "UNKNOWN"))

print("\n5. METHOD SOURCE")
print("-" * 60)

lines = source.splitlines()

start = max(method.lineno - 5, 1)
end = min(getattr(method, "end_lineno", method.lineno + 250), len(lines))

for number in range(start, end + 1):
    print(f"{number:5}: {lines[number - 1]}")

print("\n6. RETURN STATEMENTS")
print("-" * 60)

returns = [
    node
    for node in ast.walk(method)
    if isinstance(node, ast.Return)
]

print("RETURN COUNT :", len(returns))

if not returns:
    raise RuntimeError("NO_RETURN_FOUND")

for index, ret in enumerate(returns, 1):

    print("")
    print(f"RETURN #{index}")
    print("-" * 60)

    print("LINE :", ret.lineno)
    print("COL  :", ret.col_offset)

    if ret.value is None:
        print("VALUE : None")
        continue

    print("AST TYPE :", type(ret.value).__name__)

    print(
        "AST DUMP :",
        ast.dump(
            ret.value,
            indent=2,
            include_attributes=False
        )
    )

    try:
        segment = ast.get_source_segment(source, ret.value)
    except Exception:
        segment = None

    print("")
    print("SOURCE SEGMENT:")
    print(segment)

print("\n7. RETURN DICTIONARY ANALYSIS")
print("-" * 60)

for index, ret in enumerate(returns, 1):

    print("")
    print(f"RETURN #{index}")

    value = ret.value

    if isinstance(value, ast.Dict):

        print("RETURN VALUE : DIRECT DICT")
        print("KEY COUNT    :", len(value.keys))

        for key, val in zip(value.keys, value.values):

            if isinstance(key, ast.Constant):
                print(
                    "KEY:",
                    repr(key.value),
                    "VALUE_TYPE:",
                    type(val).__name__
                )
            else:
                print(
                    "KEY: <NON-CONSTANT>",
                    "VALUE_TYPE:",
                    type(val).__name__
                )

    elif isinstance(value, ast.Name):

        print("RETURN VALUE : VARIABLE")
        print("VARIABLE     :", value.id)

    elif isinstance(value, ast.Call):

        print("RETURN VALUE : FUNCTION CALL")
        print("CALL         :", ast.dump(
            value,
            include_attributes=False
        ))

    else:

        print("RETURN VALUE : OTHER")
        print("TYPE         :", type(value).__name__)

print("\n8. TRACE KEY SEARCH")
print("-" * 60)

for index, ret in enumerate(returns, 1):

    print("")
    print(f"RETURN #{index}")

    for node in ast.walk(ret):

        if isinstance(node, ast.Constant):

            if node.value in (
                "trace",
                "traceability",
                "evidence_chain",
                "scenario_trace"
            ):
                print(
                    "FOUND KEY:",
                    repr(node.value),
                    "AT LINE:",
                    node.lineno
                )

print("\n============================================================")
print("V3.7.2 RETURN STRUCTURE DIAGNOSTIC")
print("============================================================")

print("AST PARSE       : PASS")
print("CLASS           : FOUND")
print("METHOD          : FOUND")
print("RETURN          : FOUND")
print("SOURCE UNCHANGED: TRUE")

print("============================================================")