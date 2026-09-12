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
p("EROS 3.0 - BLOCK 94-96 CERTIFY/DECISION RETURN PATH DIAGNOSTIC")
p("=" * 100)

for block_id, path in targets.items():

    p()
    p("=" * 100)
    p(f"BLOCK {block_id}")
    p("=" * 100)
    p(f"SOURCE: {path}")

    if not path.exists():
        p("ERROR: SOURCE FILE NOT FOUND")
        continue

    lines = path.read_text(encoding="utf-8-sig").splitlines()

    # Locate class methods and especially certify/decide.
    method_starts = []

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        if (
            stripped.startswith("def certify(")
            or stripped.startswith("def decide(")
            or stripped.startswith("def evaluate(")
        ):
            method_starts.append(i)

    p()
    p("TARGET METHOD LOCATIONS:")
    p(str(method_starts))

    if not method_starts:
        p("WARNING: No certify/decide/evaluate method found.")

    for start_line in method_starts:

        # Find next method at same indentation.
        method_indent = len(lines[start_line - 1]) - len(lines[start_line - 1].lstrip())

        end_line = len(lines)

        for j in range(start_line, len(lines)):
            candidate = lines[j]

            if not candidate.strip():
                continue

            indent = len(candidate) - len(candidate.lstrip())

            if (
                indent == method_indent
                and candidate.lstrip().startswith("def ")
                and j + 1 > start_line
            ):
                end_line = j
                break

        p()
        p(f"--- METHOD SOURCE WINDOW " f"L{start_line}-L{end_line} ---")

        for n in range(start_line, end_line + 1):
            marker = ""

            if (
                lines[n - 1].strip().startswith("return")
                or '"status"' in lines[n - 1]
                or '"broker_submission"' in lines[n - 1]
                or '"live_order_submission"' in lines[n - 1]
                or '"execution_blocked"' in lines[n - 1]
                or '"non_mutation_invariant"' in lines[n - 1]
            ):
                marker = ">>"

            p(f"{marker} L{n}: {lines[n-1]}")

    # Also locate exact safety-field occurrences.
    p()
    p("SAFETY FIELD LOCATIONS:")

    for i, line in enumerate(lines, start=1):

        if any(
            field in line
            for field in (
                '"execution_blocked"',
                '"non_mutation_invariant"',
                '"broker_submission"',
                '"live_order_submission"',
            )
        ):
            p(f"L{i}: {line}")

p()
p("=" * 100)
p("DIAGNOSTIC COMPLETE")
p("=" * 100)
p()
p("DO NOT MODIFY SOURCE FROM THIS OUTPUT.")
p("NEXT STEP: identify the exact early BLOCKED return dictionaries.")
p()
p("EXPECTED CONTRACT:")
p('  "execution_blocked": True')
p('  "non_mutation_invariant": True')
p('  "broker_submission": False')
p('  "live_order_submission": False')
p()
p("NO BROKER")
p("NO LIVE EXECUTION")
p("NO ORDER CREATION")
p("NO PORTFOLIO MUTATION")
p("NO VALUATION MUTATION")
p("=" * 100)

# Copy complete diagnostic to Windows clipboard.
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
    print("COMPLETE DIAGNOSTIC COPIED TO WINDOWS CLIPBOARD")
    print("NOW PRESS CTRL+V IN CHATGPT")
    print("=" * 100)

except Exception as exc:
    print()
    print("CLIPBOARD : FAIL")
    print(type(exc).__name__, str(exc))
