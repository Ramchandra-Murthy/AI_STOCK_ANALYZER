import ast
from pathlib import Path

ROOT = Path(".")
QUANT = ROOT / "services" / "quantitative"

blocks = list(range(94, 102))

safety_terms = [
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

output = []

def emit(text=""):
    print(text)
    output.append(str(text))

emit("=" * 80)
emit("EROS 3.0 - BLOCK 94-101 SAFETY CONTRACT REPAIR AUDIT")
emit("=" * 80)

for block in blocks:

    matches = list(
        QUANT.glob(f"block{block}_*.py")
    )

    source_files = [
        p for p in matches
        if "test_harness" not in p.name
    ]

    if not source_files:
        emit()
        emit(f"BLOCK {block}")
        emit("-" * 80)
        emit("SOURCE : NOT FOUND")
        continue

    path = source_files[0]

    emit()
    emit("=" * 80)
    emit(f"BLOCK {block}")
    emit("=" * 80)
    emit(f"SOURCE : {path}")
    emit(f"SIZE   : {path.stat().st_size} bytes")

    try:
        text = path.read_text(
            encoding="utf-8",
            errors="replace"
        )
    except Exception as exc:
        emit(f"READ ERROR : {type(exc).__name__}: {exc}")
        continue

    lines = text.splitlines()

    emit()
    emit("SAFETY TERM LOCATIONS")
    emit("-" * 80)

    found_any = False

    for index, line in enumerate(lines, start=1):
        lower = line.lower()

        found = [
            term
            for term in safety_terms
            if term.lower() in lower
        ]

        if found:
            found_any = True
            emit(
                f"L{index:04d} "
                f"[{', '.join(found)}] "
                f"{line.strip()}"
            )

    if not found_any:
        emit("NO SAFETY TERMS FOUND")

    emit()
    emit("RETURN DICT ANALYSIS")
    emit("-" * 80)

    try:
        tree = ast.parse(text)

        return_nodes = list(
            ast.walk(tree)
        )

        returns = [
            node
            for node in return_nodes
            if isinstance(node, ast.Return)
        ]

        emit(f"RETURN STATEMENTS : {len(returns)}")

        for idx, node in enumerate(returns, start=1):

            if node.value is None:
                emit(
                    f"RETURN {idx}: "
                    f"L{node.lineno} -> None"
                )
                continue

            if isinstance(node.value, ast.Dict):

                keys = []

                for key in node.value.keys:

                    if isinstance(key, ast.Constant):
                        keys.append(repr(key.value))
                    else:
                        keys.append(
                            ast.dump(key)
                        )

                emit(
                    f"RETURN {idx}: "
                    f"L{node.lineno} -> "
                    f"DICT KEYS = {keys}"
                )

            else:
                emit(
                    f"RETURN {idx}: "
                    f"L{node.lineno} -> "
                    f"{type(node.value).__name__}"
                )

    except Exception as exc:
        emit(
            f"AST ERROR : "
            f"{type(exc).__name__}: {exc}"
        )

emit()
emit("=" * 80)
emit("REQUIRED SAFETY CONTRACT")
emit("=" * 80)

required = {
    "execution_blocked": True,
    "non_mutation_invariant": True,
    "broker_submission": False,
    "live_order_submission": False,
    "order_creation": False,
    "portfolio_mutation": False,
    "valuation_mutation": False,
    "performance_mutation": False,
    "risk_mutation": False,
    "optimization": False,
}

for key, value in required.items():
    emit(f"{key:28} = {value!r}")

emit()
emit("=" * 80)
emit("AUDIT INTERPRETATION")
emit("=" * 80)
emit(
    "This audit does NOT modify source code."
)
emit(
    "It identifies the exact implementation locations "
    "that must be repaired before certification."
)
emit(
    "No broker."
)
emit(
    "No live execution."
)
emit(
    "No order creation."
)
emit(
    "No portfolio mutation."
)
emit(
    "No valuation mutation."
)
emit(
    "No risk mutation."
)

emit()
emit("=" * 80)
emit("SAFETY CONTRACT REPAIR AUDIT COMPLETE")
emit("=" * 80)

# Copy complete output to Windows clipboard.
try:
    import subprocess

    clipboard_text = "\r\n".join(output)

    subprocess.run(
        ["clip.exe"],
        input=clipboard_text,
        text=True,
        check=True
    )

    print()
    print("=" * 80)
    print("COMPLETE OUTPUT COPIED TO WINDOWS CLIPBOARD")
    print("=" * 80)
    print("You can now paste directly into ChatGPT with CTRL+V.")

except Exception as exc:
    print()
    print("CLIPBOARD COPY FAILED")
    print(type(exc).__name__, str(exc))

