from pathlib import Path
import ast
import subprocess

SOURCE = Path(
    r"services\quantitative\block100_paper_execution_fill_gate.py"
)

OUTPUT = []

def p(text=""):
    text = str(text)
    print(text)
    OUTPUT.append(text)


def print_window(lines, start, end, title):
    p()
    p("=" * 100)
    p(title)
    p("=" * 100)

    for n in range(start, end + 1):
        p(f"L{n}: {lines[n - 1]}")


p("=" * 100)
p("EROS 3.0 - BLOCK 100 READ-ONLY RETURN / SAFETY PATH INSPECTION")
p("=" * 100)

p()
p("SOURCE:")
p(str(SOURCE))

if not SOURCE.exists():
    p()
    p("SOURCE : NOT FOUND")
else:
    p()
    p("SOURCE : FOUND")
    p(f"SIZE   : {SOURCE.stat().st_size} bytes")

    # ------------------------------------------------------------
    # BOM-SAFE READ
    # ------------------------------------------------------------
    try:
        source = SOURCE.read_text(
            encoding="utf-8-sig"
        )
        lines = source.splitlines()

        p("BOM-SAFE READ : PASS")
        p(f"SOURCE LINES  : {len(lines)}")
    except Exception as exc:
        p("BOM-SAFE READ : FAIL")
        p(f"{type(exc).__name__}: {exc}")
        lines = []
        source = ""

    # ------------------------------------------------------------
    # AST CHECK
    # ------------------------------------------------------------
    if source:
        p()
        p("-" * 100)
        p("AST / SYNTAX CHECK")
        p("-" * 100)

        try:
            tree = ast.parse(
                source,
                filename=str(SOURCE)
            )
            p("AST PARSE : PASS")
        except Exception as exc:
            p("AST PARSE : FAIL")
            p(f"{type(exc).__name__}: {exc}")
            tree = None

        # --------------------------------------------------------
        # RETURN STATEMENT DISCOVERY
        # --------------------------------------------------------
        p()
        p("-" * 100)
        p("RETURN STATEMENT DISCOVERY")
        p("-" * 100)

        return_nodes = []

        if tree is not None:
            for node in ast.walk(tree):
                if isinstance(node, ast.Return):
                    return_nodes.append(node)

        p(f"RETURN COUNT : {len(return_nodes)}")

        for index, node in enumerate(return_nodes, start=1):
            line_no = getattr(node, "lineno", None)

            p()
            p(f"RETURN #{index}")
            p(f"LOCATION : L{line_no}")

            if line_no is not None:
                start = max(1, line_no - 8)
                end = min(len(lines), line_no + 25)

                for n in range(start, end + 1):
                    marker = ">>" if n == line_no else "  "
                    p(f"{marker} L{n}: {lines[n - 1]}")

        # --------------------------------------------------------
        # BLOCKED / SAFETY KEYWORD SEARCH
        # --------------------------------------------------------
        p()
        p("-" * 100)
        p("SAFETY / BLOCKED KEYWORD SEARCH")
        p("-" * 100)

        keywords = [
            "BLOCKED",
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
            "execution_action",
            "paper_execution",
            "fill",
        ]

        matches = []

        for i, line in enumerate(lines, start=1):
            for keyword in keywords:
                if keyword in line:
                    matches.append(
                        (i, keyword, line)
                    )

        if not matches:
            p("NO SAFETY KEYWORD MATCHES FOUND")
        else:
            p(f"MATCH COUNT : {len(matches)}")

            seen = set()

            for line_no, keyword, line in matches:
                start = max(1, line_no - 5)
                end = min(len(lines), line_no + 8)

                window = (start, end)

                if window in seen:
                    continue

                seen.add(window)

                p()
                p(
                    f"--- SAFETY WINDOW "
                    f"L{start}-L{end} "
                    f"(MATCH: {keyword}) ---"
                )

                for n in range(start, end + 1):
                    marker = ">>" if n == line_no else "  "
                    p(
                        f"{marker} "
                        f"L{n}: {lines[n - 1]}"
                    )

    # ------------------------------------------------------------
    # IMPORT / CLASS RUNTIME CHECK
    # ------------------------------------------------------------
    p()
    p("-" * 100)
    p("RUNTIME IMPORT CHECK")
    p("-" * 100)

    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "block100_runtime_audit",
            SOURCE
        )

        module = importlib.util.module_from_spec(spec)

        if spec.loader is None:
            raise RuntimeError(
                "Unable to obtain module loader"
            )

        spec.loader.exec_module(module)

        p("IMPORT : PASS")

        classes = [
            name
            for name, value in vars(module).items()
            if isinstance(value, type)
            and name.startswith("EROSBlock100")
        ]

        if classes:
            p("CLASSES FOUND:")
            for name in classes:
                p(f"  {name}")
        else:
            p("NO EROSBlock100* CLASS FOUND")

    except Exception as exc:
        p("IMPORT : FAIL")
        p(f"{type(exc).__name__}: {exc}")

# ------------------------------------------------------------
# FINAL
# ------------------------------------------------------------

p()
p("=" * 100)
p("FINAL BLOCK 100 INSPECTION RESULT")
p("=" * 100)

p()
p("READ ONLY")
p("NO SOURCE CHANGES")
p("NO BROKER")
p("NO LIVE EXECUTION")
p("NO ORDER CREATION")
p("NO PORTFOLIO MUTATION")
p("NO VALUATION MUTATION")
p("NO PERFORMANCE MUTATION")
p("NO RISK MUTATION")
p("NO OPTIMIZATION")

p()
p("=" * 100)
p("TRACE COMPLETE")
p("=" * 100)

# ------------------------------------------------------------
# COPY COMPLETE OUTPUT TO WINDOWS CLIPBOARD
# ------------------------------------------------------------

clipboard_text = "\r\n".join(OUTPUT)

try:
    subprocess.run(
        ["clip.exe"],
        input=clipboard_text,
        text=True,
        check=True,
    )

    print()
    print("=" * 100)
    print("CLIPBOARD : PASS")
    print("=" * 100)
    print("COMPLETE BLOCK 100 TRACE COPIED TO WINDOWS CLIPBOARD")
    print()
    print(">>> RETURN TO CHATGPT AND PRESS CTRL+V <<<")
    print("=" * 100)

except Exception as exc:
    print()
    print("=" * 100)
    print("CLIPBOARD : FAIL")
    print("=" * 100)
    print(type(exc).__name__, str(exc))
    print("=" * 100)

