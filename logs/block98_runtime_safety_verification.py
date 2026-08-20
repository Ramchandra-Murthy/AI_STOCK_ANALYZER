from pathlib import Path
import subprocess
import importlib

SOURCE = Path(
    r"services\quantitative\block98_execution_governance_bridge.py"
)

output = []

def p(text=""):
    text = str(text)
    print(text)
    output.append(text)

p("=" * 100)
p("EROS 3.0 - BLOCK 98 READ-ONLY RUNTIME SAFETY VERIFICATION")
p("=" * 100)

p()
p("SOURCE:")
p(str(SOURCE))

if not SOURCE.exists():
    p("SOURCE ERROR: FILE NOT FOUND")
else:

    p()
    p("SOURCE : FOUND")
    p(f"SIZE   : {SOURCE.stat().st_size} bytes")

    # ------------------------------------------------------------
    # BOM-SAFE SOURCE INSPECTION
    # ------------------------------------------------------------

    source_text = SOURCE.read_text(
        encoding="utf-8-sig"
    )

    p()
    p("BOM-SAFE READ : PASS")

    # ------------------------------------------------------------
    # IMPORT TEST
    # ------------------------------------------------------------

    try:
        module = importlib.import_module(
            "services.quantitative.block98_execution_governance_bridge"
        )

        p("IMPORT : PASS")

        cls = getattr(
            module,
            "EROSBlock98ExecutionGovernanceBridge",
            None
        )

        if cls is None:
            p("CLASS : FAIL - CLASS NOT FOUND")
        else:
            p("CLASS : PASS")

            try:
                engine = cls()
                p("INSTANCE : PASS")
            except Exception as exc:
                engine = None
                p("INSTANCE : FAIL")
                p(f"{type(exc).__name__}: {exc}")

            # ----------------------------------------------------
            # DIRECT BLOCKED HELPER TEST
            # ----------------------------------------------------

            if engine is not None and hasattr(engine, "_blocked"):

                p()
                p("-" * 100)
                p("DIRECT _blocked() RUNTIME TEST")
                p("-" * 100)

                try:
                    blocked = engine._blocked(
                        "BLOCK_98_SAFETY_TEST"
                    )

                    p("CALL : PASS")
                    p()
                    p("BLOCKED RESULT:")
                    p(repr(blocked))

                    expected = {
                        "status": "BLOCKED",
                        "governance_status": "BLOCKED",
                        "execution_action": "BLOCK",
                        "execution_blocked": True,
                        "portfolio_mutation": False,
                        "valuation_mutation": False,
                        "performance_mutation": False,
                        "risk_mutation": False,
                        "optimization": False,
                        "order_creation": False,
                        "non_mutation_invariant": True,
                        "broker_submission": False,
                        "live_order_submission": False,
                    }

                    p()
                    p("SAFETY CONTRACT MATRIX")
                    p("-" * 60)

                    safety_pass = True

                    for key, expected_value in expected.items():

                        actual_value = blocked.get(
                            key,
                            "<ABSENT>"
                        )

                        p(
                            f"{key:<28}: "
                            f"{actual_value!r}"
                        )

                        if actual_value != expected_value:
                            safety_pass = False

                    p()
                    p("-" * 60)

                    if safety_pass:
                        p("BLOCK 98 SAFETY CONTRACT : PASS")
                    else:
                        p("BLOCK 98 SAFETY CONTRACT : FAIL")

                except Exception as exc:

                    p("CALL : FAIL")
                    p(
                        f"{type(exc).__name__}: {exc}"
                    )

            else:
                p()
                p("_blocked() : NOT FOUND")

            # ----------------------------------------------------
            # PUBLIC METHOD INVENTORY
            # ----------------------------------------------------

            p()
            p("-" * 100)
            p("PUBLIC GOVERNANCE METHODS")
            p("-" * 100)

            for method_name in (
                "certify",
                "evaluate",
                "govern",
            ):

                method = getattr(
                    engine,
                    method_name,
                    None
                )

                if callable(method):
                    p(
                        f"{method_name:<12}: FOUND"
                    )
                else:
                    p(
                        f"{method_name:<12}: ABSENT"
                    )

    except Exception as exc:

        p()
        p("IMPORT : FAIL")
        p(
            f"{type(exc).__name__}: {exc}"
        )

p()
p("=" * 100)
p("FINAL BLOCK 98 SAFETY RESULT")
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
    print("COMPLETE OUTPUT COPIED TO WINDOWS CLIPBOARD")
    print()
    print(">>> PRESS CTRL+V IN CHATGPT <<<")
    print("=" * 100)

except Exception as exc:

    print()
    print("=" * 100)
    print("CLIPBOARD : FAIL")
    print("=" * 100)
    print(type(exc).__name__, str(exc))
    print("=" * 100)

