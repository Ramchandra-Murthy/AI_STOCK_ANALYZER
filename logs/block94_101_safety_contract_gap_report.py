from pathlib import Path
import re

ROOT = Path("services/quantitative")

required = [
    "execution_blocked",
    "non_mutation_invariant",
    "broker_submission",
    "live_order_submission",
]

print("=" * 90)
print("EROS 3.0 - BLOCK 94-101 SAFETY CONTRACT GAP REPORT")
print("=" * 90)

print()
print("PURPOSE")
print("-------")
print("Determine whether Blocks 94-97 expose the same safety contract")
print("as Blocks 98-101.")
print()
print("This is an inspection-only report.")
print("No source modifications are performed.")

report = {}

for block in range(94, 102):

    files = [
        p for p in ROOT.glob(f"block{block}_*.py")
        if "test_harness" not in p.name
    ]

    if not files:
        continue

    path = files[0]
    text = path.read_text(encoding="utf-8")

    present = {}
    missing = {}

    for key in required:

        if key in text:
            present[key] = True
        else:
            missing[key] = True

    report[block] = {
        "file": str(path),
        "present": list(present),
        "missing": list(missing),
    }

    print()
    print("=" * 90)
    print(f"BLOCK {block}")
    print("=" * 90)
    print("SOURCE:", path)

    print()
    print("PRESENT:")
    for key in present:
        print("  [PASS]", key)

    print()
    print("MISSING:")
    for key in missing:
        print("  [GAP ]", key)

print()
print("=" * 90)
print("ARCHITECTURE SUMMARY")
print("=" * 90)

early = report.get(94, {})
late = report.get(98, {})

print()
print("BLOCKS 94-97")
print("These are the stress/risk/readiness stages.")
print("Their safety contract must be examined before normalization.")

print()
print("BLOCKS 98-101")
print("These are the execution-governance stages.")
print("They establish the stronger standardized execution safety contract.")

print()
print("IMPORTANT:")
print("A missing safety field does NOT automatically mean unsafe execution.")
print("It may indicate only that the safety invariant is represented")
print("differently at that stage.")

print()
print("NEXT DECISION:")
print("1. If 94-97 already enforce blocking through other fields,")
print("   normalize the outward schema without changing behavior.")
print()
print("2. If a real invariant is absent, repair the specific block.")
print()
print("3. Do NOT add generic fields blindly.")
print("   Preserve each block's existing semantics.")

print()
print("=" * 90)
print("SAFETY CONTRACT GAP REPORT COMPLETE")
print("=" * 90)
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print("=" * 90)
