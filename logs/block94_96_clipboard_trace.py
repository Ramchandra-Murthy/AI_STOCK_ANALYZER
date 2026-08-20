from pathlib import Path
import subprocess

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
p("EROS 3.0 - BLOCK 94-96 ACTUAL EARLY BLOCKED RETURN TRACE")
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

    # BOM-safe source reading
    lines = path.read_text(
        encoding="utf-8-sig"
    ).splitlines()

    p()
    p("SEARCHING FOR ACTUAL BLOCKED RETURN PATHS...")

    found_any = False
    reported_windows = set()

    for i, line in enumerate(lines, start=1):

        stripped = line.strip()

        match = (
            stripped.startswith("return {")
            or '"status": "BLOCKED"' in line
            or '"status": STATUS_BLOCKED' in line
            or '"gate_status": STATUS_BLOCKED' in line
            or '"decision_status": STATUS_BLOCKED' in line
            or '"readiness_status": STATUS_BLOCKED' in line
            or '"broker_submission": False' in line
            or '"live_order_submission": False' in line
        )

        if not match:
            continue

        found_any = True

        start = max(1, i - 15)
        end = min(len(lines), i + 30)

        window = (start, end)

        if window in reported_windows:
            continue

        reported_windows.add(window)

        p()
        p(f"--- SOURCE WINDOW L{start}-L{end} ---")

        for n in range(start, end + 1):
            marker = ">>" if n == i else "  "
            p(f"{marker} L{n}: {lines[n-1]}")

    if not found_any:
        p()
        p("NO DIRECT BLOCKED RETURN DICTIONARY MATCH FOUND.")

        p()
        p("Searching all return statements...")

        for i, line in enumerate(lines, start=1):

            if line.strip().startswith("return "):

                start = max(1, i - 10)
                end = min(len(lines), i + 20)

                p()
                p(f"--- RETURN WINDOW L{start}-L{end} ---")

                for n in range(start, end + 1):
                    marker = ">>" if n == i else "  "
                    p(f"{marker} L{n}: {lines[n-1]}")

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
p("IMPORTANT:")
p("READ ONLY")
p("NO SOURCE CHANGES")
p("NO BROKER")
p("NO LIVE EXECUTION")
p("NO ORDER CREATION")
p("NO PORTFOLIO MUTATION")
p("NO VALUATION MUTATION")

p("=" * 100)

# ------------------------------------------------------------
# COPY EVERYTHING TO WINDOWS CLIPBOARD
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
    print("NOW RETURN TO CHATGPT AND PRESS:")
    print("CTRL + V")
    print("=" * 100)

except Exception as exc:

    print()
    print("=" * 100)
    print("CLIPBOARD : FAIL")
    print("=" * 100)
    print(type(exc).__name__, str(exc))
    print("=" * 100)

