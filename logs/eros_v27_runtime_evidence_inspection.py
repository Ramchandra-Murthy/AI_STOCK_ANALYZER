from __future__ import annotations

import json
import sys
import traceback

from services.eros_frontend_adapter import EROSFrontendAdapter


def safe_print(title, value):
    print("")
    print("=" * 60)
    print(title)
    print("=" * 60)

    try:
        print(json.dumps(value, indent=2, default=str))
    except Exception:
        print(repr(value))


print("=" * 60)
print("EROS 3.0 - V2.7 RUNTIME DECISION EVIDENCE INSPECTION")
print("=" * 60)

try:

    print("")
    print("1. ADAPTER IMPORT")
    print("-" * 60)

    adapter = EROSFrontendAdapter()

    print("IMPORT : PASS")
    print("CLASS  :", type(adapter).__name__)

    print("")
    print("2. ADAPTER SNAPSHOT")
    print("-" * 60)

    snapshot = adapter.snapshot()

    print("SNAPSHOT : PASS")
    print(json.dumps(snapshot, indent=2, default=str))

    print("")
    print("3. DASHBOARD SNAPSHOT")
    print("-" * 60)

    dashboard = adapter.dashboard_snapshot()

    print("DASHBOARD SNAPSHOT : PASS")
    print(json.dumps(dashboard, indent=2, default=str))

    print("")
    print("4. STOCK ANALYSIS TEST")
    print("-" * 60)

    symbol = "RELIANCE.NS"

    print("SYMBOL :", symbol)

    result = adapter.stock_analysis(symbol)

    print("")
    print("STOCK ANALYSIS : PASS")
    print("RESULT TYPE    :", type(result).__name__)

    safe_print("5. RAW STOCK ANALYSIS RESULT", result)

    print("")
    print("6. RESULT STRUCTURE")
    print("-" * 60)

    if isinstance(result, dict):

        print("RESULT IS DICT : PASS")
        print("")
        print("TOP-LEVEL KEYS :")

        for key in result.keys():
            print(" -", key)

        print("")
        print("KEY TYPES :")

        for key, value in result.items():
            print(
                " - {0} : {1}".format(
                    key,
                    type(value).__name__
                )
            )

    else:

        print("RESULT IS DICT : FAIL")
        print("OBJECT :", repr(result))

    print("")
    print("7. DECISION EVIDENCE FIELD DISCOVERY")
    print("-" * 60)

    required_candidates = [
        "AI Score",
        "AI_Score",
        "ai_score",
        "AI Score",
        "Confidence",
        "confidence",
        "Recommendation",
        "recommendation",
        "Risk",
        "risk",
        "Trend",
        "trend",
        "RSI",
        "rsi",
        "MACD",
        "macd",
        "ATR",
        "atr",
        "Breakout",
        "breakout",
        "Signal",
        "signal",
        "Reasons",
        "reasons",
        "Reason",
        "reason",
        "Drivers",
        "drivers",
        "Signal Drivers",
        "signal_drivers",
    ]

    if isinstance(result, dict):

        found = []

        for candidate in required_candidates:

            if candidate in result:
                found.append(candidate)

        if found:

            print("DIRECT EVIDENCE FIELDS FOUND :")
            for key in found:
                print(" -", key)

        else:

            print("DIRECT EVIDENCE FIELDS : NONE")

        print("")
        print("NESTED STRUCTURES :")

        for key, value in result.items():

            if isinstance(value, dict):

                print("")
                print("DICT :", key)

                for nested_key in value.keys():
                    print("   -", nested_key)

            elif isinstance(value, list):

                print("")
                print("LIST :", key)

                print("   LENGTH :", len(value))

                if value:
                    print("   FIRST ITEM TYPE :", type(value[0]).__name__)

                    if isinstance(value[0], dict):
                        print("   FIRST ITEM KEYS :")
                        for nested_key in value[0].keys():
                            print("      -", nested_key)

    print("")
    print("8. DECISION EVIDENCE RECURSIVE SEARCH")
    print("-" * 60)

    evidence_terms = {
        "score",
        "confidence",
        "recommendation",
        "risk",
        "trend",
        "rsi",
        "macd",
        "atr",
        "breakout",
        "signal",
        "reason",
        "driver",
        "technical",
        "structure",
    }

    def walk(obj, path="root"):

        if isinstance(obj, dict):

            for key, value in obj.items():

                key_text = str(key)
                key_lower = key_text.lower()

                if any(term in key_lower for term in evidence_terms):

                    print(
                        "MATCH:",
                        path + "." + key_text,
                        "=",
                        repr(value)
                    )

                walk(value, path + "." + key_text)

        elif isinstance(obj, list):

            for index, item in enumerate(obj):

                walk(
                    item,
                    path + "[" + str(index) + "]"
                )

    walk(result)

    print("")
    print("9. SAFETY VERIFICATION")
    print("-" * 60)

    governance = adapter.governance()

    safety = governance["safety"]

    required = {
        "read_only": True,
        "allow_order_creation": False,
        "allow_broker_submission": False,
        "allow_live_execution": False,
        "allow_portfolio_mutation": False,
        "allow_valuation_mutation": False,
        "allow_performance_mutation": False,
        "allow_risk_mutation": False,
        "allow_optimization": False,
        "execution_blocked": True,
        "non_mutation_invariant": True,
    }

    failures = []

    for key, expected in required.items():

        actual = safety.get(key)

        if actual != expected:
            failures.append(
                "{0}: expected={1}, actual={2}".format(
                    key,
                    expected,
                    actual
                )
            )

    if failures:

        print("SAFETY : FAIL")

        for failure in failures:
            print(" -", failure)

        raise RuntimeError("V27_SAFETY_FAILED")

    print("SAFETY : PASS")

    print("")
    print("============================================================")
    print("EROS 3.0 - V2.7 RUNTIME DECISION EVIDENCE INSPECTION COMPLETE")
    print("============================================================")
    print("")
    print("NO FILES WERE MODIFIED.")
    print("")

except Exception as exc:

    print("")
    print("============================================================")
    print("V2.7 RUNTIME INSPECTION : FAIL")
    print("============================================================")
    print("")
    print("EXCEPTION TYPE :", type(exc).__name__)
    print("EXCEPTION      :", str(exc))
    print("")
    print("TRACEBACK")
    print("-" * 60)
    traceback.print_exc()
    print("")

    sys.exit(1)
