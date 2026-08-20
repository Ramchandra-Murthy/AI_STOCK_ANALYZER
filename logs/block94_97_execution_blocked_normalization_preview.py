from pathlib import Path
import re

ROOT = Path("services/quantitative")

print("=" * 90)
print("EROS 3.0 - BLOCK 94-97 EXECUTION_BLOCKED NORMALIZATION PREVIEW")
print("=" * 90)

for block in range(94, 98):

    files = [
        p for p in ROOT.glob(f"block{block}_*.py")
        if "test_harness" not in p.name
    ]

    print()
    print("=" * 90)
    print(f"BLOCK {block}")
    print("=" * 90)

    if not files:
        print("SOURCE NOT FOUND")
        continue

    path = files[0]
    lines = path.read_text(encoding="utf-8").splitlines()

    print("SOURCE:", path)

    # Find lines containing the existing non-mutation invariant.
    candidates = []

    for i, line in enumerate(lines, 1):
        if '"non_mutation_invariant": True' in line:
            candidates.append(i)

    print()
    print("EXISTING SAFETY DICTIONARY LOCATIONS:")

    if not candidates:
        print("NONE FOUND")
        continue

    for line_no in candidates:

        print()
        print(f"SAFETY LOCATION AROUND L{line_no}")

        start = max(1, line_no - 8)
        end = min(len(lines), line_no + 8)

        for n in range(start, end + 1):
            marker = ">>" if n == line_no else "  "
            print(f"{marker} L{n}: {lines[n-1]}")

        print()
        print("PROPOSED NORMALIZATION:")
        print('    "execution_blocked": True,')

print()
print("=" * 90)
print("NORMALIZATION PREVIEW COMPLETE")
print("=" * 90)
print()
print("IMPORTANT")
print("This preview makes NO source changes.")
print()
print("The intended change is ONLY:")
print('    "execution_blocked": True,')
print()
print("Existing safety fields remain untouched.")
print("No broker integration is introduced.")
print("No live execution is introduced.")
print("No order creation is introduced.")
print("No portfolio mutation is introduced.")
print("=" * 90)
