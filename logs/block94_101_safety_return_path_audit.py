from pathlib import Path

ROOT = Path("services/quantitative")

blocks = [94, 95, 96, 97, 98, 99, 100, 101]

safety_keys = [
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
print("EROS 3.0 - BLOCK 94-101 SAFETY RETURN-PATH AUDIT")
print("=" * 80)

for block in blocks:

    matches = list(ROOT.glob(f"block{block}_*.py"))

    source_files = [p for p in matches if "test_harness" not in p.name]

    print()
    print("=" * 80)
    print(f"BLOCK {block}")
    print("=" * 80)

    if not source_files:
        print("SOURCE : NOT FOUND")
        continue

    path = source_files[0]

    print("SOURCE :", path)
    print("SIZE   :", path.stat().st_size, "bytes")

    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        print("READ ERROR :", type(exc).__name__, str(exc))
        continue

    lines = text.splitlines()

    print()
    print("----- SAFETY KEY OCCURRENCES -----")

    found_keys = set()

    for key in safety_keys:

        occurrences = []

        for i, line in enumerate(lines, start=1):

            if key in line:
                occurrences.append((i, line.strip()))

        if occurrences:

            found_keys.add(key)

            print()
            print(f"[{key}]")

            for line_no, content in occurrences:
                print(f"  L{line_no}: {content}")

    if not found_keys:
        print("NO SAFETY KEYS FOUND")

    print()
    print("----- RETURN STATEMENTS -----")

    return_lines = []

    for i, line in enumerate(lines, start=1):

        stripped = line.strip()

        if stripped.startswith("return "):
            return_lines.append((i, stripped))

    if not return_lines:
        print("NO SIMPLE RETURN STATEMENTS FOUND")

    else:

        for line_no, content in return_lines:
            print(f"  L{line_no}: {content}")

    print()
    print("----- STATUS / BLOCKING LITERALS -----")

    patterns = [
        "BLOCKED",
        "CERTIFIED",
        "BLOCK",
        "SOURCE_STATUS_NOT_CERTIFIED",
        "VALUATION_NOT_CERTIFIED",
        "STRESS_CERTIFICATE_NOT_CERTIFIED",
        "SOURCE_GATE_NOT_CERTIFIED",
        "SOURCE_DECISION_NOT_CERTIFIED",
    ]

    found_literals = False

    for pattern in patterns:

        occurrences = []

        for i, line in enumerate(lines, start=1):

            if pattern in line:
                occurrences.append((i, line.strip()))

        if occurrences:

            found_literals = True

            print()
            print(f"[{pattern}]")

            for line_no, content in occurrences:
                print(f"  L{line_no}: {content}")

    if not found_literals:
        print("NO BLOCKING STATUS LITERALS FOUND")

print()
print("=" * 80)
print("AUDIT INTERPRETATION")
print("=" * 80)
print("This audit is READ ONLY.")
print()
print("Purpose:")
print("1. Locate the actual safety fields in source.")
print("2. Locate the actual return paths.")
print("3. Determine whether Blocks 94-97 intentionally use")
print("   a different safety schema from Blocks 98-101.")
print("4. Do NOT modify source until the contract difference")
print("   has been identified.")
print()
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print("=" * 80)
