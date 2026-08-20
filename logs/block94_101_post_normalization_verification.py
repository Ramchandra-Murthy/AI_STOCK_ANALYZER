import importlib

modules = {
    94: "services.quantitative.block94_portfolio_stress_scenario_engine",
    95: "services.quantitative.block95_stress_evidence_gate",
    96: "services.quantitative.block96_stress_decision_gate",
    97: "services.quantitative.block97_stress_readiness_gate",
    98: "services.quantitative.block98_execution_governance_bridge",
    99: "services.quantitative.block99_execution_intent_authorization_gate",
    100: "services.quantitative.block100_paper_execution_fill_gate",
    101: "services.quantitative.block101_execution_evidence_reconciliation",
}

required = [
    "execution_blocked",
    "non_mutation_invariant",
    "broker_submission",
    "live_order_submission",
]

print("=" * 80)
print("EROS 3.0 - POST-NORMALIZATION SAFETY VERIFICATION")
print("=" * 80)

for block_id, module_name in modules.items():

    print()
    print("=" * 80)
    print(f"BLOCK {block_id}")
    print("=" * 80)

    try:
        module = importlib.import_module(module_name)
        print("IMPORT : PASS")
    except Exception as exc:
        print("IMPORT : FAIL")
        print(type(exc).__name__, str(exc))
        continue

    classes = [
        cls for name, cls in vars(module).items()
        if isinstance(cls, type)
        and getattr(cls, "__module__", None) == module_name
        and name.startswith("EROSBlock")
    ]

    for cls in classes:
        print("CLASS :", cls.__name__)

        try:
            instance = cls()
            print("INSTANCE : PASS")
        except Exception as exc:
            print("INSTANCE : FAIL")
            print(type(exc).__name__, str(exc))
            continue

        if not hasattr(instance, "snapshot"):
            print("SNAPSHOT : ABSENT")
            continue

        try:
            snapshot = instance.snapshot()
            print("SNAPSHOT : PASS")
            print("TOP LEVEL KEYS:", list(snapshot.keys()))

            print()
            print("SAFETY FIELDS IN SNAPSHOT:")

            for key in required:
                if key in snapshot:
                    print(f"  {key:28} : {snapshot[key]!r}")
                else:
                    print(f"  {key:28} : <ABSENT>")

        except Exception as exc:
            print("SNAPSHOT : ERROR")
            print(type(exc).__name__, str(exc))

print()
print("=" * 80)
print("POST-NORMALIZATION VERIFICATION COMPLETE")
print("=" * 80)
print("EXPECTED:")
print("  execution_blocked      = True")
print("  non_mutation_invariant = True")
print("  broker_submission      = False")
print("  live_order_submission  = False")
print("=" * 80)
