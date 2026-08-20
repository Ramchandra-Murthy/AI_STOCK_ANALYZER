from pathlib import Path

targets = {
    94: Path(r"services\quantitative\block94_portfolio_stress_scenario_engine.py"),
    95: Path(r"services\quantitative\block95_stress_evidence_gate.py"),
    96: Path(r"services\quantitative\block96_stress_decision_gate.py"),
}

print("=" * 100)
print("EROS 3.0 - BLOCK 94-96 ACTUAL EARLY BLOCKED RETURN DICTIONARY TRACE")
print("=" * 100)

for block_id, path in targets.items():

    print()
    print("=" * 100)
    print(f"BLOCK {block_id}")
    print("=" * 100)
    print("SOURCE:", path)

    if not path.exists():
        print("SOURCE ERROR: FILE NOT FOUND")
        continue

    lines = path.read_text(encoding="utf-8").splitlines()

    printed_windows = set()

    for i, line in enumerate(lines, start=1):

        stripped = line.strip()

        if (
            stripped.startswith("return {")
            or '"status": "BLOCKED"' in line
            or '"status": STATUS_BLOCKED' in line
            or '"broker_submission": False' in line
            or '"live_order_submission": False' in line
        ):

            start = max(1, i - 12)
            end = min(len(lines), i + 25)

            window = (start, end)

            if window in printed_windows:
                continue

            printed_windows.add(window)

            print()
            print(f"--- SOURCE WINDOW L{start}-L{end} ---")

            for n in range(start, end + 1):
                marker = ">>" if n == i else "  "
                print(f"{marker} L{n}: {lines[n-1]}")

print()
print("=" * 100)
print("TRACE COMPLETE")
print("=" * 100)
print("READ ONLY")
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print("=" * 100)
