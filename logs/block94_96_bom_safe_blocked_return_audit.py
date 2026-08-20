from pathlib import Path
import ast

targets = {
    94: Path(r"services\quantitative\block94_portfolio_stress_scenario_engine.py"),
    95: Path(r"services\quantitative\block95_stress_evidence_gate.py"),
    96: Path(r"services\quantitative\block96_stress_decision_gate.py"),
}

required = {
    "execution_blocked": True,
    "non_mutation_invariant": True,
    "broker_submission": False,
    "live_order_submission": False,
}

print("=" * 100)
print("EROS 3.0 - BLOCK 94-96 BOM-SAFE BLOCKED RETURN AUDIT")
print("=" * 100)

for block_id, path in targets.items():

    print()
    print("=" * 100)
    print(f"BLOCK {block_id}")
    print("=" * 100)

    # IMPORTANT:
    # utf-8-sig removes the BOM without modifying the source file.
    source = path.read_text(encoding="utf-8-sig")

    tree = ast.parse(source, filename=str(path))

    found = 0

    for node in ast.walk(tree):

        if not isinstance(node, ast.Return):
            continue

        if not isinstance(node.value, ast.Dict):
            continue

        keys = []

        for key in node.value.keys:
            if isinstance(key, ast.Constant):
                if isinstance(key.value, str):
                    keys.append(key.value)

        if "status" not in keys:
            continue

        blocked = False

        for key_node, value_node in zip(
            node.value.keys,
            node.value.values,
        ):

            if (
                isinstance(key_node, ast.Constant)
                and key_node.value == "status"
            ):

                if (
                    isinstance(value_node, ast.Constant)
                    and value_node.value == "BLOCKED"
                ):
                    blocked = True

        if not blocked:
            continue

        found += 1

        print()
        print(f"BLOCKED RETURN #{found} AT LINE {node.lineno}")
        print("-" * 70)

        for field, expected in required.items():

            if field in keys:
                print(f"[PRESENT] {field}")
            else:
                print(
                    f"[MISSING ] {field}"
                    f" -> expected {expected!r}"
                )

    if found == 0:
        print("NO LITERAL status='BLOCKED' RETURN DICTIONARY FOUND")

print()
print("=" * 100)
print("AUDIT COMPLETE")
print("=" * 100)
print("NO SOURCE CHANGES")
print("BOM HANDLED READ-ONLY")
print("=" * 100)
