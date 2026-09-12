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
    "services.quantitative.block102_frontend_contract",
    "services.quantitative.block103_institutional_frontend_read_model",
    "services.quantitative.block104_eros_command_center",
    "services.quantitative.block106_institutional_integration_boundary",
]

print("=" * 70)
print("EROS 3.0 - BLOCK 94-106 ARCHITECTURE AUDIT")
print("=" * 70)

for name in modules:
    print()
    print("=" * 70)
    print(name)
    print("=" * 70)

    try:
        module = importlib.import_module(name)
        print("IMPORT : PASS")
    except Exception as exc:
        print("IMPORT : FAIL")
        print(type(exc).__name__, str(exc))
        continue

    found = False

    for class_name, cls in inspect.getmembers(module, inspect.isclass):
        if getattr(cls, "__module__", None) != name:
            continue

        found = True
        print()
        print("CLASS :", class_name)

        for method_name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if method_name.startswith("_"):
                continue

            try:
                sig = inspect.signature(method)
            except Exception:
                sig = "<unavailable>"

            print("  METHOD :", method_name)
            print("  SIGNATURE:", sig)

    if not found:
        print("NO MODULE CLASSES FOUND")

print()
print("=" * 70)
print("ARCHITECTURE AUDIT COMPLETE")
print("=" * 70)
