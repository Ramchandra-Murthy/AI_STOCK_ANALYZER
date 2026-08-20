from pathlib import Path
from datetime import datetime

targets = {
    94: Path(r"services\quantitative\block94_portfolio_stress_scenario_engine.py"),
    95: Path(r"services\quantitative\block95_stress_evidence_gate.py"),
    96: Path(r"services\quantitative\block96_stress_decision_gate.py"),
    97: Path(r"services\quantitative\block97_stress_readiness_gate.py"),
}

print("=" * 80)
print("EROS 3.0 - BLOCK 94-97 SAFETY CONTRACT NORMALIZATION")
print("=" * 80)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

for block_id, path in targets.items():

    print()
    print("=" * 80)
    print(f"BLOCK {block_id}")
    print("=" * 80)
    print("SOURCE:", path)

    if not path.exists():
        raise FileNotFoundError(f"Missing source file: {path}")

    source = path.read_text(encoding="utf-8")

    backup = path.with_suffix(
        path.suffix + f".backup_{timestamp}"
    )

    backup.write_text(source, encoding="utf-8")

    print("BACKUP :", backup)

    original_count = source.count('"execution_blocked": True')

    if original_count:
        print(
            f"EXISTING execution_blocked=True COUNT : "
            f"{original_count}"
        )

    lines = source.splitlines()

    output = []
    inserted = 0

    for line in lines:
        output.append(line)

        stripped = line.strip()

        # Insert only immediately after the standardized
        # non-mutation safety invariant.
        if stripped == '"non_mutation_invariant": True,':
            # Avoid duplicate insertion.
            next_line = None

            if len(lines) > len(output):
                next_line = lines[len(output)]

            if next_line is None or next_line.strip() != '"execution_blocked": True,':
                indent = line[:len(line) - len(line.lstrip())]

                output.append(
                    f'{indent}"execution_blocked": True,'
                )

                inserted += 1

    new_source = "\n".join(output) + (
        "\n" if source.endswith("\n") else ""
    )

    new_count = new_source.count('"execution_blocked": True')

    print("INSERTED:", inserted)
    print("FINAL execution_blocked=True COUNT:", new_count)

    if block_id in (94, 95, 96):
        if inserted != 1:
            raise RuntimeError(
                f"BLOCK {block_id}: expected exactly 1 insertion, "
                f"got {inserted}"
            )

    if block_id == 97:
        if inserted != 2:
            raise RuntimeError(
                f"BLOCK 97: expected exactly 2 insertions, "
                f"got {inserted}"
            )

    path.write_text(new_source, encoding="utf-8")

    print("SOURCE UPDATE : PASS")

print()
print("=" * 80)
print("NORMALIZATION COMPLETE")
print("=" * 80)
print("Blocks changed : 94, 95, 96, 97")
print("Blocks untouched: 98, 99, 100, 101")
print()
print("ONLY FIELD ADDED:")
print('    "execution_blocked": True,')
print()
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO PORTFOLIO MUTATION")
print("NO VALUATION MUTATION")
print("=" * 80)
