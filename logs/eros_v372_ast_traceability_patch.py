import ast
import pathlib
import sys


PROJECT_ROOT = pathlib.Path(
    r"D:\Users\User\Desktop\AI_STOCK_ANALYZER"
)

ADAPTER_PATH = (
    PROJECT_ROOT
    / "services"
    / "eros_frontend_adapter.py"
)


def fail(message: str) -> None:
    print("")
    print("AST PATCH FAILURE")
    print("-" * 60)
    print(message)
    raise SystemExit(1)


print("=" * 60)
print("EROS 3.0 - V3.7.2 AST TRACEABILITY PATCHER")
print("=" * 60)

if not ADAPTER_PATH.exists():
    fail(f"ADAPTER_NOT_FOUND:{ADAPTER_PATH}")


print("")
print("1. READING SOURCE")
print("-" * 60)

source = ADAPTER_PATH.read_text(
    encoding="utf-8"
)

print("SOURCE LENGTH :", len(source))


print("")
print("2. PARSING AST")
print("-" * 60)

try:
    tree = ast.parse(
        source,
        filename=str(ADAPTER_PATH)
    )
except SyntaxError as exc:
    fail(
        f"AST_PARSE_FAILED:"
        f"{exc}"
    )

print("AST PARSE : PASS")


print("")
print("3. LOCATING EROSFrontendAdapter")
print("-" * 60)

adapter_class = None

for node in tree.body:

    if (
        isinstance(node, ast.ClassDef)
        and node.name == "EROSFrontendAdapter"
    ):
        adapter_class = node
        break

if adapter_class is None:
    fail(
        "CLASS_NOT_FOUND:EROSFrontendAdapter"
    )

print("CLASS : FOUND")


print("")
print("4. LOCATING decision_traceability")
print("-" * 60)

method = None

for node in adapter_class.body:

    if (
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "decision_traceability"
    ):
        method = node
        break

if method is None:
    fail(
        "METHOD_NOT_FOUND:"
        "EROSFrontendAdapter.decision_traceability"
    )

print("METHOD : FOUND")
print("LINE   :", method.lineno)


print("")
print("5. LOCATING RETURN STATEMENT")
print("-" * 60)

returns = [
    node
    for node in ast.walk(method)
    if isinstance(node, ast.Return)
]

if not returns:
    fail(
        "RETURN_STATEMENT_NOT_FOUND"
    )

if len(returns) != 1:
    fail(
        "EXPECTED_EXACTLY_ONE_RETURN:"
        f"FOUND={len(returns)}"
    )

return_node = returns[0]

if return_node.value is None:
    fail(
        "RETURN_VALUE_IS_NONE"
    )

print("RETURN : FOUND")
print("RETURN LINE :", return_node.lineno)


print("")
print("6. RETURN VALUE TYPE")
print("-" * 60)

if not isinstance(return_node.value, ast.Dict):

    fail(
        "RETURN_VALUE_IS_NOT_DICT"
    )

print("RETURN DICT : PASS")


print("")
print("7. CHECKING EXISTING TRACE KEY")
print("-" * 60)

trace_key_found = False
traceability_key_found = False

for key in return_node.value.keys:

    if isinstance(key, ast.Constant):

        if key.value == "trace":
            trace_key_found = True

        if key.value == "traceability":
            traceability_key_found = True

if not trace_key_found:
    fail(
        "EXISTING_TRACE_KEY_NOT_FOUND"
    )

print('EXISTING "trace" : FOUND')

if traceability_key_found:

    print(
        'EXISTING "traceability" : FOUND'
    )

    print("")
    print("NO PATCH REQUIRED")
    sys.exit(0)


print("")
print("8. BUILDING TRACEABILITY ALIAS")
print("-" * 60)

# Build:
#
# result = {
#     existing return dictionary
# }
#
# result["traceability"] = result["trace"]
#
# return result
#
# We cannot safely insert statements into an existing Return
# without reconstructing the surrounding AST/source.
#
# Instead, transform:
#
#     return { ... }
#
# into:
#
#     return (
#         lambda __eros_result:
#             (
#                 __eros_result.__setitem__(
#                     "traceability",
#                     __eros_result["trace"]
#                 )
#                 or __eros_result
#             )
#     )({ ... })
#
# This evaluates the original dictionary exactly once.


original_dict = return_node.value


lambda_arg = ast.arg(
    arg="__eros_result"
)

lambda_body = ast.BoolOp(
    op=ast.Or(),
    values=[
        ast.Call(
            func=ast.Attribute(
                value=ast.Name(
                    id="__eros_result",
                    ctx=ast.Load()
                ),
                attr="__setitem__",
                ctx=ast.Load()
            ),
            args=[
                ast.Constant(
                    value="traceability"
                ),
                ast.Subscript(
                    value=ast.Name(
                        id="__eros_result",
                        ctx=ast.Load()
                    ),
                    slice=ast.Constant(
                        value="trace"
                    ),
                    ctx=ast.Load()
                )
            ],
            keywords=[]
        ),
        ast.Name(
            id="__eros_result",
            ctx=ast.Load()
        )
    ]
)


lambda_node = ast.Lambda(
    args=ast.arguments(
        posonlyargs=[],
        args=[lambda_arg],
        kwonlyargs=[],
        kw_defaults=[],
        defaults=[]
    ),
    body=lambda_body
)


new_call = ast.Call(
    func=lambda_node,
    args=[original_dict],
    keywords=[]
)


return_node.value = new_call


ast.fix_missing_locations(tree)


print("TRACEABILITY ALIAS : PREPARED")


print("")
print("9. GENERATING SOURCE")
print("-" * 60)

try:
    new_source = ast.unparse(tree)
except Exception as exc:

    fail(
        f"AST_UNPARSE_FAILED:{exc}"
    )


print(
    "GENERATED SOURCE LENGTH :",
    len(new_source)
)


print("")
print("10. SOURCE SAFETY CHECK")
print("-" * 60)

if "decision_traceability" not in new_source:
    fail(
        "TRACEABILITY_METHOD_LOST"
    )

if '"traceability"' not in new_source:
    fail(
        "TRACEABILITY_KEY_NOT_GENERATED"
    )

if '"trace"' not in new_source:
    fail(
        "LEGACY_TRACE_KEY_LOST"
    )

print("TRACEABILITY METHOD : PRESENT")
print('TRACEABILITY KEY    : PRESENT')
print('LEGACY TRACE KEY    : PRESENT')


print("")
print("11. WRITING PATCHED SOURCE")
print("-" * 60)

ADAPTER_PATH.write_text(
    new_source + "\n",
    encoding="utf-8",
    newline="\n"
)

print("SOURCE WRITE : PASS")


print("")
print("12. FINAL AST PARSE")
print("-" * 60)

try:

    final_source = ADAPTER_PATH.read_text(
        encoding="utf-8"
    )

    ast.parse(
        final_source,
        filename=str(ADAPTER_PATH)
    )

except SyntaxError as exc:

    fail(
        f"FINAL_AST_PARSE_FAILED:{exc}"
    )

print("FINAL AST PARSE : PASS")


print("")
print("=" * 60)
print("AST PATCH COMPLETE")
print("=" * 60)
print("SOURCE PATCH : PASS")
print("TRACEABILITY  : PRESENT")
print("LEGACY TRACE  : PRESERVED")
print("=" * 60)