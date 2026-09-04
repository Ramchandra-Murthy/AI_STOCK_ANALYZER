import json

from services.eros_frontend_adapter import EROSFrontendAdapter

adapter = EROSFrontendAdapter()

symbol = "RELIANCE.NS"

result = adapter.decision_interpretation(symbol)

assert isinstance(result, dict)

required = [
    "symbol",
    "price",
    "decision",
    "interpretation",
    "technical_indicators",
    "governance"
]

for field in required:
    assert field in result, f"MISSING_FIELD:{field}"

interpretation = result["interpretation"]

required_interpretation = [
    "market_condition",
    "price_context",
    "breakout_context",
    "decision_quality",
    "primary_drivers",
    "supporting_drivers",
    "conflicting_signals",
    "interpretation",
    "invalidation_context"
]

for field in required_interpretation:
    assert field in interpretation, (
        f"MISSING_INTERPRETATION_FIELD:{field}"
    )

governance = result["governance"]

assert governance["read_only"] is True
assert governance["execution_blocked"] is True
assert governance["non_mutation_invariant"] is True

print("DECISION INTERPRETATION : PASS")
print("SYMBOL :", result["symbol"])
print("PRICE  :", result["price"])
print("")
print(json.dumps(result, indent=2, default=str))
