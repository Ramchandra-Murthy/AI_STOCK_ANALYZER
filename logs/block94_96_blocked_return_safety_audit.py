import ast
from pathlib import Path

targets = {
    94: Path(r"services\quantitative\block94_portfolio_stress_scenario_engine.py"),
    95: Path(r"services\quantitative\block95_stress_evidence_gate.py"),
    96: Path(r"services\quantitative\block96_stress_decision_gate.py"),
}

REQUIRED = {
    "execution_blocked": True,
    "non_mutation_invariant": True,
    "broker_submission": False,
    "live_order_submission": False,
}

print("=" * 100)
print("EROS 3.0 - BLOCK 94-96 BLOCKED RETURN SAFETY DICTIONARY AUDIT")
print("=" * 100)

for block_id, path in targets.items():

    print()
    print("=" * 100)
    print(f"BLOCK {block_id}")
    print("=" * 100)

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    blocked_returns = []

    for node in ast.walk(tree):

        if not isinstance(node, ast.Return):
            continue

        value = node.value

        if not isinstance(value, ast.Dict):
            continue

        keys = []

        for key in value.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                keys.append(key.value)

        if "status" not in keys:
            continue

        # Only inspect dictionaries that visibly contain BLOCKED
        is_blocked = False

        for key_node, value_node in zip(value.keys, value.values):

            if isinstance(key_node, ast.Constant) and key_node.value == "status":
                if isinstance(value_node, ast.Constant) and value_node.value == "BLOCKED":
                    is_blocked = True

        if is_blocked:
            blocked_returns.append((node.lineno, keys))

    if not blocked_returns:
        print("NO LITERAL BLOCKED RETURN DICTIONARIES FOUND")
        continue

    for lineno, keys in blocked_returns:

        print()
        print(f"BLOCKED RETURN AT LINE {lineno}")
        print("-" * 70)

        for field, expected in REQUIRED.items():

            if field in keys:
                print(f"[PRESENT] {field}")
            else:
                print(f"[MISSING ] {field} -> expected {expected!r}")

print()
print("=" * 100)
print("AUDIT COMPLETE")
print("=" * 100)
print("NO SOURCE CHANGES")
print("=" * 100)
