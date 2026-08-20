import importlib
import inspect

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
print("EROS 3.0 - BLOCK 94-101 REAL DATA-FLOW AUDIT")
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

    for class_name, cls in inspect.getmembers(module, inspect.isclass):
        if getattr(cls, "__module__", None) != module_name:
            continue

        print()
        print("CLASS :", class_name)

        public_methods = [
            (name, method)
            for name, method in inspect.getmembers(cls, inspect.isfunction)
            if not name.startswith("_")
        ]

        for method_name, method in public_methods:
            try:
                signature = inspect.signature(method)
            except Exception:
                signature = "<unavailable>"

            print("  METHOD :", method_name)
            print("  SIGNATURE:", signature)

print()
print("=" * 70)
print("IMPORT / INTERFACE AUDIT COMPLETE")
print("=" * 70)
print("IMPORTANT: This stage performs inspection only.")
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print("=" * 70)
