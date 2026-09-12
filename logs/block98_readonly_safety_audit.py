import subprocess
from pathlib import Path

path = Path(r"services\quantitative\block98_execution_governance_bridge.py")

output = []


def p(text=""):
    print(text)
    output.append(str(text))


p("=" * 100)
p("EROS 3.0 - BLOCK 98 READ-ONLY SAFETY / RETURN PATH AUDIT")
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
    p("SOURCE LINE COUNT:")
    p(str(len(lines)))

    p()
    p("=" * 100)
    p("1. SAFETY / EXECUTION KEYWORD LOCATIONS")
    p("=" * 100)

    keywords = (
        "return {",
        "return self.",
        "return result",
        "STATUS_BLOCKED",
        '"status": "BLOCKED"',
        '"execution_blocked"',
        '"non_mutation_invariant"',
        '"broker_submission"',
        '"live_order_submission"',
        '"order_creation"',
        '"portfolio_mutation"',
        '"valuation_mutation"',
        "broker",
        "live",
        "order",
        "execution",
    )

    matches = []

    for i, line in enumerate(lines, start=1):
        lower = line.lower()

        if any(keyword.lower() in lower for keyword in keywords):
            matches.append(i)

    if not matches:
        p("NO SAFETY / EXECUTION KEYWORD LOCATIONS FOUND")
    else:

        p()
        p(f"MATCH COUNT: {len(matches)}")

        reported = set()

        for line_no in matches:

            start = max(1, line_no - 8)
            end = min(len(lines), line_no + 15)

            window = (start, end)

            if window in reported:
                continue

            reported.add(window)

            p()
            p(f"--- SOURCE WINDOW " f"L{start}-L{end} ---")

            for n in range(start, end + 1):
                marker = ">>" if n == line_no else "  "

                p(f"{marker} " f"L{n}: {lines[n-1]}")

    p()
    p("=" * 100)
    p("2. ALL RETURN STATEMENTS")
    p("=" * 100)

    return_lines = []

    for i, line in enumerate(lines, start=1):
        if line.strip().startswith("return "):
            return_lines.append(i)

    p()
    p(f"RETURN STATEMENT COUNT: {len(return_lines)}")

    if not return_lines:
        p("NO RETURN STATEMENTS FOUND")
    else:

        reported = set()

        for line_no in return_lines:

            start = max(1, line_no - 10)
            end = min(len(lines), line_no + 20)

            window = (start, end)

            if window in reported:
                continue

            reported.add(window)

            p()
            p(f"--- RETURN WINDOW " f"L{start}-L{end} ---")

            for n in range(start, end + 1):
                marker = ">>" if n == line_no else "  "

                p(f"{marker} " f"L{n}: {lines[n-1]}")

    p()
    p("=" * 100)
    p("3. BLOCKED RETURN INDICATORS")
    p("=" * 100)

    blocked_matches = []

    for i, line in enumerate(lines, start=1):

        if (
            "STATUS_BLOCKED" in line
            or '"status": "BLOCKED"' in line
            or "'status': 'BLOCKED'" in line
            or '"execution_blocked"' in line
            or '"non_mutation_invariant"' in line
        ):
            blocked_matches.append(i)

    p()
    p(f"BLOCKED / SAFETY MATCH COUNT: " f"{len(blocked_matches)}")

    if blocked_matches:

        for line_no in blocked_matches:

            start = max(1, line_no - 12)
            end = min(len(lines), line_no + 25)

            p()
            p(f"--- BLOCKED / SAFETY WINDOW " f"L{start}-L{end} ---")

            for n in range(start, end + 1):

                marker = ">>" if n == line_no else "  "

                p(f"{marker} " f"L{n}: {lines[n-1]}")

    else:
        p("NO DIRECT BLOCKED / STANDARDIZED " "SAFETY CONTRACT FOUND.")

    p()
    p("=" * 100)
    p("4. EXPECTED SAFETY CONTRACT")
    p("=" * 100)

    p('"execution_blocked": True')
    p('"non_mutation_invariant": True')
    p('"broker_submission": False')
    p('"live_order_submission": False')

    p()
    p("=" * 100)
    p("AUDIT RULE")
    p("=" * 100)

    p("READ ONLY")
    p("NO SOURCE CHANGES")
    p("NO BROKER")
    p("NO LIVE EXECUTION")
    p("NO ORDER CREATION")
    p("NO PORTFOLIO MUTATION")
    p("NO VALUATION MUTATION")
    p("NO AUTOMATIC REPAIR")

    p()
    p("=" * 100)
    p("BLOCK 98 AUDIT COMPLETE")
    p("=" * 100)

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
    print("COMPLETE BLOCK 98 AUDIT COPIED TO WINDOWS CLIPBOARD")
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
