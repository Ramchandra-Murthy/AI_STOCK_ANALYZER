from pathlib import Path
import ast
import shutil
import sys


PROJECT_ROOT = Path(r"D:\Users\User\Desktop\AI_STOCK_ANALYZER")
ADAPTER = PROJECT_ROOT / "services" / "eros_frontend_adapter.py"


print("=" * 60)
print("EROS 3.0 - V3.8.2 DECISION AUDIT INTEGRITY PATCHER")
print("=" * 60)


print("\n1. SOURCE")
print("-" * 60)

source = ADAPTER.read_text(encoding="utf-8")

print("SOURCE LENGTH :", len(source))


print("\n2. AST PARSE")
print("-" * 60)

try:
    tree = ast.parse(source)
except Exception as exc:
    print("AST PARSE : FAIL")
    print(type(exc).__name__, str(exc))
    raise SystemExit(10)

print("AST PARSE : PASS")


print("\n3. LOCATING EROSFrontendAdapter")
print("-" * 60)

adapter_class = None

for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name == "EROSFrontendAdapter":
        adapter_class = node
        break

if adapter_class is None:
    print("CLASS : NOT FOUND")
    raise SystemExit(11)

print("CLASS : FOUND")


print("\n4. LOCATING decision_audit")
print("-" * 60)

audit_method = None

for node in adapter_class.body:
    if isinstance(node, ast.FunctionDef) and node.name == "decision_audit":
        audit_method = node
        break

if audit_method is None:
    print("decision_audit : NOT FOUND")
    raise SystemExit(12)

print("decision_audit : FOUND")
print("LINE :", audit_method.lineno)


print("\n5. INSPECTING METHOD SOURCE")
print("-" * 60)

method_lines = source.splitlines()

method_start = audit_method.lineno - 1
method_end = audit_method.end_lineno

method_text = "\n".join(
    method_lines[method_start:method_end]
)

print("METHOD LENGTH :", len(method_text))


print("\n6. EXISTING V3.8.1 NORMALIZATION")
print("-" * 60)

checks = [
    "_v381_result",
    "_v381_audit",
    "_v381_trace",
    "_v381_traceability",
    "_v381_conclusion",
]

for token in checks:
    print(
        f"{token:35} : "
        f"{'PRESENT' if token in method_text else 'ABSENT'}"
    )


print("\n7. INTEGRITY ANALYSIS")
print("-" * 60)

required_sources = [
    "decision_traceability",
    "decision_convergence",
    "decision_interpretation",
    "decision_evidence",
    "decision_intelligence",
]

for token in required_sources:
    print(
        f"{token:35} : "
        f"{'PRESENT' if token in method_text else 'NOT_DIRECTLY_REFERENCED'}"
    )


print("\n8. PATCH SAFETY")
print("-" * 60)

print("The patch will NOT alter:")
print(" - decision calculations")
print(" - evidence calculations")
print(" - scenario calculations")
print(" - convergence calculations")
print(" - governance")
print(" - execution controls")
print(" - database behavior")


print("\n9. PATCH STRATEGY")
print("-" * 60)

print(
    "V3.8.2 integrity correction requires the audit result "
    "to preserve the full traceability payload instead of "
    "creating an empty normalized decision/traceability shell."
)

print(
    "\nThe runtime diagnostic will identify the exact "
    "normalization defect before modifying source."
)


print("\n10. PATCHER STATUS")
print("-" * 60)

print("AST inspection : PASS")
print("METHOD located : PASS")
print("NO SOURCE WRITE PERFORMED")
print("")
print("PATCHER RESULT : INSPECTION_ONLY")


print("=" * 60)