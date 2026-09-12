from pprint import pprint

print("=" * 90)
print("EROS 3.0 - BLOCK 94 -> 101 ACTUAL CERTIFY PAYLOAD TRACE")
print("=" * 90)
print()
print("READ-ONLY DIAGNOSTIC")
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print()

# ============================================================
# IMPORTS
# ============================================================

from services.quantitative.block94_portfolio_stress_scenario_engine import (
    EROSBlock94PortfolioStressScenarioEngine,
)
from services.quantitative.block95_stress_evidence_gate import (
    EROSBlock95StressEvidenceGate,
)
from services.quantitative.block96_stress_decision_gate import (
    EROSBlock96StressDecisionGate,
)
from services.quantitative.block97_stress_readiness_gate import (
    EROSBlock97StressReadinessGate,
)
from services.quantitative.block98_execution_governance_bridge import (
    EROSBlock98ExecutionGovernanceBridge,
)
from services.quantitative.block99_execution_intent_authorization_gate import (
    EROSBlock99ExecutionIntentAuthorizationGate,
)
from services.quantitative.block100_paper_execution_fill_gate import (
    EROSBlock100PaperExecutionFillGate,
)
from services.quantitative.block101_execution_evidence_reconciliation import (
    EROSBlock101ExecutionEvidenceReconciliationGate,
)

print("IMPORTS : PASS")
print()

# ============================================================
# SYNTHETIC READ-ONLY INPUT
# ============================================================

valuation = {
    "portfolio_value": 1_000_000.0,
    "valuation_status": "CERTIFIED",
}

performance = {
    "return_pct": 8.5,
    "performance_status": "CERTIFIED",
}

risk = {
    "risk_score": 25.0,
    "risk_status": "CERTIFIED",
}

positions = [
    {
        "symbol": "RELIANCE.NS",
        "quantity": 100,
        "price": 2500.0,
        "market_value": 250000.0,
    },
    {
        "symbol": "TCS.NS",
        "quantity": 100,
        "price": 3500.0,
        "market_value": 350000.0,
    },
]

scenarios = [
    {
        "scenario_id": "SYNTHETIC_MARKET_STRESS",
        "name": "Synthetic Market Stress",
        "shock_pct": -10.0,
    }
]


def print_payload(label, payload):
    print()
    print("=" * 90)
    print(label)
    print("=" * 90)

    print("TYPE :", type(payload))

    if isinstance(payload, dict):
        print("TOP LEVEL KEYS:")
        for key in payload.keys():
            print("  ", key)

        print()
        print("FULL PAYLOAD:")
        pprint(payload, width=160, sort_dicts=False)

        print()
        print("SAFETY FIELD SEARCH:")

        safety_keys = [
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
            "allow_order_creation",
            "allow_broker_submission",
            "allow_live_execution",
            "allow_portfolio_mutation",
            "allow_valuation_mutation",
            "allow_performance_mutation",
            "allow_risk_mutation",
            "allow_optimization",
        ]

        found = False

        for key in safety_keys:
            if key in payload:
                found = True
                print(f"  {key:32} : {payload[key]!r}")

        if isinstance(payload.get("safety"), dict):
            found = True
            print()
            print("NESTED SAFETY:")
            pprint(payload["safety"], width=140, sort_dicts=False)

        if not found:
            print("  NO EXPECTED SAFETY FIELDS AT TOP LEVEL")

    else:
        pprint(payload, width=160, sort_dicts=False)


# ============================================================
# BLOCK 94
# ============================================================

print()
print("=" * 90)
print("BLOCK 94 - PORTFOLIO STRESS SCENARIO ENGINE")
print("=" * 90)

b94 = EROSBlock94PortfolioStressScenarioEngine()

try:
    out94 = b94.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    print_payload("BLOCK 94 CERTIFY OUTPUT", out94)

except Exception as exc:
    out94 = None
    print("BLOCK 94 : ERROR")
    print(type(exc).__name__, str(exc))


# ============================================================
# BLOCK 95
# ============================================================

if out94 is not None:

    b95 = EROSBlock95StressEvidenceGate()

    try:
        out95 = b95.certify(stress_certificate=out94)

        print_payload("BLOCK 95 CERTIFY OUTPUT", out95)

    except Exception as exc:
        out95 = None
        print("BLOCK 95 : ERROR")
        print(type(exc).__name__, str(exc))

