from pathlib import Path
import subprocess

path = Path(
    r"services\quantitative\block98_execution_governance_bridge.py"
)

output = []

def p(text=""):
    print(text)
    output.append(str(text))

p("=" * 100)
p("EROS 3.0 - BLOCK 98 READ-ONLY RETURN PATH SAFETY AUDIT")
p("=" * 100)

p()
p("SOURCE:")
p(str(path))

if not path.exists():
    p("SOURCE ERROR: FILE NOT FOUND")
else:
    source = path.read_text(
        encoding="utf-8-sig"
    )
    lines = source.splitlines()

    p()
    p(f"SOURCE LINES: {len(lines)}")

    p()
    p("=" * 100)
    p("ALL RETURN STATEMENTS")
    p("=" * 100)

    return_count = 0
    reported = set()

    for i, line in enumerate(lines, start=1):

        stripped = line.strip()

        if not stripped.startswith("return "):
            continue

        return_count += 1

        start = max(1, i - 8)
        end = min(len(lines), i + 20)

        window = (start, end)

        if window in reported:
            continue

        reported.add(window)

        p()
        p(f"--- RETURN WINDOW L{start}-L{end} ---")

        for n in range(start, end + 1):
            marker = ">>" if n == i else "  "
            p(f"{marker} L{n}: {lines[n-1]}")

    p()
    p(f"TOTAL RETURN STATEMENTS FOUND: {return_count}")

    p()
    p("=" * 100)
    p("SAFETY CONTRACT FIELD LOCATIONS")
    p("=" * 100)

    safety_terms = [
        '"execution_blocked"',
        '"non_mutation_invariant"',
        '"broker_submission"',
        '"live_order_submission"',
        '"portfolio_mutation"',
        '"valuation_mutation"',
        '"performance_mutation"',
        '"risk_mutation"',
        '"optimization"',
        '"order_creation"',
        '"status": STATUS_BLOCKED',
        '"governance_status"',
        '"execution_action"',
    ]

    for term in safety_terms:

        matches = [
            i
            for i, line in enumerate(lines, start=1)
            if term in line
        ]

        p()
        p(f"{term}")
        p(f"LINES: {matches if matches else '<NONE>'}")

    p()
    p("=" * 100)
    p("BLOCKED HELPER DETECTION")
    p("=" * 100)

    blocked_lines = [
        i
        for i, line in enumerate(lines, start=1)
        if "def _blocked" in line
    ]

    if not blocked_lines:
        p("NO _blocked HELPER FOUND")
    else:
        for i in blocked_lines:

            start = max(1, i - 5)
            end = min(len(lines), i + 35)

            p()
            p(f"--- _blocked WINDOW L{start}-L{end} ---")

            for n in range(start, end + 1):
                marker = ">>" if n == i else "  "
                p(f"{marker} L{n}: {lines[n-1]}")

p()
p("=" * 100)
p("AUDIT COMPLETE")
p("=" * 100)
p("READ ONLY")
p("NO SOURCE CHANGES")
p("NO BROKER")
p("NO LIVE EXECUTION")
p("NO ORDER CREATION")
p("NO PORTFOLIO MUTATION")
p("NO VALUATION MUTATION")
p("NO PERFORMANCE MUTATION")
p("NO RISK MUTATION")
p("=" * 100)

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
    print("COMPLETE BLOCK 98 AUDIT COPIED TO WINDOWS CLIPBOARD")
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

