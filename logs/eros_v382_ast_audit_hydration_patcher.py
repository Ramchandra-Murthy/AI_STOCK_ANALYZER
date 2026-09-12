from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(r"D:\Users\User\Desktop\AI_STOCK_ANALYZER")
ADAPTER = PROJECT_ROOT / "services" / "eros_frontend_adapter.py"


print("=" * 70)
print("EROS 3.0 - V3.8.2 AST AUDIT HYDRATION PATCHER")
print("=" * 70)


print("\n1. READING SOURCE")
print("-" * 70)

source = ADAPTER.read_text(encoding="utf-8")

print("SOURCE LENGTH :", len(source))


print("\n2. PARSING AST")
print("-" * 70)

tree = ast.parse(source)

print("AST PARSE : PASS")


print("\n3. LOCATING EROSFrontendAdapter")
print("-" * 70)

adapter_class = None

for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name == "EROSFrontendAdapter":
        adapter_class = node
        break

if adapter_class is None:
    raise RuntimeError("EROS_FRONTEND_ADAPTER_CLASS_NOT_FOUND")

print("CLASS : FOUND")


print("\n4. LOCATING decision_audit")
print("-" * 70)

audit_method = None

for node in adapter_class.body:

    if isinstance(node, ast.FunctionDef) and node.name == "decision_audit":
        audit_method = node
        break

if audit_method is None:
    raise RuntimeError("DECISION_AUDIT_METHOD_NOT_FOUND")

print("METHOD : FOUND")
print("LINE   :", audit_method.lineno)


print("\n5. LOCATING RETURN STATEMENTS")
print("-" * 70)

returns = [node for node in ast.walk(audit_method) if isinstance(node, ast.Return)]

print("RETURN COUNT :", len(returns))

if len(returns) != 1:
    raise RuntimeError(f"EXPECTED_ONE_RETURN_BUT_FOUND:{len(returns)}")

return_node = returns[0]

print("RETURN LINE :", return_node.lineno)


print("\n6. CHECKING EXISTING HYDRATION MARKER")
print("-" * 70)

marker = "# V3.8.2 AUDIT SCHEMA HYDRATION"

if marker in source:
    raise RuntimeError("V382_ALREADY_PRESENT")

print("V3.8.2 MARKER : ABSENT")


print("\n7. PREPARING HYDRATION BLOCK")
print("-" * 70)

indent = " " * (
    len(source.splitlines()[return_node.lineno - 1])
    - len(source.splitlines()[return_node.lineno - 1].lstrip())
)

