from pathlib import Path

files = [
    Path("services/quantitative/block94_test_harness.py"),
    Path("services/quantitative/block95_test_harness.py"),
    Path("services/quantitative/block96_test_harness.py"),
    Path("services/quantitative/block97_test_harness.py"),
    Path("services/quantitative/block98_test_harness.py"),
    Path("services/quantitative/block99_test_harness.py"),
    Path("services/quantitative/block100_test_harness.py"),
    Path("services/quantitative/block101_test_harness.py"),
]

print("=" * 70)
print("EROS 3.0 - EXISTING TEST DATA CONTRACTS")
print("=" * 70)

for path in files:
    print()
    print("=" * 70)
    print(path)
    print("=" * 70)

    if not path.exists():
        print("FILE : NOT FOUND")
        continue

    print("FILE : FOUND")
    print()

    text = path.read_text(encoding="utf-8")

    lines = text.splitlines()

    for number, line in enumerate(lines, start=1):
        lower = line.lower()

        interesting = any(
            token in lower
            for token in [
                "valuation",
                "performance",
                "risk",
                "positions",
                "scenarios",
                "stress_certificate",
                "stress_gate",
                "decision",
                "governance",
                "intent",
                "execution",
                "fill_ratio",
                "reconciliation",
            ]
        )

        if interesting:
            print(f"{number:04d}: {line}")

print()
print("=" * 70)
print("TEST DATA CONTRACT INSPECTION COMPLETE")
print("=" * 70)
print("READ ONLY")
print("NO SOURCE CHANGES")
print("NO COMMIT")
print("NO PUSH")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print("=" * 70)
