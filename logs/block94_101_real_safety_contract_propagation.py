import importlib
from pprint import pprint

print("=" * 90)
print("EROS 3.0 - BLOCK 94-101 REAL SAFETY CONTRACT PROPAGATION")
print("=" * 90)
print()
print("READ ONLY")
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print()

# ------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------

B94 = importlib.import_module(
    "services.quantitative.block94_portfolio_stress_scenario_engine"
).EROSBlock94PortfolioStressScenarioEngine

B95 = importlib.import_module(
    "services.quantitative.block95_stress_evidence_gate"
).EROSBlock95StressEvidenceGate

B96 = importlib.import_module(
    "services.quantitative.block96_stress_decision_gate"
).EROSBlock96StressDecisionGate

B97 = importlib.import_module(
    "services.quantitative.block97_stress_readiness_gate"
).EROSBlock97StressReadinessGate

B98 = importlib.import_module(
    "services.quantitative.block98_execution_governance_bridge"
).EROSBlock98ExecutionGovernanceBridge

B99 = importlib.import_module(
    "services.quantitative.block99_execution_intent_authorization_gate"
).EROSBlock99ExecutionIntentAuthorizationGate

B100 = importlib.import_module(
    "services.quantitative.block100_paper_execution_fill_gate"
).EROSBlock100PaperExecutionFillGate

B101 = importlib.import_module(
    "services.quantitative.block101_execution_evidence_reconciliation"
).EROSBlock101ExecutionEvidenceReconciliationGate

# ------------------------------------------------------------
# SYNTHETIC INPUT
# ------------------------------------------------------------

valuation = {
    "portfolio_value": 1_000_000.0,
    "cash": 400_000.0,
}

performance = {
    "return_pct": 8.5,
    "benchmark_return_pct": 6.0,
}

risk = {
    "volatility": 0.18,
    "max_drawdown": 0.12,
}

positions = [
    {
        "symbol": "RELIANCE",
        "quantity": 100,
        "price": 2500.0,
        "weight": 0.25,
    },
    {
        "symbol": "HDFCBANK",
        "quantity": 100,
        "price": 1800.0,
        "weight": 0.18,
    },
]

scenarios = [
    {
        "name": "MARKET_SHOCK",
        "shock_pct": -10.0,
    }
]

policy = {}


def show_result(label, result):

    print()
    print("=" * 90)
    print(label)
    print("=" * 90)

    print("TYPE :", type(result))

    if not isinstance(result, dict):
        print("NON-DICT RESULT")
        pprint(result, width=160, sort_dicts=False)
        return

    print()
    print("TOP LEVEL KEYS:")
    for key in result.keys():
        print("  ", key)

    safety_fields = [
        "status",
        "gate_status",
        "decision_status",
        "readiness_status",
        "governance_status",
        "intent_status",
        "execution_status",
        "reconciliation_status",
        "execution_blocked",
        "non_mutation_invariant",
        "broker_submission",
        "live_order_submission",
        "portfolio_mutation",
        "valuation_mutation",
        "performance_mutation",
        "risk_mutation",
        "optimization",
        "order_creation",
    ]

    print()
    print("SAFETY / CONTROL FIELDS:")

    for field in safety_fields:

        if field in result:
            print(f"  {field:28} = {result[field]!r}")

    print()
    print("NESTED SAFETY FIELDS:")

    found_nested = False

    for parent_key, parent_value in result.items():

        if not isinstance(parent_value, dict):
            continue

        nested_hits = []

        for field in safety_fields:

            if field in parent_value:
                nested_hits.append(f"{field}={parent_value[field]!r}")

        if nested_hits:

            found_nested = True

            print(f"  [{parent_key}]")

            for hit in nested_hits:
                print("      " + hit)

    if not found_nested:
        print("  NONE")

    print()
    print("FULL RETURN DICTIONARY:")
    pprint(result, width=160, sort_dicts=False)


# ------------------------------------------------------------
# BLOCK 94
# ------------------------------------------------------------

b94 = B94()

try:

    r94 = b94.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    show_result("BLOCK 94 - CERTIFY RETURN", r94)

except Exception as exc:

    print()
    print("BLOCK 94 ERROR")
    print(type(exc).__name__, str(exc))
    r94 = None


# ------------------------------------------------------------
# BLOCK 95
# ------------------------------------------------------------

b95 = B95()

