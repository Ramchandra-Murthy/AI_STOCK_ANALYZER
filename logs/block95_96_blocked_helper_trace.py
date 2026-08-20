from pathlib import Path

targets = {
    95: Path(r"services\quantitative\block95_stress_evidence_gate.py"),
    96: Path(r"services\quantitative\block96_stress_decision_gate.py"),
}

print("=" * 100)
print("EROS 3.0 - BLOCK 95-96 BLOCKED HELPER SAFETY CONTRACT TRACE")
print("=" * 100)

for block_id, path in targets.items():

    print()
    print("=" * 100)
    print(f"BLOCK {block_id}")
    print("=" * 100)
    print("SOURCE:", path)

    if not path.exists():
        print("ERROR: SOURCE FILE NOT FOUND")
        continue

    lines = path.read_text(encoding="utf-8-sig").splitlines()

    found = False

    for i, line in enumerate(lines, start=1):

        if "def _blocked" in line:

            found = True

            start = max(1, i - 5)
            end = min(len(lines), i + 30)

            print()
            print(f"--- _blocked HELPER WINDOW L{start}-L{end} ---")

            for n in range(start, end + 1):
                marker = ">>" if n == i else "  "
                print(f"{marker} L{n}: {lines[n-1]}")

    if not found:
        print()
        print("NO _blocked HELPER FOUND")

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
