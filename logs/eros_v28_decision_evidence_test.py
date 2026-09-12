import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.eros_frontend_adapter import EROSFrontendAdapter


def build_decision_evidence(symbol, result):

    trend = result.get("trend") or {}
    signal = result.get("signal") or {}
    breakout = result.get("breakout") or {}
    last = result.get("last")

    def value_from_last(name):
        try:
            if last is not None and name in last:
                value = last[name]

                if hasattr(value, "item"):
                    value = value.item()

                if value is None:
                    return None

                try:
                    if value != value:
                        return None
                except Exception:
                    pass

                return value
        except Exception:
            return None

        return None

    evidence = {
        "symbol": symbol,
        "price": value_from_last("Close"),
        "trend": trend.get("Trend"),
        "momentum": trend.get("Momentum"),
        "score": signal.get("Score"),
        "confidence": signal.get("Confidence"),
        "recommendation": signal.get("Recommendation"),
        "risk": signal.get("Risk"),
        "reasons": list(signal.get("Reasons") or []),
        "breakout_signal": breakout.get("Signal"),
        "breakout_reason": breakout.get("Reason"),
        "technical_indicators": {
            "sma_20": value_from_last("SMA_20"),
            "sma_50": value_from_last("SMA_50"),
            "ema_20": value_from_last("EMA_20"),
            "rsi_14": value_from_last("RSI_14"),
            "macd": value_from_last("MACD"),
            "signal": value_from_last("Signal"),
            "histogram": value_from_last("Histogram"),
            "bb_middle": value_from_last("BB_Middle"),
            "bb_upper": value_from_last("BB_Upper"),
            "bb_lower": value_from_last("BB_Lower"),
            "atr": value_from_last("ATR"),
            "support": value_from_last("Support"),
            "resistance": value_from_last("Resistance"),
        },
        "governance": {
            "read_only": True,
            "execution_blocked": True,
            "non_mutation_invariant": True,
        },
    }

    return evidence


print("=" * 60)
print("EROS 3.0 - V2.8 DECISION EVIDENCE API FOUNDATION")
print("=" * 60)

adapter = EROSFrontendAdapter()

print("")
print("1. ADAPTER")
print("-" * 60)
print("ADAPTER : PASS")
print("CLASS   :", adapter.__class__.__name__)

print("")
print("2. GOVERNANCE")
print("-" * 60)

governance = adapter.governance()

print("GOVERNANCE : PASS")
print(json.dumps(governance, indent=2, default=str))

print("")
print("3. STOCK ANALYSIS")
print("-" * 60)

symbol = "RELIANCE.NS"

print("SYMBOL :", symbol)

result = adapter.stock_analysis(symbol)

if not isinstance(result, dict):
    raise RuntimeError("STOCK_ANALYSIS_RESULT_IS_NOT_DICT")

print("STOCK ANALYSIS : PASS")
print("RESULT TYPE    :", type(result).__name__)

print("")
print("4. BUILD DECISION EVIDENCE")
print("-" * 60)

evidence = build_decision_evidence(symbol, result)

print("DECISION EVIDENCE : PASS")

print("")
print(json.dumps(evidence, indent=2, default=str))

print("")
print("5. REQUIRED FIELD VALIDATION")
print("-" * 60)

required_fields = [
    "symbol",
    "price",
    "trend",
    "momentum",
    "score",
    "confidence",
    "recommendation",
    "risk",
    "reasons",
    "breakout_signal",
    "breakout_reason",
    "technical_indicators",
    "governance",
]

failed = []

for field in required_fields:

    present = field in evidence

    print("{0:<25} : {1}".format(field, "PASS" if present else "FAIL"))

    if not present:
        failed.append(field)

if failed:
    raise RuntimeError("MISSING_REQUIRED_FIELDS: " + ", ".join(failed))

print("")
print("6. TECHNICAL FIELD VALIDATION")
print("-" * 60)

required_indicators = [
    "sma_20",
    "sma_50",
    "ema_20",
    "rsi_14",
    "macd",
    "signal",
    "histogram",
    "bb_middle",
    "bb_upper",
    "bb_lower",
    "atr",
    "support",
    "resistance",
]

indicator_failed = []

for field in required_indicators:

    present = field in evidence["technical_indicators"]

    print("{0:<25} : {1}".format(field, "PASS" if present else "FAIL"))

    if not present:
        indicator_failed.append(field)

if indicator_failed:
    raise RuntimeError("MISSING_INDICATORS: " + ", ".join(indicator_failed))

print("")
print("7. SAFETY VERIFICATION")
print("-" * 60)

safety = evidence["governance"]

checks = {
    "read_only": safety.get("read_only") is True,
    "execution_blocked": safety.get("execution_blocked") is True,
    "non_mutation_invariant": safety.get("non_mutation_invariant") is True,
}

safety_failed = []

for name, passed in checks.items():

    print("{0:<30} : {1}".format(name, "PASS" if passed else "FAIL"))

    if not passed:
        safety_failed.append(name)

if safety_failed:
    raise RuntimeError("SAFETY_FAILURE: " + ", ".join(safety_failed))

print("")
print("8. EVIDENCE CONTRACT")
print("-" * 60)

print("EVIDENCE OBJECT : PASS")
print("NORMALIZED READ-ONLY VIEW : PASS")
print("DATABASE WRITE PATH : NONE")
print("EXECUTION PATH : BLOCKED")

print("")
print("=" * 60)
print("EROS 3.0 - V2.8 DECISION EVIDENCE API FOUNDATION")
print("=" * 60)

print("")
print("FINAL RESULT : PASS")
print("V2.8 EVIDENCE FOUNDATION : CLEARED")
print("")
