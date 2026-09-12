from __future__ import annotations

import sys
import traceback

PROJECT_ROOT = r"D:\Users\User\Desktop\AI_STOCK_ANALYZER"

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.eros_frontend_adapter import EROSFrontendAdapter

print("=" * 70)
print("EROS 3.0 - V3.8.2.9 MIDDLE-LAYER RUNTIME HYDRATION TEST")
print("=" * 70)

adapter = EROSFrontendAdapter()
symbol = "RELIANCE.NS"

methods = [
    "decision_evidence",
    "decision_intelligence",
    "decision_interpretation",
    "decision_action_framework",
    "decision_action_explanation",
    "decision_scenario_engine",
    "decision_scenario_explanation",
    "decision_convergence",
    "decision_traceability",
]

for name in methods:

    print("\n" + "=" * 70)
    print("METHOD:", name)
    print("=" * 70)

    try:
        fn = getattr(adapter, name)
        result = fn(symbol)

        print("CALL : PASS")
        print("TYPE :", type(result).__name__)

        if not isinstance(result, dict):
            print("VALUE:", repr(result)[:3000])
            continue

        print("KEY COUNT:", len(result))
        print("KEYS:", list(result.keys()))

        for key, value in result.items():

            if isinstance(value, dict):
                print(f"  {key}: DICT " f"({len(value)} keys)")

                print("    keys:", list(value.keys())[:25])

            elif isinstance(value, list):
                print(f"  {key}: LIST " f"({len(value)} items)")

                if value:
                    print("    first:", repr(value[0])[:1000])

            elif value is None:
                print(f"  {key}: NONE")

            elif value == "":
                print(f"  {key}: EMPTY STRING")

            else:
                print(f"  {key}: " f"{type(value).__name__} = " f"{repr(value)[:1000]}")

    except Exception:
        print("CALL : FAIL")
        traceback.print_exc()

print("\n" + "=" * 70)
print("V3.8.2.9 TEST COMPLETE")
print("=" * 70)
print("NO SOURCE PATCH")
print("NO DATABASE WRITE")
print("NO BROKER CALL")
print("NO ORDER CREATION")
print("NO PORTFOLIO MUTATION")
