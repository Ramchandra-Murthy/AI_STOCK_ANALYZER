from __future__ import annotations

import ast
import inspect
import os
import sys
import traceback

PROJECT_ROOT = r"D:\Users\User\Desktop\AI_STOCK_ANALYZER"
ADAPTER_PATH = os.path.join(
    PROJECT_ROOT,
    "services",
    "eros_frontend_adapter.py",
)

print("=" * 78)
print("EROS 3.0 - V3.8.2.4 AUDIT DATAFLOW SOURCE DIAGNOSTIC")
print("=" * 78)

print("\n1. ENVIRONMENT")
print("-" * 78)
print("PYTHON :", sys.version)
print("CWD    :", os.getcwd())
print("ROOT   :", PROJECT_ROOT)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print("PATH   :", "PASS" if PROJECT_ROOT in sys.path else "FAIL")

print("\n2. SOURCE READ")
print("-" * 78)

try:
    with open(ADAPTER_PATH, "r", encoding="utf-8-sig") as f:
        source = f.read()

    print("SOURCE READ :", "PASS")
    print("SOURCE LEN  :", len(source))
    print("SOURCE FILE :", ADAPTER_PATH)

except Exception:
    print("SOURCE READ : FAIL")
    traceback.print_exc()
    raise SystemExit(1)


print("\n3. AST PARSE")
print("-" * 78)

try:
    tree = ast.parse(source)
    print("AST PARSE : PASS")
except Exception:
    print("AST PARSE : FAIL")
    traceback.print_exc()
    raise SystemExit(1)


print("\n4. LOCATE decision_audit")
print("-" * 78)

audit_node = None
trace_node = None

for node in ast.walk(tree):

    if isinstance(node, ast.FunctionDef):

        if node.name == "decision_audit":
            audit_node = node

        elif node.name == "decision_traceability":
            trace_node = node

print(
    "decision_audit      :",
    "FOUND" if audit_node else "ABSENT",
)

print(
    "decision_traceability:",
    "FOUND" if trace_node else "ABSENT",
)

if audit_node:
    print(
        "AUDIT LINE RANGE    :",
        audit_node.lineno,
        "-",
        getattr(audit_node, "end_lineno", "?"),
    )

if trace_node:
    print(
        "TRACE LINE RANGE    :",
        trace_node.lineno,
        "-",
        getattr(trace_node, "end_lineno", "?"),
    )


print("\n5. RUNTIME IMPORT")
print("-" * 78)

try:
    from services.eros_frontend_adapter import EROSFrontendAdapter

    print("IMPORT : PASS")
    print("CLASS  :", EROSFrontendAdapter.__name__)

except Exception:
    print("IMPORT : FAIL")
    traceback.print_exc()
    raise SystemExit(1)


adapter = EROSFrontendAdapter()
symbol = "RELIANCE.NS"


print("\n6. HEALTHY UPSTREAM TRACEABILITY SNAPSHOT")
print("-" * 78)

try:
    trace_result = adapter.decision_traceability(symbol)

    print("CALL :", "PASS")
    print("TYPE :", type(trace_result).__name__)

    if isinstance(trace_result, dict):

        print("\nTOP LEVEL KEYS:")
        print(list(trace_result.keys()))

        for key in [
            "decision",
            "trace",
            "evidence_chain",
            "scenario_trace",
            "interpretation",
            "conclusion",
            "traceability",
        ]:

            value = trace_result.get(key)

            if isinstance(value, dict):

                print(
                    f"{key:20} : DICT "
                    f"keys={len(value)}"
                )

                if value:
                    print(
                        f"{'':20}   "
                        f"{list(value.keys())[:20]}"
                    )

            elif isinstance(value, list):

                print(
                    f"{key:20} : LIST "
                    f"items={len(value)}"
                )

            else:

                print(
                    f"{key:20} : "
                    f"{type(value).__name__} "
                    f"{value!r}"
                )

        traceability = trace_result.get(
            "traceability"
        )

        if isinstance(traceability, dict):

            print("\nTRACEABILITY STAGES:")
            stages = traceability.get("stages")

            if isinstance(stages, dict):
                for key, value in stages.items():
                    print(
                        f"  {key:35} : {value}"
                    )

        print("\nTRACEABILITY PRIMARY SCENARIO:")
        print(
            traceability.get("primary_scenario")
            if isinstance(traceability, dict)
            else None
        )

        print("\nTRACEABILITY DECISION QUALITY:")
        print(
            traceability.get("decision_quality")
            if isinstance(traceability, dict)
            else None
        )

except Exception:
    print("TRACEABILITY CALL : FAIL")
    traceback.print_exc()
    trace_result = None


print("\n7. DECISION AUDIT RUNTIME RESULT")
print("-" * 78)

try:

    audit_result = adapter.decision_audit(symbol)

    print("CALL :", "PASS")
    print("TYPE :", type(audit_result).__name__)

    if isinstance(audit_result, dict):

        print("\nAUDIT TOP LEVEL KEYS:")
        print(list(audit_result.keys()))

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
            "audit_summary",
            "audit_status",
        ]:

            value = audit_result.get(key)

            if isinstance(value, dict):

                print(
                    f"{key:20} : DICT "
                    f"keys={len(value)}"
                )

                if value:
                    print(
                        f"{'':20}   "
                        f"{list(value.keys())[:20]}"
                    )

            elif isinstance(value, list):

                print(
                    f"{key:20} : LIST "
                    f"items={len(value)}"
                )

            else:

                print(
                    f"{key:20} : "
                    f"{type(value).__name__} "
                    f"{value!r}"
                )

