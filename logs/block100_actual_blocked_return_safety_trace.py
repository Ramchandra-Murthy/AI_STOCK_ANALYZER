from pathlib import Path
import subprocess

path = Path(
    r"services\quantitative\block100_paper_execution_fill_gate.py"
)

output = []

def p(text=""):
    text = str(text)
    print(text)
    output.append(text)

p("=" * 100)
p("EROS 3.0 - BLOCK 100 ACTUAL BLOCKED RETURN / SAFETY PATH TRACE")
p("=" * 100)

p()
p("SOURCE:")
p(str(path))

if not path.exists():
    p()
    p("SOURCE ERROR: FILE NOT FOUND")
else:

    lines = path.read_text(
        encoding="utf-8-sig"
    ).splitlines()

    p()
    p("SOURCE CHECK")
    p("-" * 100)
    p("SOURCE : FOUND")
    p(f"LINES  : {len(lines)}")
    p("BOM-SAFE READ : PASS")

    # ------------------------------------------------------------
    # 1. Locate class
    # ------------------------------------------------------------

    p()
    p("=" * 100)
    p("CLASS / METHOD DISCOVERY")
    p("=" * 100)

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        if (
            stripped.startswith("class EROSBlock100")
            or stripped.startswith("def certify")
            or stripped.startswith("def _blocked")
            or stripped.startswith("def ")
        ):
            p(f"L{i}: {line}")

    # ------------------------------------------------------------
    # 2. Search for blocked/safety-related source lines
    # ------------------------------------------------------------

    p()
    p("=" * 100)
    p("BLOCKED / SAFETY RETURN SEARCH")
    p("=" * 100)

    keywords = [
        "STATUS_BLOCKED",
        '"status": "BLOCKED"',
        "'status': 'BLOCKED'",
        '"execution_status"',
        "'execution_status'",
        '"execution_blocked"',
        "'execution_blocked'",
        '"non_mutation_invariant"',
        "'non_mutation_invariant'",
        '"broker_submission"',
        "'broker_submission'",
        '"live_order_submission"',
        "'live_order_submission'",
        '"portfolio_mutation"',
        "'portfolio_mutation'",
        '"valuation_mutation"',
        "'valuation_mutation'",
        '"performance_mutation'",
        "'performance_mutation'",
        '"risk_mutation"',
        "'risk_mutation'",
        '"optimization"',
        "'optimization'",
        '"order_creation"',
        "'order_creation'",
    ]

    matches = []

    for i, line in enumerate(lines, start=1):
        if any(keyword in line for keyword in keywords):
            matches.append(i)

    if not matches:
        p("NO SAFETY / BLOCKED KEYWORDS FOUND")
    else:
        reported = set()

        for line_no in matches:

            start = max(1, line_no - 12)
            end = min(len(lines), line_no + 25)

            window = (start, end)

            if window in reported:
                continue

            reported.add(window)

            p()
            p(
                f"--- SOURCE WINDOW L{start}-L{end} ---"
            )

            for n in range(start, end + 1):
                marker = ">>" if n == line_no else "  "
                p(
                    f"{marker} L{n}: {lines[n-1]}"
                )

    # ------------------------------------------------------------
    # 3. Locate ALL return statements
    # ------------------------------------------------------------

    p()
    p("=" * 100)
    p("ALL RETURN STATEMENTS")
    p("=" * 100)

    return_lines = []

    for i, line in enumerate(lines, start=1):

        stripped = line.strip()

        if stripped.startswith("return "):
            return_lines.append(i)

    p(f"RETURN COUNT: {len(return_lines)}")

    for index, line_no in enumerate(return_lines, start=1):

        start = max(1, line_no - 8)
        end = min(len(lines), line_no + 25)

        p()
        p(
            f"--- RETURN #{index} WINDOW L{start}-L{end} ---"
        )

        for n in range(start, end + 1):
            marker = ">>" if n == line_no else "  "
            p(
                f"{marker} L{n}: {lines[n-1]}"
            )

    # ------------------------------------------------------------
    # 4. Special focus on certify()
    # ------------------------------------------------------------

    p()
    p("=" * 100)
    p("CERTIFY METHOD TRACE")
    p("=" * 100)

    certify_start = None

    for i, line in enumerate(lines, start=1):

        if line.strip().startswith("def certify("):
            certify_start = i
            break

    if certify_start is None:

        p("CERTIFY METHOD : NOT FOUND")

    else:

        p(f"CERTIFY START : L{certify_start}")

        # Find next method at same indentation.
        certify_end = len(lines)

        for i in range(certify_start + 1, len(lines) + 1):

            line = lines[i - 1]

            if (
                line.startswith("    def ")
                and i > certify_start
            ):
                certify_end = i - 1
                break

        p(
            f"CERTIFY RANGE : L{certify_start}-L{certify_end}"
        )

        for n in range(certify_start, certify_end + 1):
            p(
                f"L{n}: {lines[n-1]}"
            )

    # ------------------------------------------------------------
    # 5. Expected contract
    # ------------------------------------------------------------

    p()
    p("=" * 100)
    p("EXPECTED STANDARD SAFETY CONTRACT")
    p("=" * 100)

    p('"execution_blocked": True')
    p('"non_mutation_invariant": True')
    p('"broker_submission": False')
    p('"live_order_submission": False')
    p('"portfolio_mutation": False')
    p('"valuation_mutation": False')
    p('"performance_mutation": False')
    p('"risk_mutation": False')
    p('"optimization": False')
    p('"order_creation": False')

    p()
    p("=" * 100)
    p("IMPORTANT")
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

    p()
    p("=" * 100)
    p("TRACE COMPLETE")
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
    print("COMPLETE BLOCK 100 TRACE COPIED TO WINDOWS CLIPBOARD")
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

