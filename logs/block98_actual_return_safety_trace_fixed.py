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
p("EROS 3.0 - BLOCK 98 ACTUAL RETURN / BLOCKED PATH TRACE")
p("=" * 100)

p()
p("SOURCE:")
p(str(path))

if not path.exists():
    p()
    p("ERROR: SOURCE FILE NOT FOUND")
else:

    # BOM-safe source reading
    lines = path.read_text(
        encoding="utf-8-sig"
    ).splitlines()

    p()
    p(f"SOURCE LINES: {len(lines)}")

    p()
    p("=" * 100)
    p("SEARCHING FOR RETURN / BLOCKED / EXECUTION SAFETY PATHS")
    p("=" * 100)

    found = False
    windows = set()

    for i, line in enumerate(lines, start=1):

        stripped = line.strip()

        match = (
            stripped.startswith("return ")
            or stripped.startswith("return {")
            or '"status": "BLOCKED"' in line
            or '"status": STATUS_BLOCKED' in line
            or '"gate_status": STATUS_BLOCKED' in line
            or '"execution_blocked"' in line
            or '"non_mutation_invariant"' in line
            or '"broker_submission"' in line
            or '"live_order_submission"' in line
            or '"order_creation"' in line
            or '"paper_execution"' in line
            or '"execution_intent"' in line
            or '"authorization"' in line
        )

        if not match:
            continue

        found = True

        start = max(1, i - 15)
        end = min(len(lines), i + 30)

        window = (start, end)

        if window in windows:
            continue

        windows.add(window)

        p()
        p("-" * 100)
        p(f"SOURCE WINDOW L{start}-L{end}")
        p("-" * 100)

        for n in range(start, end + 1):

            marker = ">>" if n == i else "  "

            p(
                f"{marker} L{n}: {lines[n - 1]}"
            )

    if not found:

        p()
        p("=" * 100)
        p("NO DIRECT SAFETY/RETURN MATCH FOUND")
        p("=" * 100)

        p()
        p("ALL RETURN STATEMENTS:")

        return_found = False

        for i, line in enumerate(lines, start=1):

            if line.strip().startswith("return "):

                return_found = True

                start = max(1, i - 10)
                end = min(len(lines), i + 25)

                p()
                p(
                    f"--- RETURN WINDOW L{start}-L{end} ---"
                )

                for n in range(start, end + 1):

                    marker = ">>" if n == i else "  "

                    p(
                        f"{marker} L{n}: {lines[n - 1]}"
                    )

        if not return_found:
            p("NO RETURN STATEMENTS FOUND.")


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
# COPY COMPLETE TRACE TO WINDOWS CLIPBOARD
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
    print("COMPLETE BLOCK 98 TRACE COPIED TO WINDOWS CLIPBOARD")
    print()
    print(">>> RETURN TO CHATGPT AND PRESS CTRL+V <<<")
    print("=" * 100)

except Exception as exc:

    print()
    print("=" * 100)
    print("CLIPBOARD : FAIL")
    print("=" * 100)
    print(
        type(exc).__name__,
        str(exc)
    )
    print("=" * 100)