else:
    out95 = None
    print("BLOCK 95 : SKIPPED")


# ============================================================
# BLOCK 96
# ============================================================

if out95 is not None:

    b96 = EROSBlock96StressDecisionGate()

    try:
        out96 = b96.certify(stress_gate=out95)

        print_payload("BLOCK 96 CERTIFY OUTPUT", out96)

    except Exception as exc:
        out96 = None
        print("BLOCK 96 : ERROR")
        print(type(exc).__name__, str(exc))

else:
    out96 = None
    print("BLOCK 96 : SKIPPED")


# ============================================================
# BLOCK 97
# ============================================================

if out96 is not None:

    b97 = EROSBlock97StressReadinessGate()

    try:
        out97 = b97.certify(decision=out96)

        print_payload("BLOCK 97 CERTIFY OUTPUT", out97)

    except Exception as exc:
        out97 = None
        print("BLOCK 97 : ERROR")
        print(type(exc).__name__, str(exc))

else:
    out97 = None
    print("BLOCK 97 : SKIPPED")


# ============================================================
# BLOCK 98
# ============================================================

if out97 is not None:

    b98 = EROSBlock98ExecutionGovernanceBridge()

    try:
        out98 = b98.certify(decision=out97)

        print_payload("BLOCK 98 CERTIFY OUTPUT", out98)

    except Exception as exc:
        out98 = None
        print("BLOCK 98 : ERROR")
        print(type(exc).__name__, str(exc))

else:
    out98 = None
    print("BLOCK 98 : SKIPPED")


# ============================================================
# BLOCK 99
# ============================================================

if out98 is not None:

    b99 = EROSBlock99ExecutionIntentAuthorizationGate()

    try:
        out99 = b99.certify(governance=out98)

        print_payload("BLOCK 99 CERTIFY OUTPUT", out99)

    except Exception as exc:
        out99 = None
        print("BLOCK 99 : ERROR")
        print(type(exc).__name__, str(exc))

else:
    out99 = None
    print("BLOCK 99 : SKIPPED")


# ============================================================
# BLOCK 100
# ============================================================

if out99 is not None:

    b100 = EROSBlock100PaperExecutionFillGate()

    try:
        out100 = b100.certify(
            intent=out99,
            fill_ratio=1.0,
        )

        print_payload("BLOCK 100 CERTIFY OUTPUT", out100)

    except Exception as exc:
        out100 = None
        print("BLOCK 100 : ERROR")
        print(type(exc).__name__, str(exc))

else:
    out100 = None
    print("BLOCK 100 : SKIPPED")


# ============================================================
# BLOCK 101
# ============================================================

if out100 is not None:

    b101 = EROSBlock101ExecutionEvidenceReconciliationGate()

    try:
        out101 = b101.certify(execution=out100)

        print_payload("BLOCK 101 CERTIFY OUTPUT", out101)

    except Exception as exc:
        out101 = None
        print("BLOCK 101 : ERROR")
        print(type(exc).__name__, str(exc))

else:
    out101 = None
    print("BLOCK 101 : SKIPPED")


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 90)
print("FINAL 94 -> 101 TRACE SUMMARY")
print("=" * 90)

outputs = [
    ("BLOCK 94", out94),
    ("BLOCK 95", out95),
    ("BLOCK 96", out96),
    ("BLOCK 97", out97),
    ("BLOCK 98", out98),
    ("BLOCK 99", out99),
    ("BLOCK 100", out100),
    ("BLOCK 101", out101),
]

for name, payload in outputs:
    if payload is None:
        print(f"{name:12} : NO OUTPUT")
        continue

    if isinstance(payload, dict):
        print(f"{name:12} : status={payload.get('status', '<ABSENT>')!r}")
    else:
        print(f"{name:12} : type={type(payload)}")

print()
print("=" * 90)
print("TRACE COMPLETE")
print("=" * 90)
print("NO SOURCE CHANGES")
print("NO BROKER")
print("NO LIVE EXECUTION")
print("NO ORDER CREATION")
print("NO MUTATION")
print("=" * 90)
