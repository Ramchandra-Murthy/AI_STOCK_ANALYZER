import json

from services.eros_frontend_adapter import EROSFrontendAdapter

adapter = EROSFrontendAdapter()

print("")
print("============================================================")
print("EROS 3.0 - V3.5 SCENARIO EXPLANATION ENGINE - RUNTIME")
print("============================================================")

print("")
print("1. ADAPTER IMPORT")
print("------------------------------------------------------------")
print("IMPORT : PASS")
print("CLASS  :", adapter.__class__.__name__)

print("")
print("2. V3.4 API")
print("------------------------------------------------------------")
print("decision_scenario_engine :", hasattr(adapter, "decision_scenario_engine"))

print("")
print("3. V3.5 API")
print("------------------------------------------------------------")
print("decision_scenario_explanation :", hasattr(adapter, "decision_scenario_explanation"))

result = adapter.decision_scenario_explanation("RELIANCE.NS")

print("")
print("4. V3.5 SCENARIO EXPLANATION")
print("------------------------------------------------------------")
print("SCENARIO EXPLANATION : PASS")
print("SYMBOL :", result.get("symbol"))
print("PRICE  :", result.get("price"))

print("")
print(json.dumps(result, indent=2, default=str))

print("")
print("5. REQUIRED STRUCTURE")
print("------------------------------------------------------------")

required = [
    "symbol",
    "price",
    "current_decision",
    "primary_scenario",
    "scenario_explanation",
    "decision_quality",
    "interpretation",
    "confirmation_logic",
    "invalidation_logic",
    "summary",
    "governance",
]

for field in required:
    status = "PASS" if field in result else "FAIL"
    print(f"{field:30} : {status}")

    if status == "FAIL":
        raise RuntimeError("MISSING_FIELD_" + field)

print("")
print("6. SCENARIO STRUCTURE")
print("------------------------------------------------------------")

for scenario in ["base", "bull", "bear"]:
    status = "PASS" if scenario in result["scenario_explanation"] else "FAIL"

    print(f"{scenario.upper():30} : {status}")

    if status == "FAIL":
        raise RuntimeError("MISSING_SCENARIO_" + scenario)

print("")
print("7. SAFETY CONTRACT")
print("------------------------------------------------------------")

expected_false = [
    "allow_order_creation",
    "allow_broker_submission",
    "allow_live_execution",
    "allow_portfolio_mutation",
    "allow_valuation_mutation",
    "allow_performance_mutation",
    "allow_risk_mutation",
    "allow_optimization",
]

governance = result["governance"]

if governance.get("read_only") is True:
    print("read_only                       : PASS")
else:
    print("read_only                       : FAIL")
    raise RuntimeError("READ_ONLY_SAFETY_FAILURE")

if governance.get("execution_blocked") is True:
    print("execution_blocked               : PASS")
else:
    print("execution_blocked               : FAIL")
    raise RuntimeError("EXECUTION_SAFETY_FAILURE")

if governance.get("non_mutation_invariant") is True:
    print("non_mutation_invariant          : PASS")
else:
    print("non_mutation_invariant          : FAIL")
    raise RuntimeError("NON_MUTATION_SAFETY_FAILURE")

for field in expected_false:
    value = governance.get(field)

    if value is False:
        print(f"{field:32} : PASS")
    else:
        print(f"{field:32} : FAIL")
        raise RuntimeError("SAFETY_FIELD_FAILURE_" + field)

print("")
print("============================================================")
print("EROS 3.0 - V3.5 SCENARIO EXPLANATION ENGINE")
print("============================================================")

print("")
print("SCENARIO EXPLANATION : PASS")
print("BASE SCENARIO         : PASS")
print("BULL SCENARIO         : PASS")
print("BEAR SCENARIO         : PASS")
print("SAFETY CONTRACT       : PASS")
print("READ_ONLY             : TRUE")
print("EXECUTION_BLOCKED     : TRUE")
print("NON_MUTATION_INVARIANT: TRUE")

print("")
print("FINAL RESULT : PASS")
print("V3.5 SCENARIO EXPLANATION : CLEARED")
print("============================================================")
