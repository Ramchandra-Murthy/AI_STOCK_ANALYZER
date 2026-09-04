import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))

from services.eros_frontend_adapter import EROSFrontendAdapter

print("=" * 60)
print("EROS 3.0 - V2.5 DASHBOARD SNAPSHOT CONTRACT TEST")
print("=" * 60)

adapter = EROSFrontendAdapter()

print()
print("ADAPTER : PASS")
print("CLASS   :", type(adapter).__name__)

print()
print("1. SNAPSHOT")
snapshot = adapter.snapshot()
print("SNAPSHOT : PASS")
print(snapshot)

print()
print("2. GOVERNANCE")
governance = adapter.governance()
print("GOVERNANCE : PASS")
print(governance)

print()
print("3. DASHBOARD SNAPSHOT")
dashboard = adapter.dashboard_snapshot()
print("DASHBOARD SNAPSHOT : PASS")
print(dashboard)

print()
print("4. MARKET SCAN API")
if hasattr(adapter, "market_scan"):
    print("MARKET SCAN METHOD : PRESENT")
else:
    print("MARKET SCAN METHOD : MISSING")

print()
print("5. STOCK ANALYSIS API")
if hasattr(adapter, "stock_analysis"):
    print("STOCK ANALYSIS METHOD : PRESENT")
else:
    print("STOCK ANALYSIS METHOD : MISSING")

print()
print("6. SAFETY INVARIANTS")

safety = governance["safety"]

checks = {
    "read_only": safety["read_only"] is True,
    "allow_order_creation": safety["allow_order_creation"] is False,
    "allow_broker_submission": safety["allow_broker_submission"] is False,
    "allow_live_execution": safety["allow_live_execution"] is False,
    "allow_portfolio_mutation": safety["allow_portfolio_mutation"] is False,
    "allow_valuation_mutation": safety["allow_valuation_mutation"] is False,
    "allow_performance_mutation": safety["allow_performance_mutation"] is False,
    "allow_risk_mutation": safety["allow_risk_mutation"] is False,
    "allow_optimization": safety["allow_optimization"] is False,
    "execution_blocked": safety["execution_blocked"] is True,
    "non_mutation_invariant": safety["non_mutation_invariant"] is True,
}

for key, passed in checks.items():
    print(f"{key:32} : {'PASS' if passed else 'FAIL'}")

if not all(checks.values()):
    raise RuntimeError("V25_SAFETY_CONTRACT_FAILED")

print()
print("=" * 60)
print("EROS 3.0 - V2.5 DASHBOARD SNAPSHOT CONTRACT : PASS")
print("=" * 60)
