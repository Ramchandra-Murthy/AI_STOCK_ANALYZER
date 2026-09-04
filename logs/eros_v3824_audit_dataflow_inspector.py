from __future__ import annotations

import ast
import inspect
import sys
import os
import traceback

PROJECT_ROOT = r"D:\Users\User\Desktop\AI_STOCK_ANALYZER"
ADAPTER_PATH = os.path.join(
    PROJECT_ROOT,
    "services",
    "eros_frontend_adapter.py",
)

print("=" * 78)
print("EROS 3.0 - V3.8.2.4 AUDIT DATAFLOW INSPECTOR")
print("=" * 78)

print()
print("1. ENVIRONMENT")
print("-" * 78)
print("PYTHON :", sys.version)
print("ROOT   :", PROJECT_ROOT)
print("EXISTS :", os.path.isdir(PROJECT_ROOT))
print("ADAPTER:", ADAPTER_PATH)
print("EXISTS :", os.path.isfile(ADAPTER_PATH))

# ------------------------------------------------------------
# FORCE PROJECT ROOT INTO IMPORT PATH
# ------------------------------------------------------------

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print()
print("2. IMPORT PATH")
print("-" * 78)
print("SYS.PATH[0] :", sys.path[0])
print("ROOT IN PATH:", PROJECT_ROOT in sys.path)

# ------------------------------------------------------------
# SOURCE READ
# ------------------------------------------------------------

try:
    with open(ADAPTER_PATH, "r", encoding="utf-8-sig") as f:
        source = f.read()

    print()
    print("3. SOURCE")
    print("-" * 78)
    print("SOURCE LENGTH :", len(source))
    print("SOURCE LINES  :", len(source.splitlines()))

except Exception as exc:
    print("SOURCE READ FAILED")
    print(repr(exc))
    raise SystemExit(1)

# ------------------------------------------------------------
# AST ANALYSIS
# ------------------------------------------------------------

try:
    tree = ast.parse(source)
    print("AST PARSE     : PASS")
except Exception as exc:
    print("AST PARSE     : FAIL")
    print(type(exc).__name__, str(exc))
    raise SystemExit(1)

# ------------------------------------------------------------
# LOCATE CLASS / METHOD
# ------------------------------------------------------------

adapter_class = None
audit_method = None
trace_method = None
convergence_method = None

for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name == "EROSFrontendAdapter":
        adapter_class = node

if adapter_class is None:
    print("EROSFrontendAdapter : NOT FOUND")
    raise SystemExit(1)

for node in adapter_class.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name == "decision_audit":
            audit_method = node
        elif node.name == "decision_traceability":
            trace_method = node
        elif node.name == "decision_convergence":
            convergence_method = node

print()
print("4. METHOD LOCATIONS")
print("-" * 78)

for name, node in [
    ("decision_traceability", trace_method),
    ("decision_convergence", convergence_method),
    ("decision_audit", audit_method),
]:
    if node is None:
        print(f"{name:35} : NOT FOUND")
    else:
        print(
            f"{name:35} : line {node.lineno} -> {getattr(node, 'end_lineno', '?')}"
        )

if audit_method is None:
    raise SystemExit(1)

# ------------------------------------------------------------
# SOURCE EXTRACTOR
# ------------------------------------------------------------

lines = source.splitlines()

def print_source_range(start, end, title):
    print()
    print(title)
    print("-" * 78)

    start = max(1, start)
    end = min(len(lines), end)

    for n in range(start, end + 1):
        print(f"{n:5d} | {lines[n-1]}")

# ------------------------------------------------------------
# DECISION AUDIT SOURCE
# ------------------------------------------------------------

audit_start = audit_method.lineno
audit_end = getattr(audit_method, "end_lineno", audit_start)

print()
print("5. DECISION_AUDIT SOURCE RANGE")
print("-" * 78)
print("START :", audit_start)
print("END   :", audit_end)
print("LINES :", audit_end - audit_start + 1)

# ------------------------------------------------------------
# FIND IMPORTANT DATAFLOW SYMBOLS
# ------------------------------------------------------------

symbols = [
    "_v381_result",
    "_v381_trace",
    "_v381_traceability",
    "_v381_evidence_chain",
    "_v381_scenario_trace",
    "_v381_interpretation",
    "_v381_audit",
    "_v382_result",
    "_v382_trace_result",
    "_v382_traceability",
    "_v382_evidence_chain",
    "_v382_scenario_trace",
    "_v382_interpretation",
    "_v382_decision",
    "_v382_legacy_trace",
    "_v382_convergence_result",
    "_v382_primary_scenario",
    "_v382_decision_quality",
]

print()
print("6. DATAFLOW SYMBOL OCCURRENCES")
print("-" * 78)

audit_text = "\n".join(lines[audit_start - 1:audit_end])

for symbol in symbols:
    occurrences = []
    for i in range(audit_start, audit_end + 1):
        if symbol in lines[i - 1]:
            occurrences.append(i)

    print(f"{symbol:35} : {len(occurrences)}")
    if occurrences:
        print(" " * 37 + "LINES:", occurrences[:30])

# ------------------------------------------------------------
# AST ASSIGNMENTS
# ------------------------------------------------------------

print()
print("7. AST ASSIGNMENTS / DATA SOURCES")
print("-" * 78)

interesting = set(symbols)

