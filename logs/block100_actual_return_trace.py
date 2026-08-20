from pathlib import Path
import subprocess

path = Path(
    r"services\quantitative\block100_paper_execution_fill_gate.py"
)

out = []

def p(text=""):
    text = str(text)
    print(text)
    out.append(text)

p("=" * 100)
p("EROS 3.0 - BLOCK 100 ACTUAL RETURN / BLOCKED PATH TRACE")
p("=" * 100)

p()
p("SOURCE: " + str(path))

if not path.exists():
    p("SOURCE ERROR: FILE NOT FOUND")
else:

    lines = path.read_text(
        encoding="utf-8-sig"
    ).splitlines()

    p("SOURCE : FOUND")
    p("SOURCE LINES : " + str(len(lines)))
    p("BOM-SAFE READ : PASS")

    p()
    p("=" * 100)
    p("BLOCKED / SAFETY RELATED LOCATIONS")
    p("=" * 100)

    keywords = [
        "STATUS_BLOCKED",
        "execution_blocked",
        "non_mutation_invariant",
        "broker_submission",
        "live_order_submission",
        "portfolio_mutation",
        "valuation_mutation",
        "performance_mutation",
        "risk_mutation",
        "optimization",
        "order_creation",
    ]

    found = []

    for i, line in enumerate(lines, start=1):
        for keyword in keywords:
            if keyword in line:
                found.append(i)
                break

    found = sorted(set(found))

    p("MATCHING SOURCE LINES : " + str(len(found)))

    shown = set()

    for line_no in found:

        start = max(1, line_no - 10)
        end = min(len(lines), line_no + 20)

        key = (start, end)

        if key in shown:
            continue

        shown.add(key)

        p()
        p(
            "--- SOURCE WINDOW L"
            + str(start)
            + "-L"
            + str(end)
            + " ---"
        )

        for n in range(start, end + 1):

            marker = ">>" if n == line_no else "  "

            p(
                marker
                + " L"
                + str(n)
                + ": "
                + lines[n - 1]
            )

    p()
    p("=" * 100)
    p("ALL RETURN STATEMENTS")
    p("=" * 100)

    returns = []

    for i, line in enumerate(lines, start=1):
        if line.strip().startswith("return "):
            returns.append(i)

    p("RETURN COUNT : " + str(len(returns)))

    for index, line_no in enumerate(returns, start=1):

        start = max(1, line_no - 8)
        end = min(len(lines), line_no + 25)

        p()
        p(
            "--- RETURN #"
            + str(index)
            + " WINDOW L"
            + str(start)
            + "-L"
            + str(end)
            + " ---"
        )

        for n in range(start, end + 1):

            marker = ">>" if n == line_no else "  "

            p(
                marker
                + " L"
                + str(n)
                + ": "
                + lines[n - 1]
            )

    p()
    p("=" * 100)
    p("CERTIFY METHOD")
    p("=" * 100)

    certify_start = None

    for i, line in enumerate(lines, start=1):
        if line.strip().startswith("def certify("):
            certify_start = i
            break

    if certify_start is None:

        p("CERTIFY : NOT FOUND")

    else:

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
            "CERTIFY RANGE : L"
            + str(certify_start)
            + "-L"
            + str(certify_end)
        )

        for n in range(certify_start, certify_end + 1):
            p(
                "L"
                + str(n)
                + ": "
                + lines[n - 1]
            )

    p()
    p("=" * 100)
    p("EXPECTED STANDARD SAFETY CONTRACT")
    p("=" * 100)

    p("execution_blocked = True")
    p("non_mutation_invariant = True")
    p("broker_submission = False")
    p("live_order_submission = False")
    p("portfolio_mutation = False")
    p("valuation_mutation = False")
    p("performance_mutation = False")
    p("risk_mutation = False")
    p("optimization = False")
    p("order_creation = False")

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

clipboard_text = "\n".join(out)

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
    print(">>> PRESS CTRL+V IN CHATGPT <<<")
    print("=" * 100)

except Exception as exc:

    print()
    print("=" * 100)
    print("CLIPBOARD : FAIL")
    print("=" * 100)
    print(type(exc).__name__, str(exc))
    print("=" * 100)

