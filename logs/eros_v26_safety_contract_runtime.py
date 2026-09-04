import os
import sys

os.environ["PYTHONPATH"] = os.getcwd()

from services.eros_frontend_adapter import EROSFrontendAdapter

adapter = EROSFrontendAdapter()

safety = adapter.governance()["safety"]

checks = {
    "read_only": safety.get("read_only") is True,
    "allow_order_creation": safety.get("allow_order_creation") is False,
    "allow_broker_submission": safety.get("allow_broker_submission") is False,
    "allow_live_execution": safety.get("allow_live_execution") is False,
    "allow_portfolio_mutation": safety.get("allow_portfolio_mutation") is False,
    "allow_valuation_mutation": safety.get("allow_valuation_mutation") is False,
    "allow_performance_mutation": safety.get("allow_performance_mutation") is False,
    "allow_risk_mutation": safety.get("allow_risk_mutation") is False,
    "allow_optimization": safety.get("allow_optimization") is False,
    "execution_blocked": safety.get("execution_blocked") is True,
    "non_mutation_invariant": safety.get("non_mutation_invariant") is True,
}

failed = False

for key, value in checks.items():

    if value:
        print(f"{key:32} : PASS")
    else:
        print(f"{key:32} : FAIL")
        failed = True

if failed:
    sys.exit(1)

print("")
print("SAFETY CONTRACT : PASS")