class AssignmentVisitor(ast.NodeVisitor):
    def __init__(self):
        self.items = []

    def visit_Assign(self, node):
        targets = []

        for target in node.targets:
            if isinstance(target, ast.Name):
                targets.append(target.id)

        for target in targets:
            if target in interesting:
                try:
                    value = ast.unparse(node.value)
                except Exception:
                    value = "<unparse failed>"

                self.items.append(
                    (
                        node.lineno,
                        target,
                        value,
                    )
                )

        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if isinstance(node.target, ast.Name):
            target = node.target.id

            if target in interesting:
                try:
                    value = ast.unparse(node.value) if node.value else "<none>"
                except Exception:
                    value = "<unparse failed>"

                self.items.append(
                    (
                        node.lineno,
                        target,
                        value,
                    )
                )

        self.generic_visit(node)

visitor = AssignmentVisitor()
visitor.visit(audit_method)

for lineno, target, value in visitor.items:
    print()
    print("LINE   :", lineno)
    print("TARGET :", target)
    print("VALUE  :", value[:1200])

# ------------------------------------------------------------
# CALL ANALYSIS
# ------------------------------------------------------------

print()
print("8. INTERNAL METHOD CALLS")
print("-" * 78)

class CallVisitor(ast.NodeVisitor):
    def __init__(self):
        self.calls = []

    def visit_Call(self, node):
        try:
            call_text = ast.unparse(node)
        except Exception:
            call_text = "<unparse failed>"

        if "self." in call_text:
            self.calls.append(
                (
                    node.lineno,
                    call_text,
                )
            )

        self.generic_visit(node)

call_visitor = CallVisitor()
call_visitor.visit(audit_method)

for lineno, call in call_visitor.calls:
    print()
    print("LINE :", lineno)
    print("CALL :", call[:1600])

# ------------------------------------------------------------
# RETURN ANALYSIS
# ------------------------------------------------------------

print()
print("9. RETURN ANALYSIS")
print("-" * 78)

class ReturnVisitor(ast.NodeVisitor):
    def __init__(self):
        self.returns = []

    def visit_Return(self, node):
        try:
            value = ast.unparse(node.value) if node.value else "<none>"
        except Exception:
            value = "<unparse failed>"

        self.returns.append(
            (
                node.lineno,
                value,
            )
        )

return_visitor = ReturnVisitor()
return_visitor.visit(audit_method)

for lineno, value in return_visitor.returns:
    print()
    print("RETURN LINE :", lineno)
    print("RETURN VALUE:")
    print(value[:6000])

# ------------------------------------------------------------
# CRITICAL SOURCE WINDOWS
# ------------------------------------------------------------

print_source_range(
    max(audit_start, audit_end - 1150),
    audit_end,
    "10. FINAL DECISION_AUDIT SOURCE WINDOW",
)

# ------------------------------------------------------------
# RUNTIME EXECUTION
# ------------------------------------------------------------

print()
print("11. RUNTIME DATAFLOW EXECUTION")
print("-" * 78)

try:
    from services.eros_frontend_adapter import EROSFrontendAdapter

    adapter = EROSFrontendAdapter()

    symbol = "RELIANCE.NS"

    print("IMPORT        : PASS")
    print("ADAPTER       : PASS")
    print("SYMBOL        :", symbol)

    # First get the known-good traceability result.
    trace_result = adapter.decision_traceability(symbol)

    print()
    print("TRACEABILITY")
    print("TYPE          :", type(trace_result).__name__)
    print("DICT          :", isinstance(trace_result, dict))

    if isinstance(trace_result, dict):
        print("KEYS          :", list(trace_result.keys()))

        for key in [
            "decision",
            "trace",
            "traceability",
            "evidence_chain",
            "scenario_trace",
            "interpretation",
            "conclusion",
        ]:
            value = trace_result.get(key)
            print(
                f"{key:35} : "
                f"{'POPULATED' if value else 'EMPTY'} "
                f"type={type(value).__name__}"
            )

    # Then execute audit.
    audit_result = adapter.decision_audit(symbol)

    print()
    print("AUDIT")
    print("TYPE          :", type(audit_result).__name__)
    print("DICT          :", isinstance(audit_result, dict))

    if isinstance(audit_result, dict):
        print("KEYS          :", list(audit_result.keys()))

        for key in [
            "decision",
            "audit",
            "audit_findings",
            "trace",
            "traceability",
            "evidence_chain",
            "scenario_trace",
            "interpretation",
            "conclusion",
            "traceability_status",
            "audit_summary",
            "audit_status",
            "governance",
        ]:
            value = audit_result.get(key)

            print(
                f"{key:35} : "
                f"{'POPULATED' if value else 'EMPTY'} "
                f"type={type(value).__name__}"
            )

        print()
        print("AUDIT DECISION OBJECT")
        print("-" * 78)
        print(repr(audit_result.get("decision")))

        print()
        print("AUDIT TRACEABILITY")
        print("-" * 78)
        print(repr(audit_result.get("traceability")))

        print()
        print("AUDIT EVIDENCE CHAIN")
        print("-" * 78)
        print(repr(audit_result.get("evidence_chain")))

        print()
        print("AUDIT SCENARIO TRACE")
        print("-" * 78)
        print(repr(audit_result.get("scenario_trace")))

        print()
        print("AUDIT INTERPRETATION")
        print("-" * 78)
        print(repr(audit_result.get("interpretation")))

except Exception:
    print()
    print("RUNTIME EXCEPTION")
    print("-" * 78)
    traceback.print_exc()

# ------------------------------------------------------------
# FINAL CLASSIFICATION
# ------------------------------------------------------------

print()
print("=" * 78)
print("V3.8.2.4 DATAFLOW INSPECTION COMPLETE")
print("=" * 78)

print()
print("IMPORTANT:")
print("NO SOURCE PATCH PERFORMED")
print("NO DATABASE WRITE")
print("NO BROKER CALL")
print("NO ORDER CREATION")
print("NO PORTFOLIO MUTATION")
print("=" * 78)
