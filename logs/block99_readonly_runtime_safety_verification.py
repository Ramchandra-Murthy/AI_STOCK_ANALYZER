from pathlib import Path
import subprocess
import importlib.util

SOURCE = Path(
    r"services\quantitative\block99_execution_intent_authorization_gate.py"
)

output = []

def p(text=""):
    text = str(text)
    print(text)
    output.append(text)

p("=" * 100)
p("EROS 3.0 - BLOCK 99 READ-ONLY RUNTIME SAFETY VERIFICATION")
p("=" * 100)

p()
p("SOURCE:")
p(str(SOURCE))

p()
p("SOURCE CHECK")
p("-" * 60)

if not SOURCE.exists():
    p("SOURCE : NOT FOUND")
    raise SystemExit(1)

p("SOURCE : FOUND")
p(f"SIZE   : {SOURCE.stat().st_size} bytes")

source_text = SOURCE.read_text(encoding="utf-8-sig")

p("BOM-SAFE READ : PASS")

# ------------------------------------------------------------
# Import without modifying source
# ------------------------------------------------------------

p()
p("IMPORT CHECK")
p("-" * 60)

try:
    spec = importlib.util.spec_from_file_location(
        "block99_runtime_module",
        SOURCE,
    )

    module = importlib.util.module_from_spec(spec)

    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to create import specification")

    spec.loader.exec_module(module)

    p("IMPORT : PASS")

except Exception as exc:
    p("IMPORT : FAIL")
    p(f"{type(exc).__name__}: {exc}")
    raise

# ------------------------------------------------------------
# Discover classes
# ------------------------------------------------------------

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

# Prefer the main non-test class.
main_cls = None

for name, cls in classes:
    lowered = name.lower()
    if "test" not in lowered and "mock" not in lowered:
        main_cls = cls
        break

if main_cls is None:
    main_cls = classes[0][1]

p()
p(f"SELECTED CLASS : {main_cls.__name__}")

# ------------------------------------------------------------
# Instantiate safely
# ------------------------------------------------------------

p()
p("INSTANCE CHECK")
p("-" * 60)

try:
    try:
        instance = main_cls()
    except TypeError:
        # Try common engine version constructor shape.
        try:
            instance = main_cls(engine_version="99.1.0")
        except TypeError:
            instance = main_cls("99.1.0")

    p("INSTANCE : PASS")

except Exception as exc:
    p("INSTANCE : FAIL")
    p(f"{type(exc).__name__}: {exc}")
    raise

# ------------------------------------------------------------
# Locate _blocked helper
# ------------------------------------------------------------

p()
p("BLOCKED HELPER DISCOVERY")
p("-" * 60)

blocked = getattr(instance, "_blocked", None)

if blocked is None:
    p("_blocked : NOT FOUND")
else:
    p("_blocked : FOUND")

# ------------------------------------------------------------
# Runtime blocked-path test
# ------------------------------------------------------------

if blocked is not None:

    p()
    p("DIRECT _blocked() RUNTIME TEST")
    p("-" * 60)

    result = None

    test_calls = [
        ("BLOCK_99_SAFETY_TEST",),
        (),
    ]

    last_error = None

    for args in test_calls:
        try:
            result = blocked(*args)
            break
        except TypeError as exc:
            last_error = exc
            continue

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

    optional_safety = {
        "portfolio_mutation": False,
        "valuation_mutation": False,
        "performance_mutation": False,
        "risk_mutation": False,
        "optimization": False,
        "order_creation": False,
    }

    failures = []

    for key, expected in required.items():
        actual = result.get(key, "<ABSENT>")
        p(f"{key:<28}: {actual!r}")

        if actual != expected:
            failures.append(
                f"{key}: expected {expected!r}, got {actual!r}"
            )

    p()

    for key, expected in optional_safety.items():
        actual = result.get(key, "<ABSENT>")
        p(f"{key:<28}: {actual!r}")

    p()

    if failures:
        p("BLOCK 99 SAFETY CONTRACT : FAIL")

        for failure in failures:
            p(f" - {failure}")

    else:
        p("BLOCK 99 SAFETY CONTRACT : PASS")

else:
    p()
    p("DIRECT _blocked() RUNTIME TEST : SKIPPED")
    p("No _blocked helper found.")

# ------------------------------------------------------------
# Public method discovery
# ------------------------------------------------------------

p()
p("PUBLIC GOVERNANCE / AUTHORIZATION METHODS")
p("-" * 60)

candidate_methods = [
    "authorize",
    "authorize_intent",
    "validate",
    "evaluate",
    "certify",
    "govern",
    "execute",
    "check",
]

for method_name in candidate_methods:
    found = callable(getattr(instance, method_name, None))
    p(f"{method_name:<24}: {'FOUND' if found else 'ABSENT'}")

# ------------------------------------------------------------
# Final safety statement
# ------------------------------------------------------------

p()
p("=" * 100)
p("FINAL BLOCK 99 SAFETY RESULT")
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

# ------------------------------------------------------------
# Clipboard
# ------------------------------------------------------------

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
    print("COMPLETE BLOCK 99 TRACE COPIED TO WINDOWS CLIPBOARD")
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

