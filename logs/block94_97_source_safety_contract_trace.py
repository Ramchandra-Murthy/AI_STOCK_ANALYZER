import importlib
import inspect

modules = [
    "services.quantitative.block94_portfolio_stress_scenario_engine",
    "services.quantitative.block95_stress_evidence_gate",
    "services.quantitative.block96_stress_decision_gate",
    "services.quantitative.block97_stress_readiness_gate",
]

output = []


def emit(text=""):
    print(text)
    output.append(str(text))


emit("=" * 90)
emit("EROS 3.0 - BLOCK 94-97 SOURCE SAFETY CONTRACT TRACE")
emit("=" * 90)
emit("")
emit("PURPOSE:")
emit("Identify the exact source-level return boundaries where the common")
emit("execution safety contract is missing before Block 98.")
emit("")
emit("READ ONLY")
emit("NO SOURCE CHANGES")
emit("NO BROKER")
emit("NO LIVE EXECUTION")
emit("NO ORDER CREATION")
emit("NO MUTATION")
emit("=" * 90)

for module_name in modules:

    emit("")
    emit("=" * 90)
    emit(module_name)
    emit("=" * 90)

    try:
        module = importlib.import_module(module_name)
        emit("IMPORT : PASS")
    except Exception as exc:
        emit("IMPORT : FAIL")
        emit(f"{type(exc).__name__}: {exc}")
        continue

    classes = [
        cls
        for name, cls in vars(module).items()
        if isinstance(cls, type)
        and getattr(cls, "__module__", None) == module_name
        and name.startswith("EROSBlock")
    ]

    for cls in classes:

        emit("")
        emit(f"CLASS : {cls.__name__}")

        methods_to_trace = [
            "certify",
            "gate",
            "decide",
            "evaluate",
            "stress_portfolio",
            "run_scenario",
            "run_scenarios",
        ]

        for method_name in methods_to_trace:

            if not hasattr(cls, method_name):
                continue

            method = getattr(cls, method_name)

            emit("")
            emit("-" * 90)
            emit(f"METHOD : {method_name}")
            emit("-" * 90)

            try:
                sig = inspect.signature(method)
                emit(f"SIGNATURE : {sig}")
            except Exception:
                emit("SIGNATURE : <unavailable>")

            try:
                source = inspect.getsource(method)

                lines = source.splitlines()

                emit("")
                emit("SOURCE:")
                emit("-" * 90)

                for index, line in enumerate(lines, start=1):
                    emit(f"{index:04d} | {line}")

                emit("-" * 90)

                safety_keywords = [
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
                    "status",
                    "reason_code",
                    "reason",
                ]

                emit("")
                emit("SAFETY KEYWORD PRESENCE:")
                for keyword in safety_keywords:
                    found = keyword in source
                    emit(f"{keyword:28} : {found}")

            except Exception as exc:
                emit("SOURCE INSPECTION ERROR")
                emit(f"{type(exc).__name__}: {exc}")

emit("")
emit("=" * 90)
emit("SOURCE CONTRACT TRACE COMPLETE")
emit("=" * 90)
emit("")
emit("ARCHITECTURAL QUESTION:")
emit("Where exactly should the common safety contract be introduced?")
emit("")
emit("EXPECTED CONTRACT:")
emit("execution_blocked = True")
emit("non_mutation_invariant = True")
emit("broker_submission = False")
emit("live_order_submission = False")
emit("")
emit("NO SOURCE CHANGES WERE MADE")
emit("=" * 90)

# Copy complete output to Windows clipboard
try:
    import subprocess

    complete_output = "\r\n".join(output)

    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Set-Clipboard -Value ([Console]::In.ReadToEnd())",
        ],
        input=complete_output,
        text=True,
        check=True,
    )

    print("")
    print("=" * 90)
    print("CLIPBOARD : SUCCESS")
    print("The complete audit output is now copied to the Windows clipboard.")
    print("Paste it directly into ChatGPT.")
    print("=" * 90)

except Exception as exc:
    print("")
    print("=" * 90)
    print("CLIPBOARD : FAILED")
    print(type(exc).__name__, str(exc))
    print("The audit itself completed successfully.")
    print("=" * 90)
