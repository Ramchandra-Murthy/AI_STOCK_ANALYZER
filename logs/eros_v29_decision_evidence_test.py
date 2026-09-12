import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.eros_frontend_adapter import EROSFrontendAdapter

print("=" * 60)
print("EROS 3.0 - V2.9 DECISION EVIDENCE ADAPTER TEST")
print("=" * 60)

adapter = EROSFrontendAdapter()

print("")
print("1. IMPORT")
print("-" * 60)
print("IMPORT : PASS")
print("CLASS  :", adapter.__class__.__name__)

print("")
print("2. PUBLIC API")
print("-" * 60)

public_api = [name for name in dir(adapter) if not name.startswith("_")]

print("decision_evidence :", "PASS" if "decision_evidence" in public_api else "FAIL")

if "decision_evidence" not in public_api:
    raise RuntimeError("V29_DECISION_EVIDENCE_API_MISSING")

print("")
print("3. DECISION EVIDENCE")
print("-" * 60)

symbol = "RELIANCE.NS"

evidence = adapter.decision_evidence(symbol)

if not isinstance(evidence, dict):
    raise TypeError("DECISION_EVIDENCE_RESULT_NOT_DICT")

print("DECISION EVIDENCE : PASS")
print("SYMBOL :", evidence.get("symbol"))

print("")
print(json.dumps(evidence, indent=2, default=str))

print("")
print("4. REQUIRED FIELDS")
print("-" * 60)

required = [
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

for field in required:

    passed = field in evidence

    print("{0:<25} : {1}".format(field, "PASS" if passed else "FAIL"))

    if not passed:
        failed.append(field)

if failed:
    raise RuntimeError("V29_REQUIRED_FIELDS_FAILED: " + ", ".join(failed))

print("")
print("5. TECHNICAL INDICATORS")
print("-" * 60)

indicator_fields = [
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

failed = []

indicators = evidence["technical_indicators"]

for field in indicator_fields:

    passed = field in indicators

    print("{0:<20} : {1}".format(field, "PASS" if passed else "FAIL"))

    if not passed:
        failed.append(field)

if failed:
    raise RuntimeError("V29_INDICATORS_FAILED: " + ", ".join(failed))

print("")
print("6. SAFETY CONTRACT")
print("-" * 60)

safety = evidence["governance"]

checks = {
    "read_only": safety.get("read_only") is True,
    "execution_blocked": safety.get("execution_blocked") is True,
    "non_mutation_invariant": safety.get("non_mutation_invariant") is True,
}

failed = []

for name, passed in checks.items():

    print("{0:<30} : {1}".format(name, "PASS" if passed else "FAIL"))

    if not passed:
        failed.append(name)

if failed:
    raise RuntimeError("V29_SAFETY_FAILED: " + ", ".join(failed))

print("")
print("7. ORIGINAL APIs")
print("-" * 60)

checks = {
    "snapshot": hasattr(adapter, "snapshot"),
    "governance": hasattr(adapter, "governance"),
    "dashboard_snapshot": hasattr(adapter, "dashboard_snapshot"),
    "market_scan": hasattr(adapter, "market_scan"),
    "stock_analysis": hasattr(adapter, "stock_analysis"),
}

for name, passed in checks.items():

    print("{0:<25} : {1}".format(name, "PASS" if passed else "FAIL"))

if not all(checks.values()):
    raise RuntimeError("V29_EXISTING_API_REGRESSION")

print("")
print("=" * 60)
print("EROS 3.0 - V2.9 DECISION EVIDENCE ADAPTER TEST")
print("=" * 60)

print("")
print("DECISION EVIDENCE API : PASS")
print("NORMALIZED EVIDENCE   : PASS")
print("SAFETY CONTRACT       : PASS")
print("EXISTING API          : PASS")
print("DATABASE WRITE PATH   : NONE")
print("EXECUTION PATH        : BLOCKED")

print("")
print("FINAL RESULT : PASS")
print("V2.9 DECISION EVIDENCE API : CLEARED")