except Exception:
    print("AUDIT CALL : FAIL")
    traceback.print_exc()
    audit_result = None


print("\n8. AST VARIABLE ASSIGNMENT ANALYSIS")
print("-" * 78)

tracked = [
    "_v381_result",
    "_v381_trace",
    "_v381_audit",
    "_v382_result",
    "_v382_trace",
    "_v382_trace_result",
    "_v382_convergence_result",
    "_v382_decision",
    "_v382_evidence_chain",
    "_v382_scenario_trace",
    "_v382_interpretation",
    "_v382_traceability",
    "_v382_legacy_trace",
    "_v382_primary_scenario",
    "_v382_decision_quality",
    "_v382_conclusion",
]

if audit_node:

    assignments = {}

    for node in ast.walk(audit_node):

        if isinstance(node, ast.Assign):

            for target in node.targets:

                if isinstance(target, ast.Name):

                    name = target.id

                    if name in tracked:

                        assignments.setdefault(
                            name,
                            []
                        ).append(
                            node.lineno
                        )

        elif isinstance(node, ast.AnnAssign):

            target = node.target

            if isinstance(target, ast.Name):

                name = target.id

                if name in tracked:

                    assignments.setdefault(
                        name,
                        []
                    ).append(
                        node.lineno
                    )

    for name in tracked:

        lines = assignments.get(name, [])

        print(
            f"{name:30} : "
            f"{len(lines)} assignment(s)"
        )

        if lines:
            print(
                f"{'':30}   lines={lines}"
            )


print("\n9. AUDIT METHOD SOURCE — TARGETED")
print("-" * 78)

if audit_node:

    lines = source.splitlines()

    start = max(
        audit_node.lineno - 1,
        0,
    )

    end = min(
        getattr(
            audit_node,
            "end_lineno",
            audit_node.lineno + 1,
        ),
        len(lines),
    )

    print(
        "AUDIT METHOD SOURCE LINES "
        f"{start + 1}-{end}"
    )
    print("-" * 78)

    for number in range(start, end):

        print(
            f"{number + 1:5} | {lines[number]}"
        )


print("\n10. TRACEABILITY METHOD SOURCE — TARGETED")
print("-" * 78)

if trace_node:

    lines = source.splitlines()

    start = max(
        trace_node.lineno - 1,
        0,
    )

    end = min(
        getattr(
            trace_node,
            "end_lineno",
            trace_node.lineno + 1,
        ),
        len(lines),
    )

    print(
        "TRACEABILITY METHOD SOURCE LINES "
        f"{start + 1}-{end}"
    )
    print("-" * 78)

    for number in range(start, end):

        print(
            f"{number + 1:5} | {lines[number]}"
        )


print("\n11. DIRECT COMPARISON")
print("-" * 78)

if (
    isinstance(trace_result, dict)
    and isinstance(audit_result, dict)
):

    fields = [
        "decision",
        "trace",
        "traceability",
        "evidence_chain",
        "scenario_trace",
        "interpretation",
        "conclusion",
    ]

    print(
        f"{'FIELD':25} "
        f"{'TRACEABILITY':20} "
        f"{'AUDIT':20}"
    )

    print("-" * 68)

    for field in fields:

        upstream = trace_result.get(field)
        downstream = audit_result.get(field)

        def describe(value):

            if isinstance(value, dict):
                return f"DICT({len(value)})"

            if isinstance(value, list):
                return f"LIST({len(value)})"

            if value is None:
                return "NONE"

            if value == "":
                return "EMPTY"

            return type(value).__name__

        print(
            f"{field:25} "
            f"{describe(upstream):20} "
            f"{describe(downstream):20}"
        )


print("\n12. FIRST DATA LOSS INDICATOR")
print("-" * 78)

if (
    isinstance(trace_result, dict)
    and isinstance(audit_result, dict)
):

    fields = [
        "decision",
        "trace",
        "traceability",
        "evidence_chain",
        "scenario_trace",
        "interpretation",
        "conclusion",
    ]

    found = False

    for field in fields:

        upstream = trace_result.get(field)
        downstream = audit_result.get(field)

        upstream_populated = (
            isinstance(upstream, dict)
            and len(upstream) > 0
        ) or (
            isinstance(upstream, list)
            and len(upstream) > 0
        ) or (
            isinstance(upstream, str)
            and len(upstream) > 0
        )

        downstream_empty = (
            downstream == {}
            or downstream == []
            or downstream is None
            or downstream == ""
        )

        if upstream_populated and downstream_empty:

            print(
                "FIRST OBSERVED DATA LOSS:"
            )

            print(
                "FIELD      :",
                field,
            )

            print(
                "UPSTREAM   :",
                type(upstream).__name__,
            )

            print(
                "DOWNSTREAM :",
                type(downstream).__name__,
            )

            print(
                "CONCLUSION : decision_audit "
                "is not preserving the upstream value."
            )

            found = True
            break

    if not found:

        print(
            "No direct upstream/downstream "
            "loss detected by this comparison."
        )


print("\n" + "=" * 78)
print("V3.8.2.4 DIAGNOSTIC COMPLETE")
print("=" * 78)

print(
    """
NO SOURCE PATCH PERFORMED.

This diagnostic only inspects the existing source and runtime.

The objective is to identify exactly which variables inside
decision_audit() fail to receive the already-populated
V3.7.2 decision_traceability() data.

DO NOT PATCH UNTIL THIS OUTPUT IS REVIEWED.
"""
)

print("=" * 78)