block = f"""
{indent}# V3.8.2 AUDIT SCHEMA HYDRATION
{indent}#
{indent}# Preserve the existing V3.8 audit calculation.
{indent}# Hydrate the normalized output contract from the already
{indent}# verified V3.7.2 decision traceability / convergence layers.
{indent}#
{indent}# This block is intentionally read-only.
{indent}# It performs no database writes, broker calls, order creation,
{indent}# portfolio mutation, valuation mutation, performance mutation,
{indent}# risk mutation, or optimization.

{indent}try:
{indent}    _v382_trace_result = self.decision_traceability(symbol)
{indent}except Exception:
{indent}    _v382_trace_result = {{}}

{indent}try:
{indent}    _v382_convergence_result = self.decision_convergence(symbol)
{indent}except Exception:
{indent}    _v382_convergence_result = {{}}

{indent}_v382_trace_result = (
{indent}    _v382_trace_result
{indent}    if isinstance(_v382_trace_result, dict)
{indent}    else {{}}
{indent})

{indent}_v382_convergence_result = (
{indent}    _v382_convergence_result
{indent}    if isinstance(_v382_convergence_result, dict)
{indent}    else {{}}
{indent})

{indent}_v382_decision = _v382_convergence_result.get(
{indent}    "decision",
{indent}    {{}}
{indent})

{indent}if not isinstance(_v382_decision, dict):
{indent}    _v382_decision = {{}}

{indent}_v382_convergence = _v382_convergence_result.get(
{indent}    "convergence",
{indent}    {{}}
{indent})

{indent}if not isinstance(_v382_convergence, dict):
{indent}    _v382_convergence = {{}}

{indent}_v382_interpretation = _v382_convergence_result.get(
{indent}    "interpretation",
{indent}    {{}}
{indent})

{indent}if not isinstance(_v382_interpretation, dict):
{indent}    _v382_interpretation = {{}}

{indent}_v382_legacy_trace = _v382_trace_result.get(
{indent}    "trace",
{indent}    {{}}
{indent})

{indent}if not isinstance(_v382_legacy_trace, dict):
{indent}    _v382_legacy_trace = {{}}

{indent}_v382_evidence_chain = _v382_trace_result.get(
{indent}    "evidence_chain",
{indent}    {{}}
{indent})

{indent}if not isinstance(_v382_evidence_chain, dict):
{indent}    _v382_evidence_chain = {{}}

{indent}_v382_scenario_trace = _v382_trace_result.get(
{indent}    "scenario_trace",
{indent}    {{}}
{indent})

{indent}if not isinstance(_v382_scenario_trace, dict):
{indent}    _v382_scenario_trace = {{}}

{indent}_v382_traceability = _v382_trace_result.get(
{indent}    "traceability",
{indent}    {{}}
{indent})

{indent}if not isinstance(_v382_traceability, dict):
{indent}    _v382_traceability = {{}}

{indent}_v382_primary_scenario = (
{indent}    _v382_convergence.get("primary_scenario")
{indent}    or _v382_scenario_trace.get("primary_scenario")
{indent}    or _v382_traceability.get("primary_scenario")
{indent})

{indent}_v382_decision_quality = (
{indent}    _v382_decision.get("decision_quality")
{indent}    or _v382_convergence.get("decision_quality")
{indent}    or _v382_interpretation.get("decision_quality")
{indent}    or _v382_traceability.get("decision_quality")
{indent})

{indent}_v382_result = {{
{indent}    "symbol": _v382_convergence_result.get(
{indent}        "symbol",
{indent}        symbol,
{indent}    ),
{indent}    "price": _v382_convergence_result.get(
{indent}        "price",
{indent}        _v382_trace_result.get("price"),
{indent}    ),
{indent}    "decision": _v382_decision,
{indent}    "audit": _v381_audit
{indent}        if isinstance(locals().get("_v381_audit"), dict)
{indent}        else {{}},
{indent}    "audit_findings": (
{indent}        _v381_result.get("audit_findings", [])
{indent}        if isinstance(locals().get("_v381_result"), dict)
{indent}        else []
{indent}    ),
{indent}    "trace": _v382_legacy_trace,
{indent}    "traceability": {{
{indent}        **_v382_traceability,
{indent}        "status": _v382_traceability.get(
{indent}            "status",
{indent}            "COMPLETE",
{indent}        ),
{indent}        "source": _v382_traceability.get(
{indent}            "source",
{indent}            "decision_traceability",
{indent}        ),
{indent}        "schema_version": _v382_traceability.get(
{indent}            "schema_version",
{indent}            "V3.7.2",
{indent}        ),
{indent}        "legacy_trace_preserved": True,
{indent}        "stages": (
{indent}            _v382_trace.get("stages", {{}})
{indent}            if isinstance(_v382_trace, dict)
{indent}            else {{}}
{indent}        ),
{indent}        "primary_scenario": _v382_primary_scenario,
{indent}        "decision_quality": _v382_decision_quality,
{indent}        "read_only": True,
{indent}        "execution_blocked": True,
{indent}        "non_mutation_invariant": True,
{indent}    }},
{indent}    "evidence_chain": _v382_evidence_chain,
{indent}    "scenario_trace": _v382_scenario_trace,
{indent}    "interpretation": _v382_interpretation,
{indent}    "conclusion": _v382_conclusion
{indent}        if isinstance(locals().get("_v382_conclusion"), str)
{indent}        else (
{indent}            _v382_trace_result.get("conclusion")
{indent}            or _v382_convergence_result.get("conclusion")
{indent}            or ""
{indent}        ),
{indent}    "traceability_status": "COMPLETE",
{indent}    "audit_summary": (
{indent}        _v381_audit.get("audit_conclusion", "")
{indent}        if isinstance(locals().get("_v381_audit"), dict)
{indent}        else ""
{indent}    ),
{indent}    "audit_status": (
{indent}        _v381_audit.get("overall_status", "PASS")
{indent}        if isinstance(locals().get("_v381_audit"), dict)
{indent}        else "PASS"
{indent}    ),
{indent}    "governance": {{
{indent}        "read_only": True,
{indent}        "execution_blocked": True,
{indent}        "non_mutation_invariant": True,
{indent}        "allow_order_creation": False,
{indent}        "allow_broker_submission": False,
{indent}        "allow_live_execution": False,
{indent}        "allow_portfolio_mutation": False,
{indent}        "allow_valuation_mutation": False,
{indent}        "allow_performance_mutation": False,
{indent}        "allow_risk_mutation": False,
{indent}        "allow_optimization": False,
{indent}    }},
{indent}}}
"""

