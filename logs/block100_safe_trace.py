from pathlib import Path
import subprocess
import importlib.util
import inspect

SOURCE = Path(
    r"services\quantitative\block100_paper_execution_fill_gate.py"
)

OUTPUT = []

def p(text=""):
    text = str(text)
    print(text)
    OUTPUT.append(text)

p("=" * 100)
p("EROS 3.0 - BLOCK 100 READ-ONLY RETURN / SAFETY PATH INSPECTION")
p("=" * 100)

p()
p("SOURCE:")
p(str(SOURCE))

# ------------------------------------------------------------
# SOURCE CHECK
# ------------------------------------------------------------

p()
p("SOURCE CHECK")
p("-" * 60)

if not SOURCE.exists():
    p("SOURCE : NOT FOUND")
    raise SystemExit(1)

p("SOURCE : FOUND")
p(f"SIZE   : {SOURCE.stat().st_size} bytes")

# BOM-safe source reading
source_text = SOURCE.read_text(encoding="utf-8-sig")
lines = source_text.splitlines()

p("BOM-SAFE READ : PASS")
p(f"SOURCE LINES  : {len(lines)}")

# ------------------------------------------------------------
# IMPORT CHECK
# ------------------------------------------------------------

p()
p("IMPORT CHECK")
p("-" * 60)

try:
    spec = importlib.util.spec_from_file_location(
        "block100_module",
        SOURCE
    )

    module = importlib.util.module_from_spec(spec)

    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to create import specification")

    spec.loader.exec_module(module)

    p("IMPORT : PASS")

except Exception as exc:
    p("IMPORT : FAIL")
    p(f"{type(exc).__name__}: {exc}")
    raise SystemExit(1)

# ------------------------------------------------------------
# CLASS DISCOVERY
# ------------------------------------------------------------

p()
p("CLASS DISCOVERY")
p("-" * 60)

classes = []

for name, obj in vars(module).items():
    if inspect.isclass(obj):
        if obj.__module__ == module.__name__:
            classes.append((name, obj))

if not classes:
    p("CLASS : NOT FOUND")
    raise SystemExit(1)

for name, obj in classes:
    p(f"CLASS : FOUND -> {name}")

class_name, cls = classes[0]

p()
p(f"SELECTED CLASS : {class_name}")

# ------------------------------------------------------------
# INSTANCE
# ------------------------------------------------------------

p()
p("INSTANCE CHECK")
p("-" * 60)

try:
    instance = cls()
    p("INSTANCE : PASS")
except Exception as exc:
    p("INSTANCE : FAIL")
    p(f"{type(exc).__name__}: {exc}")
    raise SystemExit(1)

# ------------------------------------------------------------
# METHOD DISCOVERY
# ------------------------------------------------------------

p()
p("METHOD DISCOVERY")
p("-" * 60)

method_names = [
    "_blocked",
    "certify",
    "authorize",
    "authorize_execution",
    "validate",
    "evaluate",
    "govern",
    "execute",
    "fill",
    "paper_execute",
    "check",
]

for name in method_names:
    value = getattr(instance, name, None)

    if callable(value):
        p(f"{name:24} : FOUND")
    else:
        p(f"{name:24} : ABSENT")

# ------------------------------------------------------------
# SOURCE RETURN STATEMENT INSPECTION
# ------------------------------------------------------------

p()
p("RETURN STATEMENT INSPECTION")
p("-" * 60)

return_locations = []

for number, line in enumerate(lines, start=1):
    stripped = line.strip()

    if stripped.startswith("return"):
        return_locations.append(number)

if return_locations:
    p(f"RETURN STATEMENTS FOUND : {len(return_locations)}")

    for number in return_locations:
        start = max(1, number - 4)
        end = min(len(lines), number + 12)

        p()
        p(f"--- RETURN WINDOW L{start}-L{end} ---")

        for n in range(start, end + 1):
            marker = ">>" if n == number else "  "
            p(f"{marker} L{n}: {lines[n - 1]}")
else:
    p("RETURN STATEMENTS FOUND : 0")

# ------------------------------------------------------------
# BLOCKED HELPER RUNTIME TEST
# ------------------------------------------------------------

p()
p("=" * 100)
p("BLOCKED HELPER RUNTIME TEST")
p("=" * 100)

blocked = getattr(instance, "_blocked", None)

if not callable(blocked):

    p()
    p("_blocked : NOT FOUND")
    p()
    p("RESULT : REQUIRES INSPECTION")
    p("Block 100 does not expose a direct _blocked() helper.")

else:

    p()
    p("_blocked : FOUND")

    try:
        signature = inspect.signature(blocked)
        p(f"SIGNATURE : {signature}")

        # Try the common reason argument used by the EROS blocks.
        try:
            result = blocked("BLOCK_100_SAFETY_TEST")
        except TypeError:
            result = blocked()

        p()
        p("CALL : PASS")

        p()
        p("BLOCKED RESULT:")
        p(repr(result))

        if isinstance(result, dict):

            p()
            p("SAFETY CONTRACT MATRIX")
            p("-" * 60)

            fields = [
                "status",
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

            safety_pass = True

            for field in fields:

                if field not in result:
                    value = "<ABSENT>"
                else:
                    value = repr(result[field])

                p(f"{field:28} : {value}")

                if field == "execution_blocked":
                    if result.get(field) is not True:
                        safety_pass = False

                elif field == "non_mutation_invariant":
                    if result.get(field) is not True:
                        safety_pass = False

                elif field in (
                    "broker_submission",
                    "live_order_submission",
                ):
                    if result.get(field) is not False:
                        safety_pass = False

            p()
            if safety_pass:
                p("BLOCK 100 SAFETY CONTRACT : PASS")
            else:
                p("BLOCK 100 SAFETY CONTRACT : FAIL")

    except Exception as exc:
        p()
        p("CALL : FAIL")
        p(f"{type(exc).__name__}: {exc}")

# ------------------------------------------------------------
# FINAL
# ------------------------------------------------------------

p()
p("=" * 100)
p("FINAL BLOCK 100 READ-ONLY RESULT")
p("=" * 100)

p()
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
# WINDOWS CLIPBOARD
# ------------------------------------------------------------

clipboard_text = "\n".join(OUTPUT)

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

