from pathlib import Path
import subprocess
import importlib.util

SOURCE = Path(
    r"services\quantitative\block100_paper_execution_fill_gate.py"
)

output = []

def p(text=""):
    text = str(text)
    print(text)
    output.append(text)

p("=" * 100)
p("EROS 3.0 - BLOCK 100 READ-ONLY RUNTIME SAFETY VERIFICATION")
p("=" * 100)

p()
p("SOURCE:")
p(str(SOURCE))

if not SOURCE.exists():
    p("SOURCE : NOT FOUND")
    raise SystemExit(1)

p()
p("SOURCE CHECK")
p("-" * 60)
p("SOURCE : FOUND")
p(f"SIZE   : {SOURCE.stat().st_size} bytes")

source_text = SOURCE.read_text(encoding="utf-8-sig")
p("BOM-SAFE READ : PASS")

p()
p("IMPORT CHECK")
p("-" * 60)

spec = importlib.util.spec_from_file_location(
    "block100_runtime_module",
    SOURCE,
)

if spec is None or spec.loader is None:
    p("IMPORT : FAIL")
    raise SystemExit(1)

module = importlib.util.module_from_spec(spec)

try:
    spec.loader.exec_module(module)
    p("IMPORT : PASS")
except Exception as exc:
    p("IMPORT : FAIL")
    p(f"{type(exc).__name__}: {exc}")
    raise

p()
p("CLASS DISCOVERY")
p("-" * 60)

classes = []

for name, obj in vars(module).items():
    if isinstance(obj, type) and obj.__module__ == module.__name__:
        classes.append((name, obj))

if not classes:
    p("CLASS : NOT FOUND")
    raise SystemExit(1)

for name, cls in classes:
    p(f"CLASS : FOUND -> {name}")

main_cls = None

for name, cls in classes:
    if "test" not in name.lower() and "mock" not in name.lower():
        main_cls = cls
        break

if main_cls is None:
    main_cls = classes[0][1]

p()
p(f"SELECTED CLASS : {main_cls.__name__}")

p()
p("INSTANCE CHECK")
p("-" * 60)

try:
    try:
        instance = main_cls()
    except TypeError:
        try:
            instance = main_cls(engine_version="100.1.0")
        except TypeError:
            instance = main_cls("100.1.0")

    p("INSTANCE : PASS")

except Exception as exc:
    p("INSTANCE : FAIL")
    p(f"{type(exc).__name__}: {exc}")
    raise

p()
p("BLOCKED HELPER DISCOVERY")
p("-" * 60)

blocked = getattr(instance, "_blocked", None)

if blocked is None:
    p("_blocked : NOT FOUND")
else:
    p("_blocked : FOUND")

failures = []

if blocked is not None:

    p()
    p("DIRECT _blocked() RUNTIME TEST")
    p("-" * 60)

    result = None
    last_error = None

    for args in [
        ("BLOCK_100_SAFETY_TEST",),
        (),
    ]:
        try:
            result = blocked(*args)
            break
        except TypeError as exc:
            last_error = exc

    if result is None:
        p("CALL : FAIL")
        p(f"{type(last_error).__name__}: {last_error}")
        raise SystemExit(1)

    p("CALL : PASS")

    p()
    p("BLOCKED RESULT:")
    p(repr(result))

    p()
    p("SAFETY CONTRACT MATRIX")
    p("-" * 60)

    required = {
        "status": "BLOCKED",
        "execution_blocked": True,
        "non_mutation_invariant": True,
        "broker_submission": False,
        "live_order_submission": False,
    }

    optional = {
        "portfolio_mutation": False,
        "valuation_mutation": False,
        "performance_mutation": False,
        "risk_mutation": False,
        "optimization": False,
        "order_creation": False,
    }

    for key, expected in required.items():
        actual = result.get(key, "<ABSENT>")
        p(f"{key:<28}: {actual!r}")

        if actual != expected:
            failures.append(
                f"{key}: expected {expected!r}, got {actual!r}"
            )

    p()

    for key, expected in optional.items():
        actual = result.get(key, "<ABSENT>")
        p(f"{key:<28}: {actual!r}")

    p()

    if failures:
        p("BLOCK 100 SAFETY CONTRACT : FAIL")
        for failure in failures:
            p(f" - {failure}")
    else:
        p("BLOCK 100 SAFETY CONTRACT : PASS")

p()
p("PUBLIC EXECUTION METHODS")
p("-" * 60)

candidate_methods = [
    "authorize",
    "authorize_execution",
    "validate",
    "evaluate",
    "certify",
    "govern",
    "execute",
    "fill",
    "paper_execute",
    "check",
]

for method_name in candidate_methods:
    found = callable(getattr(instance, method_name, None))
    p(f"{method_name:<24}: {'FOUND' if found else 'ABSENT'}")

p()
p("=" * 100)
p("FINAL BLOCK 100 SAFETY RESULT")
p("=" * 100)

if blocked is not None and not failures:
    p("SAFETY : PASS")
else:
    p("SAFETY : REQUIRES INSPECTION")

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

clipboard_text = "\n".join(output)

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

