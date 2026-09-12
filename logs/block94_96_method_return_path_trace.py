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
p("EROS 3.0 - BLOCK 94-96 CERTIFY/DECIDE RETURN PATH TRACE")
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

    # BOM-safe
    source = path.read_text(encoding="utf-8-sig")

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        p("AST PARSE ERROR")
        p(f"{type(exc).__name__}: {exc}")
        continue

    lines = source.splitlines()

    # ------------------------------------------------------------
    # Find target methods
    # ------------------------------------------------------------

    target_method_names = {
        94: {"certify"},
        95: {"certify"},
        96: {"decide", "certify"},
    }[block_id]

    methods = []

    for node in ast.walk(tree):

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in target_method_names:
                methods.append(node)

    if not methods:
        p("TARGET METHOD NOT FOUND")
        continue

    for method in methods:

        p()
        p("-" * 100)
        p(f"METHOD: {method.name}")
        p(f"LOCATION: L{method.lineno}-L" f"{getattr(method, 'end_lineno', method.lineno)}")
        p("-" * 100)

        # --------------------------------------------------------
        # Print complete method
        # --------------------------------------------------------

        start = method.lineno
        end = getattr(method, "end_lineno", method.lineno)

        p()
        p("COMPLETE METHOD SOURCE:")

        for n in range(start, end + 1):
            p(f"L{n}: {lines[n-1]}")

        # --------------------------------------------------------
        # Find all return statements inside this method
        # --------------------------------------------------------

        p()
        p("RETURN STATEMENTS INSIDE TARGET METHOD:")

        returns = [node for node in ast.walk(method) if isinstance(node, ast.Return)]

        if not returns:
            p("NO RETURN STATEMENTS FOUND")
            continue

        for index, ret in enumerate(
            sorted(returns, key=lambda x: x.lineno),
            start=1,
        ):

            rstart = max(start, ret.lineno - 8)
            rend = min(end, getattr(ret, "end_lineno", ret.lineno) + 12)

            p()
            p(f"--- RETURN #{index} " f"AT L{ret.lineno} " f"WINDOW L{rstart}-L{rend} ---")

            for n in range(rstart, rend + 1):
                marker = ">>" if n == ret.lineno else "  "
                p(f"{marker} L{n}: {lines[n-1]}")

            # ----------------------------------------------------
            # AST classification of return value
            # ----------------------------------------------------

            value = ret.value

            if isinstance(value, ast.Dict):
                keys = []

                for key in value.keys:
                    if isinstance(key, ast.Constant):
                        keys.append(repr(key.value))
                    else:
                        keys.append(ast.unparse(key) if key is not None else "<**>")

                p()
                p("RETURN DICTIONARY KEYS:")
                for key in keys:
                    p(f"  {key}")

                required = {
                    "execution_blocked",
                    "non_mutation_invariant",
                    "broker_submission",
                    "live_order_submission",
                }

                missing = required - set(k.strip("'\"") for k in keys)

                p()
                if missing:
                    p("SAFETY CONTRACT: MISSING")
                    for field in sorted(missing):
                        p(f"  MISSING: {field}")
                else:
                    p("SAFETY CONTRACT: PRESENT")

            else:
                p()
                p("RETURN TYPE:")
                p(
                    ast.dump(
                        value,
                        include_attributes=False,
                    )
                    if value is not None
                    else "None"
                )

p()
p("=" * 100)
p("TRACE COMPLETE")
p("=" * 100)

p()
p("EXPECTED STANDARD SAFETY CONTRACT:")
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
# COPY COMPLETE OUTPUT TO WINDOWS CLIPBOARD
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
    print("COMPLETE TRACE COPIED TO WINDOWS CLIPBOARD")
    print()
    print(">>> RETURN TO CHATGPT AND PRESS CTRL+V <<<")
    print("=" * 100)

except Exception as exc:

    print()
    print("=" * 100)
    print("CLIPBOARD : FAIL")
    print("=" * 100)
    print(type(exc).__name__, str(exc))
    print("=" * 100)
