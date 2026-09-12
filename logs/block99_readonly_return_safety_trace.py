import subprocess
from pathlib import Path

SOURCE = Path(r"services\quantitative\block99_execution_intent_authorization_gate.py")

output = []


def p(text=""):
    text = str(text)
    print(text)
    output.append(text)


p("=" * 100)
p("EROS 3.0 - BLOCK 99 READ-ONLY RETURN / SAFETY CONTRACT TRACE")
p("=" * 100)

p()
p("SOURCE:")
p(str(SOURCE))

if not SOURCE.exists():
    p("SOURCE ERROR: FILE NOT FOUND")
else:

    source = SOURCE.read_text(encoding="utf-8-sig")

    lines = source.splitlines()

    p()
    p("SOURCE : FOUND")
    p(f"SOURCE LINE COUNT : {len(lines)}")
    p("BOM-SAFE READ : PASS")

    # ------------------------------------------------------------
    # SEARCH FOR SAFETY / EXECUTION / BLOCKED LOCATIONS
    # ------------------------------------------------------------

    keywords = (
        "def _blocked",
        "return {",
        '"status": STATUS_BLOCKED',
        '"status": "BLOCKED"',
        '"gate_status": STATUS_BLOCKED',
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
    )

    matches = []

    for i, line in enumerate(lines, start=1):
        if any(keyword in line for keyword in keywords):
            matches.append(i)

    p()
    p("=" * 100)
    p("SAFETY / RETURN KEYWORD LOCATIONS")
    p("=" * 100)

    p(f"MATCH COUNT : {len(matches)}")

    reported = set()

    for line_no in matches:

        start = max(1, line_no - 8)
        end = min(len(lines), line_no + 18)

        key = (start, end)

        if key in reported:
            continue

        reported.add(key)

        p()
        p("-" * 100)
        p(f"SOURCE WINDOW L{start}-L{end}")
        p("-" * 100)

        for n in range(start, end + 1):
            marker = ">>" if n == line_no else "  "
            p(f"{marker} L{n}: {lines[n-1]}")

    # ------------------------------------------------------------
    # IMPORT / AST-SAFE CHECK
    # ------------------------------------------------------------

    p()
    p("=" * 100)
    p("IMPORT / SOURCE VALIDATION")
    p("=" * 100)

    try:
        import ast

        ast.parse(source, filename=str(SOURCE))

        p("AST PARSE : PASS")

    except Exception as exc:

        p("AST PARSE : FAIL")
        p(f"{type(exc).__name__}: {exc}")

    # ------------------------------------------------------------
    # IMPORTANT SAFETY STATEMENT
    # ------------------------------------------------------------

    p()
    p("=" * 100)
    p("AUDIT POLICY")
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
    p("BLOCK 99 SOURCE TRACE COMPLETE")
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
    print("COMPLETE BLOCK 99 TRACE COPIED TO WINDOWS CLIPBOARD")
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
