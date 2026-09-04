import json
import sys

from services.eros_frontend_adapter import EROSFrontendAdapter

adapter = EROSFrontendAdapter()

symbol = "RELIANCE.NS"

result = adapter.decision_intelligence(symbol)

assert isinstance(result, dict)

required = [
    "symbol",
    "price",
    "decision",
    "market_context",
    "technical_drivers",
    "technical_indicators",
    "risk_flags",
    "summary",
    "governance",
]

for field in required:
    assert field in result, f"MISSING_FIELD:{field}"

decision = result["decision"]

for field in [
    "stance",
    "recommendation",
    "score",
    "score_band",
    "confidence",
    "confidence_band",
    "risk",
]:
    assert field in decision, f"MISSING_DECISION_FIELD:{field}"

governance = result["governance"]

assert governance["read_only"] is True
assert governance["execution_blocked"] is True
assert governance["non_mutation_invariant"] is True

print("DECISION INTELLIGENCE : PASS")
print("SYMBOL :", result["symbol"])
print("PRICE  :", result["price"])
print("")
print(json.dumps(result, indent=2, default=str))
