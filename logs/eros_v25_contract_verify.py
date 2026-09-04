import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.eros_frontend_adapter import EROSFrontendAdapter

print("============================================================")
print("EROS 3.0 - FRONTEND V2.5 ADAPTER CONTRACT VERIFICATION")
print("============================================================")

adapter = EROSFrontendAdapter()

print("")
print("1. ADAPTER INSTANCE")
print("ADAPTER INSTANCE :", type(adapter).__name__)

snapshot = adapter.snapshot()
governance = adapter.governance()
dashboard = adapter.dashboard()

print("")
print("2. SNAPSHOT")
print("SNAPSHOT : PASS")
print(snapshot)

print("")
print("3. GOVERNANCE")
print("GOVERNANCE : PASS")
print(governance)

print("")
print("4. DASHBOARD")
print("DASHBOARD : PASS")
print(dashboard)

print("")
print("5. SAFETY CONTRACT")

safety = governance["safety"]

checks = {
    "Read Only": safety["read_only"] is True,
    "Order Creation": safety["allow_order_creation"] is False,
    "Broker Submission": safety["allow_broker_submission"] is False,
    "Live Execution": safety["allow_live_execution"] is False,
    "Portfolio Mutation": safety["allow_portfolio_mutation"] is False,
    "Valuation Mutation": safety["allow_valuation_mutation"] is False,
    "Performance Mutation": safety["allow_performance_mutation"] is False,
    "Risk Mutation": safety["allow_risk_mutation"] is False,
    "Optimization": safety["allow_optimization"] is False,
    "Execution Blocked": safety["execution_blocked"] is True,
    "Non-Mutation Invariant": safety["non_mutation_invariant"] is True,
}

failed = []

for name, result in checks.items():
    print(f"{name:32} : {'PASS' if result else 'FAIL'}")
    if not result:
        failed.append(name)

print("")

if failed:
    print("ADAPTER CONTRACT : FAIL")
    print("FAILED CHECKS :", ", ".join(failed))
    raise SystemExit(1)

print("ADAPTER CONTRACT : PASS")
print("")
print("READ ONLY")
print("NO ORDER CREATION")
print("NO BROKER SUBMISSION")
print("NO LIVE EXECUTION")
print("NO PORTFOLIO MUTATION")
print("NO VALUATION MUTATION")
print("NO PERFORMANCE MUTATION")
print("NO RISK MUTATION")
print("NO OPTIMIZATION")
print("EXECUTION BLOCKED")
print("NON-MUTATION INVARIANT")

print("")
print("============================================================")
print("EROS 3.0 - V2.5 ADAPTER CONTRACT : PASS")
print("============================================================")
