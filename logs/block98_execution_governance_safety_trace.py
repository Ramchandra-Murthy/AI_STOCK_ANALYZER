import subprocess
from pathlib import Path

path = Path(r"services\quantitative\block98_execution_governance_bridge.py")

output = []


def p(text=""):
    print(text)
    output.append(str(text))


p("=" * 100)
p("EROS 3.0 - BLOCK 98 EXECUTION GOVERNANCE BRIDGE READ-ONLY SAFETY TRACE")
p("=" * 100)

p()
p("SOURCE:")
p(str(path))

if not path.exists():
    p()
    p("SOURCE ERROR: FILE NOT FOUND")
else:

    # BOM-safe reading
    lines = path.read_text(encoding="utf-8-sig").splitlines()

    p()
    p("SOURCE LINE COUNT:")
    p(str(len(lines)))

    p()
    p("=" * 100)
    p("METHOD / FUNCTION DISCOVERY")
    p("=" * 100)

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        if (
            stripped.startswith("def ")
            or stripped.startswith("async def ")
            or stripped.startswith("class ")
        ):
            p(f"L{i}: {line}")

    p()
    p("=" * 100)
    p("BLOCKED / DENY / SAFETY RETURN TRACE")
    p("=" * 100)

    found = False
    windows = set()

    keywords = (
        '"status": "BLOCKED"',
        '"status": STATUS_BLOCKED',
        '"gate_status": STATUS_BLOCKED',
        '"decision_status": STATUS_BLOCKED',
        '"authorization_status": STATUS_BLOCKED',
        '"execution_status": STATUS_BLOCKED',
        '"readiness_status": STATUS_BLOCKED',
        '"broker_submission": False',
        '"live_order_submission": False',
        '"execution_blocked"',
        '"non_mutation_invariant"',
        '"order_creation"',
        '"portfolio_mutation"',
        '"valuation_mutation"',
        "return {",
        "return self._blocked",
        "return _blocked",
        "raise ",
    )

    for i, line in enumerate(lines, start=1):

        if not any(keyword in line for keyword in keywords):
            continue

        found = True

        start = max(1, i - 15)
        end = min(len(lines), i + 30)

        window = (start, end)

        if window in windows:
            continue

        windows.add(window)

        p()
        p(f"--- SOURCE WINDOW L{start}-L{end} ---")

        for n in range(start, end + 1):
            marker = ">>" if n == i else "  "
            p(f"{marker} L{n}: {lines[n-1]}")

    if not found:
        p()
        p("NO DIRECT BLOCKED / SAFETY RETURN MATCH FOUND.")

    p()
    p("=" * 100)
    p("ALL RETURN STATEMENTS")
    p("=" * 100)

    return_found = False

    for i, line in enumerate(lines, start=1):

        if line.strip().startswith("return "):

            return_found = True

            start = max(1, i - 8)
            end = min(len(lines), i + 20)

            p()
            p(f"--- RETURN WINDOW L{start}-L{end} ---")

            for n in range(start, end + 1):
                marker = ">>" if n == i else "  "
                p(f"{marker} L{n}: {lines[n-1]}")

    if not return_found:
        p("NO RETURN STATEMENTS FOUND.")

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
    print("COMPLETE BLOCK 98 TRACE COPIED TO WINDOWS CLIPBOARD")
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
