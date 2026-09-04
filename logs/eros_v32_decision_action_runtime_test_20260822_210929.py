import json
import sys
import traceback

from services.eros_frontend_adapter import EROSFrontendAdapter

print("============================================================")
print("EROS 3.0 - V3.2 DECISION ACTION FRAMEWORK - RUNTIME")
print("============================================================")
print()

try:

    # --------------------------------------------------------
    # 1. IMPORT
    # --------------------------------------------------------

    adapter = EROSFrontendAdapter()

    print("1. ADAPTER IMPORT")
    print("------------------------------------------------------------")
    print("IMPORT : PASS")
    print("CLASS  :", adapter.__class__.__name__)
    print()

    # --------------------------------------------------------
    # 2. EXISTING API
    # --------------------------------------------------------

    required_existing = [
        "snapshot",
        "governance",
        "dashboard_snapshot",
        "market_scan",
        "stock_analysis",
        "decision_evidence",
        "decision_intelligence",
        "decision_interpretation",
    ]

    print("2. EXISTING API")
    print("------------------------------------------------------------")

    for name in required_existing:
        present = hasattr(adapter, name)
        print(
            f"{name:<30}: "
            f"{'PASS' if present else 'FAIL'}"
        )

    print()

    # --------------------------------------------------------
    # 3. V3.2 API DISCOVERY
    # --------------------------------------------------------

    print("3. V3.2 ACTION API DISCOVERY")
    print("------------------------------------------------------------")

    public_names = [
        name
        for name in dir(adapter)
        if not name.startswith("_")
    ]

    action_candidates = [
        name
        for name in public_names
        if "action" in name.lower()
        or "framework" in name.lower()
    ]

    if action_candidates:
        print("ACTION-RELATED API : PASS")
        for name in action_candidates:
            print(" -", name)
    else:
        print("ACTION-RELATED API : NOT FOUND")

    print()

    # --------------------------------------------------------
    # 4. DECISION INTERPRETATION
    # --------------------------------------------------------

    symbol = "RELIANCE.NS"

    print("4. DECISION INTERPRETATION")
    print("------------------------------------------------------------")
    print("SYMBOL :", symbol)

    interpretation = adapter.decision_interpretation(symbol)

    print("DECISION INTERPRETATION : PASS")
    print()

    print(json.dumps(
        interpretation,
        indent=2,
        default=str
    ))

    print()

    # --------------------------------------------------------
    # 5. V3.2 ACTION METHOD DISCOVERY / EXECUTION
    # --------------------------------------------------------

    print("5. V3.2 ACTION FRAMEWORK")
    print("------------------------------------------------------------")

    action_methods = [
        name
        for name in public_names
        if "action" in name.lower()
    ]

    action_result = None

    if not action_methods:
        print("ACTION API : NOT FOUND")
    else:

        print("ACTION METHODS FOUND :")

        for name in action_methods:
            print(" -", name)

        print()

        # Try the most likely action method.
        for method_name in action_methods:

            method = getattr(adapter, method_name)

            if not callable(method):
                continue

            try:

                # First attempt: symbol only.
                action_result = method(symbol)

                print(
                    "ACTION METHOD EXECUTED :",
                    method_name
                )
                print("ACTION RESULT : PASS")
                print()

                print(json.dumps(
                    action_result,
                    indent=2,
                    default=str
                ))

                break

            except TypeError:

                # Method may expect interpretation/evidence.
                try:

                    action_result = method(
                        interpretation
                    )

                    print(
                        "ACTION METHOD EXECUTED :",
                        method_name
                    )
                    print("ACTION RESULT : PASS")
                    print()

                    print(json.dumps(
                        action_result,
                        indent=2,
                        default=str
                    ))

                    break

                except Exception as inner_error:

                    print(
                        "ACTION METHOD SKIPPED :",
                        method_name
                    )
                    print(
                        "REASON :",
                        type(inner_error).__name__,
                        str(inner_error)
                    )

            except Exception as error:

                print(
                    "ACTION METHOD ERROR :",
                    method_name
                )
                print(
                    "REASON :",
                    type(error).__name__,
                    str(error)
                )

    print()

    # --------------------------------------------------------
    # 6. SAFETY CONTRACT
    # --------------------------------------------------------

    print("6. SAFETY CONTRACT")
    print("------------------------------------------------------------")

    governance = adapter.governance()

    safety = governance.get("safety", {})

    safety_fields = {
        "read_only": True,
        "execution_blocked": True,
        "non_mutation_invariant": True,
        "allow_order_creation": False,
        "allow_broker_submission": False,
        "allow_live_execution": False,
        "allow_portfolio_mutation": False,
        "allow_valuation_mutation": False,
        "allow_performance_mutation": False,
        "allow_risk_mutation": False,
        "allow_optimization": False,
    }

    safety_pass = True

    for field, expected in safety_fields.items():

        actual = safety.get(field)

        passed = actual == expected

        if not passed:
            safety_pass = False

        print(
            f"{field:<32}: "
            f"{'PASS' if passed else 'FAIL'} "
            f"(actual={actual!r}, expected={expected!r})"
        )

    print()

    # --------------------------------------------------------
    # 7. FINAL RESULT
    # --------------------------------------------------------

    print("============================================================")
    print("EROS 3.0 - V3.2 DECISION ACTION FRAMEWORK")
    print("============================================================")

    if safety_pass:
        print()
        print("SAFETY CONTRACT : PASS")
        print("READ_ONLY       : TRUE")
        print("EXECUTION_BLOCKED : TRUE")
        print("NON_MUTATION_INVARIANT : TRUE")
        print()
        print("FINAL RUNTIME SAFETY : PASS")
    else:
        print()
        print("SAFETY CONTRACT : FAIL")
        print("FINAL RUNTIME SAFETY : FAIL")

    print()
    print("============================================================")

except Exception as error:

    print()
    print("============================================================")
    print("RUNTIME TEST ERROR")
    print("============================================================")
    print()
    print("ERROR TYPE :", type(error).__name__)
    print("ERROR      :", str(error))
    print()
    traceback.print_exc()
    print()
    print("V3.2 RUNTIME TEST : FAIL")

    sys.exit(1)