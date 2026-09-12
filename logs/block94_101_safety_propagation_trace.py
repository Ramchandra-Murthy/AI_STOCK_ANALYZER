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

SAFETY_FIELDS = [
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

print("=" * 90)
print("EROS 3.0 - BLOCK 94-101 SAFETY PROPAGATION TRACE")
print("=" * 90)
print()
print("PURPOSE")
print("-------")
print("Read-only inspection of actual safety schemas and propagation.")
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO PORTFOLIO MUTATION")
print()

all_results = {}

for module_name in modules:

    print()
    print("=" * 90)
    print(module_name)
    print("=" * 90)

    try:
        module = importlib.import_module(module_name)
        print("IMPORT : PASS")
    except Exception as exc:
        print("IMPORT : FAIL")
        print(type(exc).__name__, str(exc))
        continue

    classes = [
        cls
        for name, cls in vars(module).items()
        if isinstance(cls, type)
        and getattr(cls, "__module__", None) == module_name
        and name.startswith("EROSBlock")
    ]

    for cls in classes:

        print()
        print("CLASS :", cls.__name__)

        try:
            instance = cls()
            print("INSTANCE : PASS")
        except Exception as exc:
            print("INSTANCE : FAIL")
            print(type(exc).__name__, str(exc))
            continue

        block_result = {
            "module": module_name,
            "class": cls.__name__,
        }

        # ------------------------------------------------------------
        # SNAPSHOT
        # ------------------------------------------------------------
        if hasattr(instance, "snapshot"):

            print()
            print("----- SNAPSHOT TRACE -----")

            try:
                snapshot = instance.snapshot()

                print("TYPE :", type(snapshot))

                if isinstance(snapshot, dict):

                    block_result["snapshot"] = snapshot

                    print()
                    print("TOP LEVEL KEYS:")
                    for key in snapshot:
                        print("  ", key)

                    print()
                    print("SAFETY FIELD LOCATION:")
                    for field in SAFETY_FIELDS:

                        locations = []

                        if field in snapshot:
                            locations.append("TOP_LEVEL=" + repr(snapshot[field]))

                        for parent_key, parent_value in snapshot.items():
                            if isinstance(parent_value, dict):
                                if field in parent_value:
                                    locations.append(
                                        f"NESTED[{parent_key}]=" + repr(parent_value[field])
                                    )

                        if locations:
                            print(f"{field:28} : " + " | ".join(locations))
                        else:
                            print(f"{field:28} : ABSENT")

                    print()
                    print("FULL SNAPSHOT:")
                    pprint(snapshot, width=160, sort_dicts=False)

            except Exception as exc:
                print("SNAPSHOT ERROR")
                print(type(exc).__name__, str(exc))

        # ------------------------------------------------------------
        # HISTORY
        # ------------------------------------------------------------
        for history_method in [
            "certificate_history",
            "scenario_history",
        ]:

            if not hasattr(instance, history_method):
                continue

            print()
            print("-----", history_method, "-----")

            try:
                history = getattr(instance, history_method)()

                print("TYPE :", type(history))
                pprint(history, width=160, sort_dicts=False)

            except Exception as exc:
                print("HISTORY ERROR")
                print(type(exc).__name__, str(exc))

        all_results[cls.__name__] = block_result

# ====================================================================
# SOURCE-LEVEL SAFETY CONSTANT TRACE
# ====================================================================

print()
print("=" * 90)
print("SOURCE-LEVEL SAFETY CONSTANT TRACE")
print("=" * 90)

for module_name in modules:

    print()
    print("-" * 90)
    print(module_name)
    print("-" * 90)

    try:
        module = importlib.import_module(module_name)

        source = inspect_source = None

        import inspect

        source = inspect.getsource(module)

        for field in SAFETY_FIELDS:

            occurrences = [line.strip() for line in source.splitlines() if field in line]

            if occurrences:
                print()
                print(field + " :")
                for line in occurrences[:20]:
                    print("   ", line)

    except Exception as exc:
        print("SOURCE TRACE ERROR")
        print(type(exc).__name__, str(exc))

# ====================================================================
# FINAL SUMMARY
# ====================================================================

print()
print("=" * 90)
print("FINAL SAFETY FIELD SUMMARY")
print("=" * 90)

for class_name, result in all_results.items():

    print()
    print(class_name)

    snapshot = result.get("snapshot")

    if not isinstance(snapshot, dict):
        print("  SNAPSHOT : UNAVAILABLE")
        continue

    for field in SAFETY_FIELDS:

        if field in snapshot:
            print(f"  {field:28} TOP_LEVEL = " f"{snapshot[field]!r}")
            continue

        nested = []

        for parent_key, parent_value in snapshot.items():
            if isinstance(parent_value, dict):
                if field in parent_value:
                    nested.append(f"{parent_key}={parent_value[field]!r}")

        if nested:
            print(f"  {field:28} NESTED = " + " | ".join(nested))
        else:
            print(f"  {field:28} ABSENT")

print()
print("=" * 90)
print("SAFETY PROPAGATION TRACE COMPLETE")
print("=" * 90)
print("READ ONLY")
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO PORTFOLIO MUTATION")
print("=" * 90)
