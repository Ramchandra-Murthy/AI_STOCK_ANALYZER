from pathlib import Path
import ast
import re

adapter_path = Path(r".\services\eros_frontend_adapter.py")
source = adapter_path.read_text(encoding="utf-8-sig")

print("=" * 70)
print("EROS 3.0 - V3.8.2.3 HYDRATION SOURCE-FLOW INSPECTION")
print("=" * 70)

print()
print("1. SOURCE")
print("-" * 70)
print("SOURCE LENGTH :", len(source))
print("SOURCE LINES  :", len(source.splitlines()))

try:
    tree = ast.parse(source)
    print("AST PARSE     : PASS")
except SyntaxError as exc:
    print("AST PARSE     : FAIL")
    print("LINE          :", exc.lineno)
    print("OFFSET        :", exc.offset)
    print("MESSAGE       :", exc.msg)
    raise SystemExit(1)

print()
print("2. LOCATING EROSFrontendAdapter")
print("-" * 70)

adapter_class = None

for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name == "EROSFrontendAdapter":
        adapter_class = node
        break

if adapter_class is None:
    print("CLASS : NOT FOUND")
    raise SystemExit(2)

print("CLASS : FOUND")
print("LINE  :", adapter_class.lineno)

print()
print("3. LOCATING decision_traceability")
print("-" * 70)

trace_method = None

for node in adapter_class.body:
    if isinstance(node, ast.FunctionDef) and node.name == "decision_traceability":
        trace_method = node
        break

if trace_method is None:
    print("METHOD : NOT FOUND")
else:
    print("METHOD : FOUND")
    print("LINE   :", trace_method.lineno)
    print("END    :", trace_method.end_lineno)

print()
print("4. LOCATING decision_audit")
print("-" * 70)

audit_method = None

for node in adapter_class.body:
    if isinstance(node, ast.FunctionDef) and node.name == "decision_audit":
        audit_method = node
        break

if audit_method is None:
    print("METHOD : NOT FOUND")
    raise SystemExit(3)

print("METHOD : FOUND")
print("LINE   :", audit_method.lineno)
print("END    :", audit_method.end_lineno)

lines = source.splitlines()

print()
print("5. decision_traceability SOURCE")
print("-" * 70)

if trace_method:
    start = max(1, trace_method.lineno - 3)
    end = min(len(lines), trace_method.end_lineno)

    for number in range(start, end + 1):
        print(f"{number:5} | {lines[number-1]}")

print()
print("6. decision_audit VARIABLE ASSIGNMENTS")
print("-" * 70)

target_names = [
    "_v381_result",
    "_v381_trace",
    "_v381_audit",
    "_v382_trace_result",
    "_v382_convergence_result",
    "_v382_decision",
    "_v382_evidence_chain",
    "_v382_scenario_trace",
    "_v382_interpretation",
    "_v382_traceability",
    "_v382_primary_scenario",
    "_v382_decision_quality",
    "_v382_conclusion",
    "_v382_legacy_trace",
    "_v382_trace",
    "_v382_result",
]

audit_source = "\n".join(
    lines[audit_method.lineno-1:audit_method.end_lineno]
)

for name in target_names:
    print()
    print("VARIABLE:", name)

    matches = []

    for index, line in enumerate(
        lines[audit_method.lineno-1:audit_method.end_lineno],
        start=audit_method.lineno
    ):
        if re.search(r"\b" + re.escape(name) + r"\b", line):
            matches.append((index, line))

    if not matches:
        print("  NO REFERENCES")
    else:
        for index, line in matches:
            print(f"  {index:5} | {line}")

print()
print("7. TRACE / CONVERGENCE CALLS")
print("-" * 70)

call_patterns = [
    "decision_traceability(",
    "decision_convergence(",
    "decision_evidence(",
    "decision_intelligence(",
    "decision_interpretation(",
    "decision_action_framework(",
    "decision_action_explanation(",
    "decision_scenario_engine(",
    "decision_scenario_explanation(",
]

for pattern in call_patterns:
    print()
    print("PATTERN:", pattern)

    found = False

    for index, line in enumerate(
        lines[audit_method.lineno-1:audit_method.end_lineno],
        start=audit_method.lineno
    ):
        if pattern in line:
            print(f"{index:5} | {line}")
            found = True

    if not found:
        print("  NOT FOUND")

print()
print("8. V3.8.2 HYDRATION MARKERS")
print("-" * 70)

markers = [
    "V3.8.2",
    "V3.8.2.1",
    "V3.8.2.2",
    "_v382_trace",
    "_v382_result",
    "_v382_decision",
    "_v382_evidence_chain",
    "_v382_scenario_trace",
    "_v382_interpretation",
    "_v382_traceability",
]

for marker in markers:
    print()
    print("MARKER:", marker)

    found = False

    for index, line in enumerate(
        lines[audit_method.lineno-1:audit_method.end_lineno],
        start=audit_method.lineno
    ):
        if marker in line:
            print(f"{index:5} | {line}")
            found = True

    if not found:
        print("  NOT FOUND")

print()
print("9. RETURN STATEMENT")
print("-" * 70)

for index, line in enumerate(
    lines[audit_method.lineno-1:audit_method.end_lineno],
    start=audit_method.lineno
):
    if re.search(r"\breturn\b", line):
        print(f"{index:5} | {line}")

print()
print("10. SOURCE FLOW DIAGNOSIS")
print("-" * 70)

print("""
The runtime result showed:

    decision         = {}
    evidence_chain   = {}
    scenario_trace   = {}
    interpretation   = {}

while:

    trace            = populated
    traceability     = populated
    audit            = populated

This inspection is intentionally READ-ONLY.

No source modification is performed.
No backup is modified.
No database operation is performed.
No broker operation is performed.
No order operation is performed.
""")

print()
print("=" * 70)
print("V3.8.2.3 SOURCE-FLOW INSPECTION COMPLETE")
print("=" * 70)
