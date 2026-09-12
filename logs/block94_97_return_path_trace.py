from pathlib import Path

targets = {
    94: Path(r"services\quantitative\block94_portfolio_stress_scenario_engine.py"),
    95: Path(r"services\quantitative\block95_stress_evidence_gate.py"),
    96: Path(r"services\quantitative\block96_stress_decision_gate.py"),
    97: Path(r"services\quantitative\block97_stress_readiness_gate.py"),
}

print("=" * 90)
print("EROS 3.0 - BLOCK 94-97 RETURN PATH / SAFETY CONTRACT TRACE")
print("=" * 90)

for block_id, path in targets.items():

    print()
    print("=" * 90)
    print(f"BLOCK {block_id}")
    print("=" * 90)
    print("SOURCE:", path)

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    matches = []

    for i, line in enumerate(lines, start=1):
        if (
            '"execution_blocked"' in line
            or '"non_mutation_invariant"' in line
            or '"broker_submission"' in line
            or '"live_order_submission"' in line
            or "return " in line
        ):
            matches.append(i)

    print()
    print("RELEVANT SOURCE LOCATIONS:")

    for line_no in matches:
        start = max(1, line_no - 5)
        end = min(len(lines), line_no + 5)

        print()
        print(f"--- SOURCE WINDOW {start}-{end} ---")

        for n in range(start, end + 1):
            marker = ">>" if n == line_no else "  "
            print(f"{marker} L{n}: {lines[n-1]}")

print()
print("=" * 90)
print("RETURN PATH / SAFETY CONTRACT TRACE COMPLETE")
print("=" * 90)
print("READ ONLY")
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print("=" * 90)
