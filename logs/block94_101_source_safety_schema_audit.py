from pathlib import Path

ROOT = Path("services/quantitative")

blocks = range(94, 102)

keys = [
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

print("=" * 80)
print("EROS 3.0 - BLOCK 94-101 SOURCE SAFETY SCHEMA AUDIT")
print("=" * 80)

for block in blocks:

    files = [p for p in ROOT.glob(f"block{block}_*.py") if "test_harness" not in p.name]

    print()
    print("=" * 80)
    print(f"BLOCK {block}")
    print("=" * 80)

    if not files:
        print("SOURCE NOT FOUND")
        continue

    path = files[0]
    print("SOURCE:", path)

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    for key in keys:

        hits = [(i, line.strip()) for i, line in enumerate(lines, 1) if key in line]

        if hits:
            print()
            print(f"--- {key} ---")
            for line_no, line in hits:
                print(f"L{line_no}: {line}")

print()
print("=" * 80)
print("SOURCE SAFETY SCHEMA AUDIT COMPLETE")
print("=" * 80)
print("READ ONLY")
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print("=" * 80)
