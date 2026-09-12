import importlib
from pprint import pprint

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

print("=" * 80)
print("EROS 3.0 - BLOCK 94-101 ACTUAL SAFETY SCHEMA TRACE")
print("=" * 80)

for module_name in modules:

    print()
    print("=" * 80)
    print(module_name)
    print("=" * 80)

    try:
        module = importlib.import_module(module_name)
        print("IMPORT : PASS")
    except Exception as exc:
        print("IMPORT : FAIL")
        print(type(exc).__name__, str(exc))
        continue

    eros_classes = [
        cls
        for name, cls in vars(module).items()
        if isinstance(cls, type)
        and getattr(cls, "__module__", None) == module_name
        and name.startswith("EROSBlock")
    ]

    for cls in eros_classes:

        print()
        print("CLASS :", cls.__name__)

        try:
            instance = cls()
            print("INSTANCE : PASS")
        except Exception as exc:
            print("INSTANCE : FAIL")
            print(type(exc).__name__, str(exc))
            continue

        # Inspect snapshot if available
        if hasattr(instance, "snapshot"):

            print()
            print("----- SNAPSHOT -----")

            try:
                snapshot = instance.snapshot()

                print("TYPE :", type(snapshot))

                if isinstance(snapshot, dict):
                    print("TOP LEVEL KEYS:")
                    for key in snapshot.keys():
                        print("  ", key)

                    print()
                    print("FULL SNAPSHOT:")
                    pprint(snapshot, width=140, sort_dicts=False)

            except Exception as exc:
                print("SNAPSHOT ERROR")
                print(type(exc).__name__, str(exc))

        # Inspect empty history methods if present
        for history_method in [
            "certificate_history",
            "scenario_history",
        ]:

            if not hasattr(instance, history_method):
                continue

            print()
            print("-----", history_method, "-----")

            try:
                result = getattr(instance, history_method)()

                print("TYPE :", type(result))
                pprint(result, width=140, sort_dicts=False)

            except Exception as exc:
                print("HISTORY ERROR")
                print(type(exc).__name__, str(exc))

print()
print("=" * 80)
print("ACTUAL SAFETY SCHEMA TRACE COMPLETE")
print("=" * 80)
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print("=" * 80)
