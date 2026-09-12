from services.eros_frontend_adapter import EROSFrontendAdapter

adapter = EROSFrontendAdapter()

required = [
    "decision_evidence",
    "decision_intelligence",
    "decision_interpretation",
    "decision_action_framework",
    "decision_action_explanation",
    "decision_scenario_engine",
    "decision_scenario_explanation",
    "decision_convergence",
]

print("V3.6 FOUNDATION API CHECK")

for name in required:
    ok = hasattr(adapter, name)
    print(f"{name:35} : {'PRESENT' if ok else 'ABSENT'}")
    if not ok:
        raise RuntimeError(f"MISSING_V36_API:{name}")

print("V3.6 FOUNDATION : VERIFIED")