try:

    r95 = b95.certify(
        stress_certificate=r94 if isinstance(r94, dict) else {},
        policy=policy,
    )

    show_result("BLOCK 95 - CERTIFY RETURN", r95)

except Exception as exc:

    print()
    print("BLOCK 95 ERROR")
    print(type(exc).__name__, str(exc))
    r95 = None


# ------------------------------------------------------------
# BLOCK 96
# ------------------------------------------------------------

b96 = B96()

try:

    r96 = b96.certify(
        stress_gate=r95 if isinstance(r95, dict) else {},
        policy=policy,
    )

    show_result("BLOCK 96 - CERTIFY RETURN", r96)

except Exception as exc:

    print()
    print("BLOCK 96 ERROR")
    print(type(exc).__name__, str(exc))
    r96 = None


# ------------------------------------------------------------
# BLOCK 97
# ------------------------------------------------------------

b97 = B97()

try:

    r97 = b97.certify(
        decision=r96 if isinstance(r96, dict) else {},
    )

    show_result("BLOCK 97 - CERTIFY RETURN", r97)

except Exception as exc:

    print()
    print("BLOCK 97 ERROR")
    print(type(exc).__name__, str(exc))
    r97 = None


# ------------------------------------------------------------
# BLOCK 98
# ------------------------------------------------------------

b98 = B98()

try:

    r98 = b98.certify(
        decision=r97 if isinstance(r97, dict) else {},
    )

    show_result("BLOCK 98 - CERTIFY RETURN", r98)

except Exception as exc:

    print()
    print("BLOCK 98 ERROR")
    print(type(exc).__name__, str(exc))
    r98 = None


# ------------------------------------------------------------
# BLOCK 99
# ------------------------------------------------------------

b99 = B99()

try:

    r99 = b99.certify(
        governance=r98 if isinstance(r98, dict) else {},
    )

    show_result("BLOCK 99 - CERTIFY RETURN", r99)

except Exception as exc:

    print()
    print("BLOCK 99 ERROR")
    print(type(exc).__name__, str(exc))
    r99 = None


# ------------------------------------------------------------
# BLOCK 100
# ------------------------------------------------------------

b100 = B100()

try:

    r100 = b100.certify(
        intent=r99 if isinstance(r99, dict) else {},
        fill_ratio=1.0,
    )

    show_result("BLOCK 100 - CERTIFY RETURN", r100)

except Exception as exc:

    print()
    print("BLOCK 100 ERROR")
    print(type(exc).__name__, str(exc))
    r100 = None


# ------------------------------------------------------------
# BLOCK 101
# ------------------------------------------------------------

b101 = B101()

try:

    r101 = b101.certify(
        execution=r100 if isinstance(r100, dict) else {},
    )

    show_result("BLOCK 101 - CERTIFY RETURN", r101)

except Exception as exc:

    print()
    print("BLOCK 101 ERROR")
    print(type(exc).__name__, str(exc))
    r101 = None


# ------------------------------------------------------------
# FINAL PROPAGATION MATRIX
# ------------------------------------------------------------

print()
print("=" * 90)
print("FINAL SAFETY PROPAGATION MATRIX")
print("=" * 90)

results = [
    ("94", r94),
    ("95", r95),
    ("96", r96),
    ("97", r97),
    ("98", r98),
    ("99", r99),
    ("100", r100),
    ("101", r101),
]

fields = [
    "execution_blocked",
    "non_mutation_invariant",
    "broker_submission",
    "live_order_submission",
    "portfolio_mutation",
    "valuation_mutation",
    "performance_mutation",
    "risk_mutation",
    "optimization",
    "order_creation",
]

print()

header = "BLOCK".ljust(8) + " | " + " | ".join(f.ljust(22) for f in fields)

print(header)
print("-" * len(header))

for block_id, result in results:

    values = []

    if isinstance(result, dict):

        for field in fields:

            if field in result:
                values.append(repr(result[field]).ljust(22))
            else:
                values.append("ABSENT".ljust(22))

    else:

        values = ["NO RESULT".ljust(22) for _ in fields]

    print(block_id.ljust(8) + " | " + " | ".join(values))

print()
print("=" * 90)
print("KEY QUESTION")
print("=" * 90)
print()
print("Does the safety contract survive the REAL 94 -> 101 method chain?")
print()
print("If fields are ABSENT, that identifies the exact propagation boundary.")
print("If fields survive, the earlier failure is an observability/read-model issue.")
print()
print("=" * 90)
print("TRACE COMPLETE")
print("=" * 90)
