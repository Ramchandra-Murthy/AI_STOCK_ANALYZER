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
p("EROS 3.0 - BLOCK 94-96 CERTIFY/GATE METHOD SAFETY RETURN TRACE")
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

    lines = path.read_text(encoding="utf-8-sig").splitlines()

    # ------------------------------------------------------------
    # Locate the actual public execution method
    # ------------------------------------------------------------

    method_names = {
        94: ["def certify("],
        95: ["def certify("],
        96: ["def decide("],
    }

    method_line = None

    for i, line in enumerate(lines, start=1):
        if any(name in line for name in method_names[block_id]):
            method_line = i
            break

    if method_line is None:
        p("ERROR: PUBLIC METHOD NOT FOUND")
        continue

    p()
    p(f"PUBLIC METHOD START: L{method_line}")

    # ------------------------------------------------------------
    # Determine method end using next same-level def/class
    # ------------------------------------------------------------

    method_end = len(lines)

    for i in range(method_line + 1, len(lines) + 1):

        line = lines[i - 1]

        if line.startswith("    def ") or line.startswith("    @"):
            # Decorators can belong to next method, so only terminate
            # when another function definition is encountered.
            if line.startswith("    def "):
                method_end = i - 1
                break

        if line.startswith("class "):
            method_end = i - 1
            break

    p(f"PUBLIC METHOD END APPROX: L{method_end}")

    # ------------------------------------------------------------
    # Print the complete public method
    # ------------------------------------------------------------

    p()
    p("=" * 100)
    p("ACTUAL PUBLIC METHOD SOURCE")
    p("=" * 100)

    for n in range(method_line, method_end + 1):
        p(f"L{n}: {lines[n-1]}")

    # ------------------------------------------------------------
    # Find relevant safety/status lines INSIDE method only
    # ------------------------------------------------------------

    p()
    p("=" * 100)
    p("SAFETY / BLOCKED LINES INSIDE PUBLIC METHOD")
    p("=" * 100)

    found = False

    for i in range(method_line, method_end + 1):

        line = lines[i - 1]

        if any(
            token in line
            for token in [
                "STATUS_BLOCKED",
                '"status": "BLOCKED"',
                '"status": STATUS_BLOCKED',
                '"gate_status": STATUS_BLOCKED',
                '"decision_status": STATUS_BLOCKED',
                '"readiness_status": STATUS_BLOCKED',
                '"execution_blocked"',
                '"non_mutation_invariant"',
                '"broker_submission"',
                '"live_order_submission"',
                "return {",
                "return result",
                "return certificate",
            ]
        ):

            found = True

            start = max(method_line, i - 8)
            end = min(method_end, i + 18)

            p()
            p(f"--- METHOD WINDOW L{start}-L{end} ---")

            for n in range(start, end + 1):
                marker = ">>" if n == i else "  "
                p(f"{marker} L{n}: {lines[n-1]}")

    if not found:
        p("NO SAFETY/BLOCKED RETURN TOKENS FOUND INSIDE PUBLIC METHOD.")

p()
p("=" * 100)
p("TRACE COMPLETE")
p("=" * 100)

p()
p("THIS TRACE IS READ ONLY.")
p("NO SOURCE CHANGES")
p("NO BROKER")
p("NO LIVE EXECUTION")
p("NO ORDER CREATION")
p("NO PORTFOLIO MUTATION")
p("NO VALUATION MUTATION")

p()
p("EXPECTED NORMALIZATION TARGET:")
p('  "execution_blocked": True')
p('  "non_mutation_invariant": True')
p('  "broker_submission": False')
p('  "live_order_submission": False')

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
    print("COMPLETE TRACE COPIED TO WINDOWS CLIPBOARD")
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
