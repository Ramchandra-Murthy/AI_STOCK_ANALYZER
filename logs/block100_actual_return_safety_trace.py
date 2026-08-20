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
p("EROS 3.0 - BLOCK 100 ACTUAL RETURN / SAFETY PATH TRACE")
p("=" * 100)

p("")
p("SOURCE:")
p(str(path))

if not path.exists():
    p("SOURCE ERROR: FILE NOT FOUND")
else:
    source = path.read_text(
        encoding="utf-8-sig"
    )

    lines = source.splitlines()

    p("")
    p("SOURCE CHECK")
    p("-" * 60)
    p("SOURCE : FOUND")
    p(f"SIZE   : {path.stat().st_size} bytes")
    p("BOM-SAFE READ : PASS")
    p(f"SOURCE LINES: {len(lines)}")

    p("")
    p("=" * 100)
    p("SEARCHING FOR BLOCK 100 RETURN PATHS")
    p("=" * 100)

    matches = []

    keywords = (
        "return {",
        '"status":',
        '"execution_status":',
        '"fill_status":',
        '"execution_blocked":',
        '"non_mutation_invariant":',
        "def _blocked",
        "def certify",
        "def execute",
        "def fill",
        "def paper_execute",
    )

    for i, line in enumerate(lines, start=1):
        if any(keyword in line for keyword in keywords):
            matches.append(i)

    reported = set()

    for line_no in matches:
        start = max(1, line_no - 8)
        end = min(len(lines), line_no + 18)

        key = (start, end)

        if key in reported:
            continue

        reported.add(key)

        p("")
        p(f"--- SOURCE WINDOW L{start}-L{end} ---")

        for n in range(start, end + 1):
            marker = ">>" if n == line_no else "  "
            p(f"{marker} L{n}: {lines[n - 1]}")

    p("")
    p("=" * 100)
    p("BLOCK 100 PUBLIC METHODS")
    p("=" * 100)

    method_names = (
        "certify",
        "execute",
        "fill",
        "paper_execute",
        "validate",
        "evaluate",
        "authorize",
        "check",
        "snapshot",
    )

    for name in method_names:
        found = False

        for line in lines:
            stripped = line.strip()

            if (
                stripped.startswith(f"def {name}(")
                or stripped.startswith(f"async def {name}(")
            ):
                found = True
                break

        p(f"{name:20s}: {'FOUND' if found else 'ABSENT'}")

    p("")
    p("=" * 100)
    p("SAFETY FIELD OCCURRENCES")
    p("=" * 100)

    safety_fields = (
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
    )

    for field in safety_fields:
        count = sum(
            1
            for line in lines
            if field in line
        )

        p(f"{field:30s}: {count}")

    p("")
    p("=" * 100)
    p("TRACE COMPLETE")
    p("=" * 100)

    p("")
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

clipboard_text = "\n".join(output)

try:
    subprocess.run(
        ["clip.exe"],
        input=clipboard_text,
        text=True,
        check=True,
    )

    print("")
    print("=" * 100)
    print("CLIPBOARD : PASS")
    print("=" * 100)
    print("COMPLETE BLOCK 100 TRACE COPIED TO WINDOWS CLIPBOARD")
    print("")
    print(">>> RETURN TO CHATGPT AND PRESS CTRL+V <<<")
    print("=" * 100)

except Exception as exc:
    print("")
    print("=" * 100)
    print("CLIPBOARD : FAIL")
    print("=" * 100)
    print(type(exc).__name__, str(exc))
    print("=" * 100)