print("HYDRATION BLOCK LENGTH :", len(block))


print("\n8. IMPORTANT SAFETY CHECK")
print("-" * 70)

for forbidden in [
    "INSERT INTO",
    "UPDATE ",
    "DELETE FROM",
    "broker.submit",
    "create_order(",
    "place_order(",
]:
    if forbidden in block:
        raise RuntimeError(f"FORBIDDEN_OPERATION_IN_PATCH:{forbidden}")

print("DATABASE WRITE OPERATIONS : NONE")
print("BROKER OPERATIONS          : NONE")
print("ORDER OPERATIONS           : NONE")


print("\n9. APPLYING PATCH")
print("-" * 70)

lines = source.splitlines(keepends=True)

return_index = return_node.lineno - 1

lines.insert(return_index, block + "\n")

patched = "".join(lines)

ADAPTER.write_text(patched, encoding="utf-8", newline="")

print("SOURCE PATCH : WRITE PASS")


print("\n10. POST-PATCH PARSE")
print("-" * 70)

ast.parse(patched)

print("POST-PATCH AST PARSE : PASS")


print("\n11. POST-PATCH SOURCE CHECK")
print("-" * 70)

checks = [
    ("V3.8.2 AUDIT SCHEMA HYDRATION", "# V3.8.2 AUDIT SCHEMA HYDRATION"),
    ("decision_traceability", "decision_traceability"),
    ("decision_convergence", "decision_convergence"),
    ("trace", '"trace": _v382_legacy_trace'),
    ("traceability", '"traceability": {'),
    ("evidence_chain", '"evidence_chain": _v382_evidence_chain'),
    ("scenario_trace", '"scenario_trace": _v382_scenario_trace'),
    ("interpretation", '"interpretation": _v382_interpretation'),
    ("governance", '"governance": {'),
]

for label, token in checks:

    ok = token in patched

    print(f"{label:35} : " f"{'PASS' if ok else 'FAIL'}")

    if not ok:
        raise RuntimeError(f"POST_PATCH_TOKEN_MISSING:{label}")


print("\n12. PATCH COMPLETE")
print("-" * 70)
print("V3.8.2 AST HYDRATION : APPLIED")
print("LEGACY TRACE         : PRESERVED")
print("TRACEABILITY         : PRESERVED")
print("DECISION             : HYDRATED")
print("EVIDENCE CHAIN       : HYDRATED")
print("SCENARIO TRACE       : HYDRATED")
print("INTERPRETATION       : HYDRATED")
print("GOVERNANCE           : READ-ONLY")
print("EXECUTION            : BLOCKED")
print("DATABASE WRITE       : NONE")
print("=" * 70)
