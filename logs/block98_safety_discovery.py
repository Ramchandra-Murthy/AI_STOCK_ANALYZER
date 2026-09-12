import subprocess
from pathlib import Path

path = Path(r"services\quantitative\block98_execution_governance_bridge.py")

output = []


def p(text=""):
    print(text)
    output.append(str(text))


p("=" * 100)
p("EROS 3.0 - BLOCK 98 EXECUTION GOVERNANCE BRIDGE SAFETY DISCOVERY")
p("=" * 100)

p()
p("SOURCE:")
p(str(path))

if not path.exists():
    p("ERROR: SOURCE FILE NOT FOUND")
else:
    # BOM-safe read
    lines = path.read_text(encoding="utf-8-sig").splitlines()

    p()
    p(f"TOTAL SOURCE LINES: {len(lines)}")

    p()
    p("=" * 100)
    p("1. ALL RETURN STATEMENTS")
    p("=" * 100)

    return_count = 0

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        if stripped.startswith("return "):
            return_count += 1

            start = max(1, i - 8)
            end = min(len(lines), i + 20)

            p()
            p(f"--- RETURN #{return_count} WINDOW L{start}-L{end} ---")

            for n in range(start, end + 1):
                marker = ">>" if n == i else "  "
                p(f"{marker} L{n}: {lines[n-1]}")

    p()
    p(f"TOTAL RETURN STATEMENTS FOUND: {return_count}")

    p()
    p("=" * 100)
    p("2. SAFETY-RELATED LOCATIONS")
    p("=" * 100)

    keywords = (
        "BLOCKED",
        "STATUS_BLOCKED",
        "execution_blocked",
        "non_mutation_invariant",
        "broker_submission",
        "live_order_submission",
        "order_creation",
        "portfolio_mutation",
        "valuation_mutation",
        "risk_mutation",
        "execution",
        "authorization",
        "governance",
    )

    found = set()

    for i, line in enumerate(lines, start=1):
        if any(keyword in line for keyword in keywords):

            start = max(1, i - 8)
            end = min(len(lines), i + 15)

            key = (start, end)

            if key in found:
                continue

            found.add(key)

            p()
            p(f"--- SAFETY WINDOW L{start}-L{end} ---")

            for n in range(start, end + 1):
                marker = ">>" if n == i else "  "
                p(f"{marker} L{n}: {lines[n-1]}")

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
p("IMPORTANT")
p("=" * 100)
p("READ ONLY")
p("NO SOURCE CHANGES")
p("NO BACKUP CHANGES")
p("NO BROKER")
p("NO LIVE EXECUTION")
p("NO ORDER CREATION")
p("NO PORTFOLIO MUTATION")
p("NO VALUATION MUTATION")

p()
p("=" * 100)
p("DISCOVERY COMPLETE")
p("=" * 100)

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
    print("COMPLETE BLOCK 98 DISCOVERY COPIED TO WINDOWS CLIPBOARD")
    print("RETURN TO CHATGPT AND PRESS CTRL+V")
    print("=" * 100)

except Exception as exc:
    print()
    print("=" * 100)
    print("CLIPBOARD : FAIL")
    print("=" * 100)
    print(type(exc).__name__, str(exc))
    print("=" * 100)
