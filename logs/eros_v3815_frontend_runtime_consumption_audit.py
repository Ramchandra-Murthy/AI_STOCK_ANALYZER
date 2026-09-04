from services.eros_frontend_adapter import EROSFrontendAdapter

print("======================================================================")
print("EROS 3.0 - V3.8.15 FRONTEND RUNTIME CONSUMPTION AUDIT")
print("======================================================================")
print("")

adapter = EROSFrontendAdapter()
symbol = "RELIANCE.NS"

print("SYMBOL :", symbol)
print("")

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

print("======================================================================")
print("EROS DECISION API RUNTIME CHECK")
print("======================================================================")

for method_name in methods:

    print("")
    print("METHOD :", method_name)

    method = getattr(adapter, method_name, None)

    if method is None:
        print("STATUS : NOT AVAILABLE")
        continue

    print("STATUS : AVAILABLE")

    try:

        result = method(symbol)

        print("RESULT TYPE :", type(result).__name__)

        if isinstance(result, dict):

            print("TOP LEVEL KEYS :")

            for key in result.keys():
                print("  ", repr(key))

            if method_name == "decision_traceability":

                print("")
                print("DECISION:")
                print(result.get("decision"))

                print("")
                print("TRACE:")
                print(result.get("trace"))

                print("")
                print("TRACEABILITY STATUS:")
                print(result.get("traceability_status"))

                print("")
                print("GOVERNANCE:")
                print(result.get("governance"))

        else:
            print("RESULT :", result)

    except Exception as exc:

        print("RUNTIME ERROR :", type(exc).__name__)
        print("MESSAGE :", str(exc))

print("")
print("======================================================================")
print("SAFETY")
print("======================================================================")
print("NO SOURCE PATCH")
print("NO DATABASE WRITE")
print("NO BROKER CALL")
print("NO ORDER CREATION")
print("NO PORTFOLIO MUTATION")
print("NO GIT OPERATION")
print("")
print("V3.8.15 RUNTIME CONSUMPTION AUDIT COMPLETE")
print("======================================================================")
