import subprocess
from pathlib import Path

path = Path(r"services\quantitative\block98_execution_governance_bridge.py")

output = []


def p(text=""):
    print(text)
    output.append(str(text))


p("=" * 100)
p("EROS 3.0 - BLOCK 98 EXECUTION GOVERNANCE BRIDGE")
p("READ-ONLY RETURN / SAFETY CONTRACT TRACE")
p("=" * 100)

p()
p(f"SOURCE: {path}")

if not path.exists():
    p("ERROR: SOURCE FILE NOT FOUND")
else:
    # BOM-safe source reading
    lines = path.read_text(encoding="utf-8-sig").splitlines()

    p()
    p(f"SOURCE LINES: {len(lines)}")

    p()
    p("SEARCHING FOR BLOCKED RETURN PATHS...")

    found = False
    reported = set()

    for i, line in enumerate(lines, start=1):

        stripped = line.strip()

        match = (
            stripped.startswith("return {")
            or '"status": "BLOCKED"' in line
            or '"status": STATUS_BLOCKED' in line
            or '"governance_status": STATUS_BLOCKED' in line
            or '"execution_status": STATUS_BLOCKED' in line
            or '"broker_submission": False' in line
            or '"live_order_submission": False' in line
            or '"execution_blocked": True' in line
            or '"non_mutation_invariant": True' in line
        )

        if not match:
            continue

        found = True

        start = max(1, i - 15)
        end = min(len(lines), i + 30)

        window = (start, end)

        if window in reported:
            continue

        reported.add(window)

        p()
        p(f"--- SOURCE WINDOW L{start}-L{end} ---")

        for n in range(start, end + 1):
            marker = ">>" if n == i else "  "
            p(f"{marker} L{n}: {lines[n-1]}")

    if not found:
        p()
        p("NO DIRECT SAFETY/BLOCKED RETURN MATCH FOUND.")

        p()
        p("SEARCHING ALL RETURN STATEMENTS...")

        for i, line in enumerate(lines, start=1):

            if line.strip().startswith("return "):

                start = max(1, i - 12)
                end = min(len(lines), i + 25)

                p()
                p(f"--- RETURN WINDOW L{start}-L{end} ---")

                for n in range(start, end + 1):
                    marker = ">>" if n == i else "  "
                    p(f"{marker} L{n}: {lines[n-1]}")

p()
p("=" * 100)
p("EXPECTED STANDARD SAFETY CONTRACT")
p("=" * 100)

p('  "execution_blocked": True')
p('  "non_mutation_invariant": True')
p('  "broker_submission": False')
p('  "live_order_submission": False')

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
p("NO OPTIMIZATION")

# Copy complete output to Windows clipboard
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
    print("COMPLETE BLOCK 98 TRACE COPIED TO WINDOWS CLIPBOARD")
    print()
    print("NOW RETURN TO CHATGPT AND PRESS CTRL+V")
    print("=" * 100)

except Exception as exc:

    print()
    print("=" * 100)
    print("CLIPBOARD : FAIL")
    print("=" * 100)
    print(type(exc).__name__, str(exc))
    print("=" * 100)
