from pathlib import Path
import subprocess

path = Path(r"services\quantitative\block100_paper_execution_fill_gate.py")

output = []

def p(text=""):
    text = str(text)
    print(text)
    output.append(text)

p("=" * 100)
p("EROS 3.0 - BLOCK 100 COMPLETE READ-ONLY RETURN / SAFETY INSPECTION")
p("=" * 100)

p()
p(f"SOURCE: {path}")

if not path.exists():
    p("SOURCE : NOT FOUND")
else:
    p("SOURCE : FOUND")
    p(f"SIZE   : {path.stat().st_size} bytes")

    source = path.read_text(encoding="utf-8-sig")
    lines = source.splitlines()

    p()
    p("BOM-SAFE READ : PASS")
    p(f"SOURCE LINES  : {len(lines)}")

    p()
    p("=" * 100)
    p("ALL RETURN STATEMENTS")
    p("=" * 100)

    return_locations = []

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        if stripped.startswith("return "):
            return_locations.append(i)

    p(f"RETURN COUNT : {len(return_locations)}")

    for i in return_locations:
        start = max(1, i - 8)
        end = min(len(lines), i + 20)

        p()
        p(f"--- RETURN WINDOW L{start}-L{end} ---")

        for n in range(start, end + 1):
            marker = ">>" if n == i else "  "
            p(f"{marker} L{n}: {lines[n-1]}")

    p()
    p("=" * 100)
    p("SAFETY-RELATED SOURCE REFERENCES")
    p("=" * 100)

    keywords = [
        "BLOCKED",
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
        "paper",
        "fill",
        "execution",
        "authorize",
        "certify",
        "gate",
    ]

    found = set()

    for i, line in enumerate(lines, start=1):
        if any(keyword in line for keyword in keywords):
            start = max(1, i - 5)
            end = min(len(lines), i + 10)

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
p("INSPECTION COMPLETE")
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
    print("COMPLETE BLOCK 100 INSPECTION COPIED TO WINDOWS CLIPBOARD")
    print()
    print("NOW PRESS CTRL+V IN CHATGPT")
    print("=" * 100)

except Exception as exc:
    print()
    print("CLIPBOARD : FAIL")
    print(type(exc).__name__, str(exc))

