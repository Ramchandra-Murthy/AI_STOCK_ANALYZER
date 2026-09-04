import os
import sys
import traceback

ROOT = r"D:\Users\User\Desktop\AI_STOCK_ANALYZER"

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

print("=" * 70)
print("EROS 3.0 - V3.8.2.4 RUNTIME DATAFLOW DIAGNOSTIC")
print("=" * 70)

print("\nPYTHON")
print("-" * 70)
print(sys.version)
print("CWD :", os.getcwd())
print("ROOT IN PATH :", ROOT in sys.path)

try:
    from services.eros_frontend_adapter import EROSFrontendAdapter

    print("\nIMPORT")
    print("-" * 70)
    print("IMPORT : PASS")
    print("CLASS  :", EROSFrontendAdapter.__name__)

    adapter = EROSFrontendAdapter()
    symbol = "RELIANCE.NS"

    print("\n" + "=" * 70)
    print("1. DECISION TRACEABILITY")
    print("=" * 70)

    trace = adapter.decision_traceability(symbol)

    print("CALL :", "PASS")
    print("TYPE :", type(trace).__name__)

    if isinstance(trace, dict):
        print("\nTRACEABILITY TOP LEVEL")
        for k, v in trace.items():
            if isinstance(v, dict):
                print(f"{k:25} : dict ({len(v)} keys)")
            elif isinstance(v, list):
                print(f"{k:25} : list ({len(v)} items)")
            else:
                print(f"{k:25} : {type(v).__name__} = {v!r}")

        print("\nDECISION")
        print(trace.get("decision"))

        print("\nEVIDENCE CHAIN")
        print(trace.get("evidence_chain"))

        print("\nSCENARIO TRACE")
        print(trace.get("scenario_trace"))

        print("\nINTERPRETATION")
        print(trace.get("interpretation"))

        print("\nTRACE")
        print(trace.get("trace"))

        print("\nTRACEABILITY")
        print(trace.get("traceability"))

        print("\nCONCLUSION")
        print(trace.get("conclusion"))

    else:
        print("TRACEABILITY RESULT IS NOT A DICT")

    print("\n" + "=" * 70)
    print("2. DECISION AUDIT")
    print("=" * 70)

    audit = adapter.decision_audit(symbol)

    print("CALL :", "PASS")
    print("TYPE :", type(audit).__name__)

    if isinstance(audit, dict):

        print("\nAUDIT TOP LEVEL")

        for k, v in audit.items():
            if isinstance(v, dict):
                print(f"{k:25} : dict ({len(v)} keys)")
            elif isinstance(v, list):
                print(f"{k:25} : list ({len(v)} items)")
            else:
                print(f"{k:25} : {type(v).__name__} = {v!r}")

        print("\nDECISION")
        print(audit.get("decision"))

        print("\nEVIDENCE CHAIN")
        print(audit.get("evidence_chain"))

        print("\nSCENARIO TRACE")
        print(audit.get("scenario_trace"))

        print("\nINTERPRETATION")
        print(audit.get("interpretation"))

        print("\nTRACE")
        print(audit.get("trace"))

        print("\nTRACEABILITY")
        print(audit.get("traceability"))

        print("\nCONCLUSION")
        print(audit.get("conclusion"))

        print("\nAUDIT")
        print(audit.get("audit"))

        print("\nAUDIT STATUS")
        print(audit.get("audit_status"))

        print("\nGOVERNANCE")
        print(audit.get("governance"))

        print("\n" + "=" * 70)
        print("3. HYDRATION MATRIX")
        print("=" * 70)

        checks = [
            "decision",
            "audit",
            "audit_findings",
            "trace",
            "traceability",
            "evidence_chain",
            "scenario_trace",
            "interpretation",
            "conclusion",
            "traceability_status",
            "audit_summary",
            "audit_status",
            "governance",
        ]

        for key in checks:
            value = audit.get(key)

            if isinstance(value, dict):
                status = "HYDRATED" if value else "EMPTY"
            elif isinstance(value, list):
                status = "HYDRATED" if value else "EMPTY"
            elif value is None:
                status = "NONE"
            elif value == "":
                status = "EMPTY"
            else:
                status = "HYDRATED"

            print(f"{key:25} : {status}")

        print("\n" + "=" * 70)
        print("4. DECISION CONTENT")
        print("=" * 70)

        decision = audit.get("decision")

        if isinstance(decision, dict):
            for key in [
                "stance",
                "recommendation",
                "classification",
                "confidence",
                "risk",
                "decision_quality",
            ]:
                print(f"{key:25} : {decision.get(key)!r}")
        else:
            print("DECISION IS NOT A DICT")

        print("\n" + "=" * 70)
        print("5. FINAL SAFETY CONTRACT")
        print("=" * 70)

        governance = audit.get("governance", {})

        safety_keys = [
            "read_only",
            "execution_blocked",
            "non_mutation_invariant",
            "allow_order_creation",
            "allow_broker_submission",
            "allow_live_execution",
            "allow_portfolio_mutation",
            "allow_valuation_mutation",
            "allow_performance_mutation",
            "allow_risk_mutation",
            "allow_optimization",
        ]

        safety_pass = True

        for key in safety_keys:
            value = governance.get(key)
            print(f"{key:35} : {value!r}")

            if key in [
                "read_only",
                "execution_blocked",
                "non_mutation_invariant",
            ]:
                if value is not True:
                    safety_pass = False
            else:
                if value is not False:
                    safety_pass = False

        print("\nSAFETY CONTRACT :", "PASS" if safety_pass else "FAIL")

        print("\n" + "=" * 70)
        print("6. FINAL V3.8.2.4 RUNTIME STATUS")
        print("=" * 70)

        required = [
            "decision",
            "trace",
            "traceability",
            "evidence_chain",
            "scenario_trace",
            "interpretation",
            "conclusion",
        ]

        hydration_pass = True

        for key in required:
            value = audit.get(key)

            if isinstance(value, (dict, list)):
                populated = bool(value)
            else:
                populated = value not in (None, "")

            print(f"{key:25} : {'HYDRATED' if populated else 'EMPTY'}")

            if not populated:
                hydration_pass = False

        print("\nHYDRATION :", "PASS" if hydration_pass else "FAIL")
        print("SAFETY    :", "PASS" if safety_pass else "FAIL")

        if hydration_pass and safety_pass:
            print("\nV3.8.2.4 RUNTIME : PASS")
        else:
            print("\nV3.8.2.4 RUNTIME : FAIL")

    else:
        print("AUDIT RESULT IS NOT A DICT")

except Exception:
    print("\n" + "=" * 70)
    print("RUNTIME EXCEPTION")
    print("=" * 70)
    traceback.print_exc()

print("\n" + "=" * 70)
print("V3.8.2.4 RUNTIME DIAGNOSTIC COMPLETE")
print("=" * 70)
