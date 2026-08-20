from pathlib import Path
import re

targets = {
    94: Path(r"services\quantitative\block94_portfolio_stress_scenario_engine.py"),
    95: Path(r"services\quantitative\block95_stress_evidence_gate.py"),
    96: Path(r"services\quantitative\block96_stress_decision_gate.py"),
}

print("=" * 100)
print("EROS 3.0 - BLOCK 94-96 BLOCKED PATH CONSTRUCTION TRACE")
print("=" * 100)

patterns = [
    r"STATUS_BLOCKED",
    r"status.*BLOCKED",
    r"gate_status",
    r"decision_status",
    r"reason_code",
    r"broker_submission",
    r"live_order_submission",
    r"non_mutation_invariant",
    r"execution_blocked",
    r"return",
]

for block_id, path in targets.items():

    print()
    print("=" * 100)
    print(f"BLOCK {block_id}")
    print("=" * 100)
    print("SOURCE:", path)

    if not path.exists():
        print("ERROR: FILE NOT FOUND")
        continue

    # BOM-safe read
    lines = path.read_text(encoding="utf-8-sig").splitlines()

    matches = []

    for i, line in enumerate(lines, start=1):

        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                matches.append(i)
                break

    # Remove duplicates while preserving order
    matches = list(dict.fromkeys(matches))

    print()
    print("MATCHING SOURCE LOCATIONS:", len(matches))

    seen = set()

    for line_no in matches:

        start = max(1, line_no - 8)
        end = min(len(lines), line_no + 15)

        window = (start, end)

        if window in seen:
            continue

        seen.add(window)

        print()
        print(f"--- SOURCE WINDOW L{start}-L{end} ---")

        for n in range(start, end + 1):

            marker = ">>" if n == line_no else "  "

            print(
                f"{marker} L{n}: {lines[n-1]}"
            )

print()
print("=" * 100)
print("TRACE COMPLETE")
print("=" * 100)
print()
print("READ ONLY")
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO PORTFOLIO MUTATION")
print("NO VALUATION MUTATION")
print("=" * 100)
