from services.eros_frontend_adapter import EROSFrontendAdapter

print("=" * 70)
print("EROS 3.0 - V3.8.13 TRACEABILITY RUNTIME CONTRACT")
print("=" * 70)

adapter = EROSFrontendAdapter()

symbol = "RELIANCE.NS"

print()
print("SYMBOL :", symbol)
print()

result = adapter.decision_traceability(symbol)

print("RESULT TYPE :", type(result).__name__)

if not isinstance(result, dict):
    raise RuntimeError("TRACEABILITY_RESULT_NOT_DICT")

print()
print("TOP LEVEL KEYS")
print("-" * 70)

for key in result.keys():
    print(repr(key))

print()
print("DECISION")
print("-" * 70)

decision = result.get("decision", {})
print("TYPE :", type(decision).__name__)

if isinstance(decision, dict):
    for key, value in decision.items():
        print(f"{key!r} : {value!r}")

print()
print("TRACE")
print("-" * 70)

trace = result.get("trace", {})
print("TYPE :", type(trace).__name__)

if isinstance(trace, dict):
    for stage, value in trace.items():
        print()
        print("STAGE :", stage)
        print("TYPE  :", type(value).__name__)

        if isinstance(value, dict):
            for key, item in value.items():
                print(f"  {key!r} : {item!r}")
        else:
            print("  VALUE :", repr(value))

print()
print("GOVERNANCE")
print("-" * 70)

governance = result.get("governance", {})
print("TYPE :", type(governance).__name__)

if isinstance(governance, dict):
    for key, value in governance.items():
        print(f"{key!r} : {value!r}")

print()
print("=" * 70)
print("SAFETY")
print("=" * 70)
print("READ ONLY")
print("NO DATABASE WRITE")
print("NO BROKER CALL")
print("NO ORDER CREATION")
print("NO PORTFOLIO MUTATION")
print("NO SOURCE PATCH")
print("=" * 70)
