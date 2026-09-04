import sys
import os

ROOT = r"D:\Users\User\Desktop\AI_STOCK_ANALYZER"

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.eros_frontend_adapter import EROSFrontendAdapter

print("IMPORT : PASS")
print("CLASS  :", EROSFrontendAdapter.__name__)

adapter = EROSFrontendAdapter()

symbol = "RELIANCE.NS"

print("SYMBOL :", symbol)

trace = adapter.decision_traceability(symbol)

print("")
print("TRACEABILITY TYPE :", type(trace).__name__)

if isinstance(trace, dict):
    print("TRACE KEYS        :", list(trace.keys()))
    print("DECISION          :", trace.get("decision"))
    print("EVIDENCE CHAIN    :", trace.get("evidence_chain"))
    print("SCENARIO TRACE    :", trace.get("scenario_trace"))
    print("INTERPRETATION    :", trace.get("interpretation"))
    print("CONCLUSION        :", trace.get("conclusion"))

audit = adapter.decision_audit(symbol)

print("")
print("AUDIT TYPE        :", type(audit).__name__)

if isinstance(audit, dict):
    print("AUDIT KEYS        :", list(audit.keys()))
    print("DECISION          :", audit.get("decision"))
    print("EVIDENCE CHAIN    :", audit.get("evidence_chain"))
    print("SCENARIO TRACE    :", audit.get("scenario_trace"))
    print("INTERPRETATION    :", audit.get("interpretation"))
    print("CONCLUSION        :", audit.get("conclusion"))
    print("AUDIT STATUS      :", audit.get("audit_status"))
    print("GOVERNANCE        :", audit.get("governance"))

print("")
print("GOLDEN BASELINE RUNTIME COMPLETE")
