import importlib

modules = [
    "services.quantitative.block94_portfolio_stress_scenario_engine",
    "services.quantitative.block95_stress_evidence_gate",
    "services.quantitative.block96_stress_decision_gate",
    "services.quantitative.block97_stress_readiness_gate",
    "services.quantitative.block98_execution_governance_bridge",
    "services.quantitative.block99_execution_intent_authorization_gate",
    "services.quantitative.block100_paper_execution_fill_gate",
    "services.quantitative.block101_execution_evidence_reconciliation",
]

print("=" * 70)
print("EROS 3.0 - BLOCK 94-101 SAFETY FIELD INSPECTION")
print("=" * 70)

for module_name in modules:
    print()
    print("=" * 70)
    print(module_name)
    print("=" * 70)

    try:
        module = importlib.import_module(module_name)
        print("IMPORT : PASS")
    except Exception as exc:
        print("IMPORT : FAIL")
        print(type(exc).__name__, str(exc))
        continue

    for class_name, cls in vars(module).items():
        if not isinstance(cls, type):
            continue

        if getattr(cls, "__module__", None) != module_name:
            continue

        if not class_name.startswith("EROSBlock"):
            continue

        print()
        print("CLASS :", class_name)

        try:
            instance = cls()
        except Exception as exc:
            print("INSTANCE : FAIL")
            print(type(exc).__name__, str(exc))
            continue

        print("INSTANCE : PASS")

        for method_name in [
            "snapshot",
            "certificate_history",
            "scenario_history",
        ]:
            if not hasattr(instance, method_name):
                continue

            method = getattr(instance, method_name)

            try:
                result = method()

                print()
                print("METHOD :", method_name)
                print("TYPE   :", type(result))

                if isinstance(result, dict):
                    print("TOP KEYS:", list(result.keys()))

                    for key in [
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
                    ]:
                        print(
                            f"{key:28} : "
                            f"{result.get(key, '<ABSENT>')!r}"
                        )

                    if isinstance(result.get("safety"), dict):
                        print()
                        print("NESTED SAFETY:")
                        for key, value in result["safety"].items():
                            print(f"  {key:26} : {value!r}")

            except Exception as exc:
                print()
                print("METHOD :", method_name)
                print("RESULT : ERROR")
                print(type(exc).__name__, str(exc))

print()
print("=" * 70)
print("SAFETY FIELD INSPECTION COMPLETE")
print("=" * 70)
print("READ ONLY")
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print("=" * 70)
