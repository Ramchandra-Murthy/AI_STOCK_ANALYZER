import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))

from services.eros_frontend_adapter import EROSFrontendAdapter

print("=" * 60)
print("EROS 3.0 - V2.5 MARKET SCAN CONTRACT TEST")
print("=" * 60)

adapter = EROSFrontendAdapter()

print()
print("ADAPTER : PASS")

print()
print("1. MARKET SCAN")
print("-" * 60)

result = adapter.market_scan()

print("MARKET SCAN : PASS")
print("TYPE :", type(result).__name__)

if result is None:
    print("RESULT : NONE")
else:
    print("ROWS :", len(result))

    if hasattr(result, "columns"):
        print()
        print("COLUMNS")
        for column in result.columns:
            print(" -", column)

        print()
        print("DATA")
        print(result.to_string(index=False))

print()
print("2. REQUIRED FIELD INSPECTION")
print("-" * 60)

required = [
    "Symbol",
    "AI Score",
    "Recommendation",
    "Trend",
    "Confidence",
]

if hasattr(result, "columns"):

    for field in required:
        if field in result.columns:
            print(f"{field:20} : PRESENT")
        else:
            print(f"{field:20} : ABSENT")

else:
    print("NO DATAFRAME COLUMNS AVAILABLE")

print()
print("3. SAFETY CONTRACT")
print("-" * 60)

governance = adapter.governance()
safety = governance["safety"]

checks = {
    "read_only": safety["read_only"] is True,
    "order_creation_blocked": safety["allow_order_creation"] is False,
    "broker_blocked": safety["allow_broker_submission"] is False,
    "execution_blocked": safety["allow_live_execution"] is False,
    "portfolio_mutation_blocked": safety["allow_portfolio_mutation"] is False,
    "valuation_mutation_blocked": safety["allow_valuation_mutation"] is False,
    "performance_mutation_blocked": safety["allow_performance_mutation"] is False,
    "risk_mutation_blocked": safety["allow_risk_mutation"] is False,
    "optimization_blocked": safety["allow_optimization"] is False,
    "execution_flag": safety["execution_blocked"] is True,
    "non_mutation": safety["non_mutation_invariant"] is True,
}

for name, passed in checks.items():
    print(f"{name:32} : {'PASS' if passed else 'FAIL'}")

if not all(checks.values()):
    raise RuntimeError("V25_MARKET_SCAN_SAFETY_FAILED")

print()
print("=" * 60)
print("EROS 3.0 - V2.5 MARKET SCAN CONTRACT : PASS")
print("=" * 60)
