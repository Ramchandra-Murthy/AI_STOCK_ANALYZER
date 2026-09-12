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
p("EROS 3.0 - BLOCK 94-96 BOM-SAFE ACTUAL BLOCKED RETURN TRACE")
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

    # BOM-safe source reading
    lines = path.read_text(encoding="utf-8-sig").splitlines()

    p(f"SOURCE LINES: {len(lines)}")

    found = False

    # --------------------------------------------------------------
    # Locate all return statements and BLOCKED-related safety fields
    # --------------------------------------------------------------

    for i, line in enumerate(lines, start=1):

        stripped = line.strip()

        is_candidate = (
            stripped.startswith("return ")
            or "STATUS_BLOCKED" in line
            or '"status"' in line
            or '"gate_status"' in line
            or '"decision_status"' in line
            or '"readiness_status"' in line
            or '"broker_submission"' in line
            or '"live_order_submission"' in line
            or '"non_mutation_invariant"' in line
            or '"execution_blocked"' in line
        )

        if not is_candidate:
            continue

        found = True

        start = max(1, i - 8)
        end = min(len(lines), i + 20)

        p()
        p(f"--- SOURCE WINDOW L{start}-L{end} ---")

        for n in range(start, end + 1):
            marker = ">>" if n == i else "  "
            p(f"{marker} L{n}: {lines[n-1]}")

    if not found:
        p()
        p("NO RELEVANT RETURN/SAFETY LOCATIONS FOUND")

p()
p("=" * 100)
p("EXPECTED STANDARD SAFETY CONTRACT")
p("=" * 100)
p('"execution_blocked": True')
p('"non_mutation_invariant": True')
p('"broker_submission": False')
p('"live_order_submission": False')

p()
p("=" * 100)
p("TRACE COMPLETE")
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

# --------------------------------------------------------------
# COPY EVERYTHING TO WINDOWS CLIPBOARD
# --------------------------------------------------------------

clipboard_text = "\r\n".join(output)

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
    print("NOW PRESS CTRL+V IN CHATGPT")
    print("=" * 100)

except Exception as exc:

    print()
    print("=" * 100)
    print("CLIPBOARD : FAIL")
    print("=" * 100)
    print(type(exc).__name__, str(exc))
    print("=" * 100)
