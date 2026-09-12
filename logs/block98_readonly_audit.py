import subprocess
from pathlib import Path

path = Path(r"services\quantitative\block98_execution_governance_bridge.py")

output = []


def p(text=""):
    print(text)
    output.append(str(text))


p("=" * 100)
p("EROS 3.0 - BLOCK 98 EXECUTION GOVERNANCE BRIDGE READ-ONLY AUDIT")
p("=" * 100)

p()
p("SOURCE")
p(str(path))

if not path.exists():
    p()
    p("ERROR: SOURCE FILE NOT FOUND")
else:
    source = path.read_text(encoding="utf-8-sig")
    lines = source.splitlines()

    p()
    p(f"TOTAL SOURCE LINES: {len(lines)}")

    p()
    p("=" * 100)
    p("COMPLETE BLOCK 98 SOURCE")
    p("=" * 100)

    for i, line in enumerate(lines, start=1):
        p(f"L{i}: {line}")

    p()
    p("=" * 100)
    p("SAFETY-RELEVANT LOCATIONS")
    p("=" * 100)

    keywords = (
        "def ",
        "return ",
        "BLOCKED",
        "execution_blocked",
        "non_mutation_invariant",
        "broker_submission",
        "live_order_submission",
        "order_creation",
        "portfolio_mutation",
        "valuation_mutation",
        "risk_mutation",
        "optimization",
        "execute",
        "execution",
        "broker",
        "order",
        "mutation",
        "authorization",
        "governance",
    )

    for i, line in enumerate(lines, start=1):
        lower = line.lower()

        if any(keyword.lower() in lower for keyword in keywords):
            p(f"L{i}: {line}")

p()
p("=" * 100)
p("AUDIT COMPLETE")
p("=" * 100)
p("READ ONLY")
p("NO SOURCE CHANGES")
p("NO BROKER")
p("NO LIVE EXECUTION")
p("NO ORDER CREATION")
p("NO MUTATION")
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
    print("NOW PRESS CTRL+V IN CHATGPT")
    print("=" * 100)

except Exception as exc:
    print()
    print("=" * 100)
    print("CLIPBOARD : FAIL")
    print("=" * 100)
    print(type(exc).__name__, str(exc))
    print("=" * 100)
