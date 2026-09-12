import ast
import subprocess
from pathlib import Path

targets = {
    94: Path(r"services\quantitative\block94_portfolio_stress_scenario_engine.py"),
    95: Path(r"services\quantitative\block95_stress_evidence_gate.py"),
    96: Path(r"services\quantitative\block96_stress_decision_gate.py"),
}

output = []


def p(text=""):
    print(text)
    output.append(str(text))


p("=" * 100)
p("EROS 3.0 - BLOCK 94-96 BLOCKED HELPER TRACE")
p("=" * 100)

for block_id, path in targets.items():

    p()
    p("=" * 100)
    p(f"BLOCK {block_id}")
    p("=" * 100)
    p(f"SOURCE: {path}")

    if not path.exists():
        p("ERROR: FILE NOT FOUND")
        continue

    source = path.read_text(encoding="utf-8-sig")

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        p("AST PARSE ERROR")
        p(f"{type(exc).__name__}: {exc}")
        continue

    lines = source.splitlines()

    # ------------------------------------------------------------
    # Find helper methods whose names suggest BLOCKED construction
    # ------------------------------------------------------------

    candidates = []

    for node in ast.walk(tree):

        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        name = node.name.lower()

        if "blocked" in name or "block" in name or "reject" in name or "fail" in name:
            candidates.append(node)

    if not candidates:
        p("NO BLOCKED/REJECTION HELPER FOUND")
        continue

    for method in sorted(candidates, key=lambda x: x.lineno):

        start = method.lineno
        end = getattr(method, "end_lineno", method.lineno)

        p()
        p("-" * 100)
        p(f"HELPER: {method.name}")
        p(f"LOCATION: L{start}-L{end}")
        p("-" * 100)

        for n in range(start, end + 1):
            p(f"L{n}: {lines[n-1]}")

        # --------------------------------------------------------
        # Analyze returns
        # --------------------------------------------------------

        returns = [node for node in ast.walk(method) if isinstance(node, ast.Return)]

        p()
        p(f"RETURN COUNT: {len(returns)}")

        for idx, ret in enumerate(sorted(returns, key=lambda x: x.lineno), start=1):

            p()
            p(f"RETURN #{idx} AT L{ret.lineno}")

            if isinstance(ret.value, ast.Dict):

                keys = []

                for key in ret.value.keys:

                    if isinstance(key, ast.Constant):
                        keys.append(str(key.value))
                    elif key is None:
                        keys.append("<**>")
                    else:
                        keys.append(ast.unparse(key))

                p("RETURN DICTIONARY KEYS:")

                for key in keys:
                    p(f"  {key}")

                required = {
                    "execution_blocked",
                    "non_mutation_invariant",
                    "broker_submission",
                    "live_order_submission",
                }

                missing = required - set(keys)

                p()

                if missing:
                    p("SAFETY CONTRACT: MISSING")

                    for field in sorted(missing):
                        p(f"  MISSING: {field}")
                else:
                    p("SAFETY CONTRACT: PRESENT")

            else:

                p("RETURN VALUE IS NOT A LITERAL DICTIONARY")

                if ret.value is not None:
                    p(ast.dump(ret.value, include_attributes=False))

p()
p("=" * 100)
p("BLOCKED HELPER TRACE COMPLETE")
p("=" * 100)

p()
p("TARGET STANDARD CONTRACT:")
p('  "execution_blocked": True')
p('  "non_mutation_invariant": True')
p('  "broker_submission": False')
p('  "live_order_submission": False')

p()
p("READ ONLY")
p("NO SOURCE CHANGES")
p("NO BROKER")
p("NO LIVE EXECUTION")
p("NO ORDER CREATION")
p("NO PORTFOLIO MUTATION")
p("NO VALUATION MUTATION")

# ------------------------------------------------------------
# Clipboard
# ------------------------------------------------------------

clipboard_text = "\n".join(output)

try:

    subprocess.run(
        ["clip.exe"],
        input=clipboard_text,
        text=True,
        check=True,
    )

    print()
    print("=" * 100)
    print("CLIPBOARD : PASS")
    print("=" * 100)
    print("COMPLETE HELPER TRACE COPIED TO WINDOWS CLIPBOARD")
    print()
    print(">>> PRESS CTRL+V IN CHATGPT <<<")
    print("=" * 100)

except Exception as exc:

    print()
    print("=" * 100)
    print("CLIPBOARD : FAIL")
    print("=" * 100)
    print(type(exc).__name__, str(exc))
    print("=" * 100)
