from pathlib import Path
import subprocess

PATH = Path(r"services\quantitative\block98_execution_governance_bridge.py")

output = []

def p(text=""):
    text = str(text)
    print(text)
    output.append(text)

p("=" * 100)
p("EROS 3.0 - BLOCK 98 ACTUAL RETURN / BLOCKED PATH SAFETY TRACE")
p("=" * 100)

p()
p("SOURCE:")
p(str(PATH))

if not PATH.exists():
    p()
    p("ERROR: SOURCE FILE NOT FOUND")
else:
    source = PATH.read_text(
        encoding="utf-8-sig"
    )

    lines = source.splitlines()

    p()
    p("SOURCE LINES: " + str(len(lines)))

    p()
    p("=" * 100)
    p("SEARCH RESULTS")
    p("=" * 100)

    matches = []

    keywords = [
        "return {",
        "STATUS_BLOCKED",
        '"status"',
        "'status'",
        "blocked",
        "broker_submission",
        "live_order_submission",
        "execution_blocked",
        "non_mutation_invariant",
        "portfolio_mutation",
        "valuation_mutation",
        "performance_mutation",
        "risk_mutation",
        "optimization",
        "order_creation",
    ]

    for number, line in enumerate(lines, start=1):
        lower = line.lower()

        if any(keyword.lower() in lower for keyword in keywords):
            matches.append(number)

    if not matches:
        p("NO SAFETY-RELATED LINES FOUND")
    else:
        p("MATCHED SOURCE LINES: " + str(len(matches)))

        reported = set()

        for number in matches:
            start = max(1, number - 8)
            end = min(len(lines), number + 15)

            window = (start, end)

            if window in reported:
                continue

            reported.add(window)

            p()
            p("--- SOURCE WINDOW L" + str(start) + "-L" + str(end) + " ---")

            for n in range(start, end + 1):
                if n == number:
                    prefix = ">>"
                else:
                    prefix = "  "

                p(
                    prefix
                    + " L"
                    + str(n)
                    + ": "
                    + lines[n - 1]
                )

    p()
    p("=" * 100)
    p("BLOCK 98 RETURN STATEMENT LOCATIONS")
    p("=" * 100)

    return_lines = []

    for number, line in enumerate(lines, start=1):
        if line.strip().startswith("return "):
            return_lines.append(number)

    if not return_lines:
        p("NO RETURN STATEMENTS FOUND")
    else:
        p("RETURN COUNT: " + str(len(return_lines)))

        for number in return_lines:
            p("RETURN AT L" + str(number) + ": " + lines[number - 1])

    p()
    p("=" * 100)
    p("EXPECTED STANDARD SAFETY CONTRACT")
    p("=" * 100)

    p("execution_blocked = True")
    p("non_mutation_invariant = True")
    p("broker_submission = False")
    p("live_order_submission = False")

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
    p("NO PORTFOLIO MUTATION")
    p("NO VALUATION MUTATION")

clipboard_text = "\n".join(output)

p()
p("=" * 100)

try:
    subprocess.run(
        ["clip.exe"],
        input=clipboard_text,
        text=True,
        check=True,
    )

    print("CLIPBOARD : PASS")
    print("=" * 100)
    print("COMPLETE BLOCK 98 TRACE COPIED TO WINDOWS CLIPBOARD")
    print()
    print(">>> RETURN TO CHATGPT AND PRESS CTRL+V <<<")
    print("=" * 100)

except Exception as exc:
    print("CLIPBOARD : FAIL")
    print(type(exc).__name__ + ": " + str(exc))
    print("=" * 100)
