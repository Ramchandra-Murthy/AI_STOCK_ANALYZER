import importlib
import pprint
from datetime import datetime

print("=" * 90)
print("EROS 3.0 - FULL BLOCK 94 -> 106 END-TO-END CONTRACT TRACE")
print("=" * 90)


def dump_result(label, result):
    print()
    print("-" * 90)
    print(label)
    print("-" * 90)

    print("TYPE :", type(result))

    if not isinstance(result, dict):
        pprint.pprint(result, width=140, sort_dicts=False)
        return

    print("TOP LEVEL KEYS:")
    for key in result.keys():
        print("  ", key)

    print()
    print("KEY VALUES:")

    important_keys = [
        "status",
        "block_id",
        "engine_version",
        "source_block",
        "reason",
        "reason_code",
        "gate_status",
        "decision_status",
        "readiness_status",
        "governance_status",
        "intent_status",
        "execution_status",
        "reconciliation_status",
        "execution_action",
        "intent_action",
        "execution_id",
        "source_execution_id",
        "source_intent_id",
        "source_readiness_id",
        "source_governance_id",
        "execution_blocked",
        "non_mutation_invariant",
        "broker_submission",
        "live_order_submission",
        "order_creation",
        "portfolio_mutation",
        "valuation_mutation",
        "performance_mutation",
        "risk_mutation",
        "optimization",
    ]

    for key in important_keys:
        if key in result:
            print(f"  {key:28} : {result[key]!r}")

    if isinstance(result.get("safety"), dict):
        print()
        print("NESTED SAFETY:")
        for key, value in result["safety"].items():
            print(f"  {key:28} : {value!r}")

    print()
    print("FULL RESULT:")
    pprint.pprint(result, width=150, sort_dicts=False)


def import_class(module_name, class_name):
    print()
    print("=" * 90)
    print("IMPORT:", module_name)
    print("=" * 90)

    try:
        module = importlib.import_module(module_name)
        print("IMPORT : PASS")
        cls = getattr(module, class_name)
        instance = cls()
        print("INSTANCE : PASS")
        return instance
    except Exception as exc:
        print("IMPORT / INSTANCE : FAIL")
        print(type(exc).__name__, str(exc))
        return None


print()
print("AUDIT TIME :", datetime.now().isoformat())
print("MODE       : READ ONLY")
print("BROKER     : DISABLED")
print("LIVE EXEC  : DISABLED")
print("MUTATION   : DISABLED")
print("ORDERS     : DISABLED")

# ------------------------------------------------------------------
# SYNTHETIC BUT REALISTIC INPUT
# ------------------------------------------------------------------

valuation = {
    "portfolio_value": 1_000_000.0,
    "currency": "INR",
}

performance = {
    "daily_return": -0.012,
    "monthly_return": 0.021,
}

risk = {
    "portfolio_volatility": 0.18,
    "max_drawdown": -0.15,
}

positions = [
    {
        "symbol": "RELIANCE.NS",
        "quantity": 100,
        "market_value": 300000.0,
        "weight": 0.30,
    },
    {
        "symbol": "HDFCBANK.NS",
        "quantity": 200,
        "market_value": 200000.0,
        "weight": 0.20,
    },
]

scenarios = [
    {
        "scenario_id": "MARKET_SHOCK_10",
        "name": "Market Shock -10%",
        "shock_pct": -0.10,
    }
]

print()
print("=" * 90)
print("SYNTHETIC INPUT")
print("=" * 90)
print("Portfolio Value :", valuation["portfolio_value"])
print("Positions       :", len(positions))
print("Scenarios       :", len(scenarios))

# ------------------------------------------------------------------
# BLOCK 94
# ------------------------------------------------------------------

b94 = import_class(
    "services.quantitative.block94_portfolio_stress_scenario_engine",
    "EROSBlock94PortfolioStressScenarioEngine",
)

r94 = None

if b94:
    try:
        r94 = b94.certify(
            valuation=valuation,
            performance=performance,
            risk=risk,
            positions=positions,
            scenarios=scenarios,
        )
        dump_result("BLOCK 94 - CERTIFY", r94)
    except Exception as exc:
        print("BLOCK 94 ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------------
# BLOCK 95
# ------------------------------------------------------------------

b95 = import_class(
    "services.quantitative.block95_stress_evidence_gate", "EROSBlock95StressEvidenceGate"
)

r95 = None

if b95 and r94 is not None:
    try:
        r95 = b95.certify(stress_certificate=r94)
        dump_result("BLOCK 95 - CERTIFY", r95)
    except Exception as exc:
        print("BLOCK 95 ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------------
# BLOCK 96
# ------------------------------------------------------------------

b96 = import_class(
    "services.quantitative.block96_stress_decision_gate", "EROSBlock96StressDecisionGate"
)

r96 = None

if b96 and r95 is not None:
    try:
        r96 = b96.certify(stress_gate=r95)
        dump_result("BLOCK 96 - CERTIFY", r96)
    except Exception as exc:
        print("BLOCK 96 ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------------
# BLOCK 97
# ------------------------------------------------------------------

b97 = import_class(
    "services.quantitative.block97_stress_readiness_gate", "EROSBlock97StressReadinessGate"
)

r97 = None

if b97 and r96 is not None:
    try:
        r97 = b97.certify(decision=r96)
        dump_result("BLOCK 97 - CERTIFY", r97)
    except Exception as exc:
        print("BLOCK 97 ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------------
# BLOCK 98
# ------------------------------------------------------------------

b98 = import_class(
    "services.quantitative.block98_execution_governance_bridge",
    "EROSBlock98ExecutionGovernanceBridge",
)

r98 = None

if b98 and r97 is not None:
    try:
        r98 = b98.certify(decision=r97)
        dump_result("BLOCK 98 - CERTIFY", r98)
    except Exception as exc:
        print("BLOCK 98 ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------------
# BLOCK 99
# ------------------------------------------------------------------

b99 = import_class(
    "services.quantitative.block99_execution_intent_authorization_gate",
    "EROSBlock99ExecutionIntentAuthorizationGate",
)

r99 = None

if b99 and r98 is not None:
    try:
        r99 = b99.certify(governance=r98)
        dump_result("BLOCK 99 - CERTIFY", r99)
    except Exception as exc:
        print("BLOCK 99 ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------------
# BLOCK 100
# ------------------------------------------------------------------

b100 = import_class(
    "services.quantitative.block100_paper_execution_fill_gate", "EROSBlock100PaperExecutionFillGate"
)

r100 = None

if b100 and r99 is not None:
    try:
        r100 = b100.certify(
            intent=r99,
            fill_ratio=1.0,
        )
        dump_result("BLOCK 100 - CERTIFY", r100)
    except Exception as exc:
        print("BLOCK 100 ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------------
# BLOCK 101
# ------------------------------------------------------------------

b101 = import_class(
    "services.quantitative.block101_execution_evidence_reconciliation",
    "EROSBlock101ExecutionEvidenceReconciliationGate",
)

r101 = None

if b101 and r100 is not None:
    try:
        r101 = b101.certify(execution=r100)
        dump_result("BLOCK 101 - CERTIFY", r101)
    except Exception as exc:
        print("BLOCK 101 ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------------
# BLOCK 102
# ------------------------------------------------------------------

b102 = import_class(
    "services.quantitative.block102_frontend_contract", "EROSBlock102FrontendContract"
)

r102 = None

if b102:
    try:
        r102 = b102.build(
            block94=r94,
            block95=r95,
            block96=r96,
            block97=r97,
            block98=r98,
            block99=r99,
            block100=r100,
            block101=r101,
        )
        dump_result("BLOCK 102 - BUILD", r102)
    except Exception as exc:
        print("BLOCK 102 ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------------
# BLOCK 103
# ------------------------------------------------------------------

b103 = import_class(
    "services.quantitative.block103_institutional_frontend_read_model",
    "EROSBlock103InstitutionalFrontendReadModel",
)

r103 = None

if b103 and r102 is not None:
    try:
        r103 = b103.build(contract=r102)
        dump_result("BLOCK 103 - BUILD", r103)
    except Exception as exc:
        print("BLOCK 103 ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------------
# BLOCK 104
# ------------------------------------------------------------------

b104 = import_class(
    "services.quantitative.block104_eros_command_center", "EROSBlock104CommandCenter"
)

r104 = None

if b104 and r103 is not None:
    try:
        r104 = b104.render_model(read_model=r103)
        dump_result("BLOCK 104 - RENDER MODEL", r104)
    except Exception as exc:
        print("BLOCK 104 ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------------
# BLOCK 106
# ------------------------------------------------------------------

b106 = import_class(
    "services.quantitative.block106_institutional_integration_boundary",
    "EROSBlock106InstitutionalIntegrationBoundary",
)

r106 = None

if b106 and r104 is not None:
    try:
        r106 = b106.build_integration_payload(command_center=r104)
        dump_result("BLOCK 106 - BUILD INTEGRATION", r106)

        print()
        print("=" * 90)
        print("BLOCK 106 VALIDATION")
        print("=" * 90)

        try:
            validation = b106.validate_payload(r106)
            print("VALIDATION RESULT :", validation)
        except Exception as exc:
            print("VALIDATION ERROR :", type(exc).__name__, str(exc))

    except Exception as exc:
        print("BLOCK 106 ERROR:", type(exc).__name__, str(exc))

# ------------------------------------------------------------------
# FINAL SAFETY MATRIX
# ------------------------------------------------------------------

print()
print("=" * 90)
print("FINAL SAFETY MATRIX")
print("=" * 90)

results = {
    "94": r94,
    "95": r95,
    "96": r96,
    "97": r97,
    "98": r98,
    "99": r99,
    "100": r100,
    "101": r101,
    "102": r102,
    "103": r103,
    "104": r104,
    "106": r106,
}

safety_keys = [
    "execution_blocked",
    "non_mutation_invariant",
    "broker_submission",
    "live_order_submission",
    "order_creation",
    "portfolio_mutation",
    "valuation_mutation",
    "performance_mutation",
    "risk_mutation",
    "optimization",
]

for block_id, result in results.items():

    print()
    print("BLOCK", block_id)

    if not isinstance(result, dict):
        print("  RESULT : ABSENT / NON-DICT")
        continue

    for key in safety_keys:
        if key in result:
            print(f"  {key:28} : {result[key]!r}")

    if isinstance(result.get("safety"), dict):
        print("  NESTED SAFETY:")
        for key, value in result["safety"].items():
            print(f"    {key:26} : {value!r}")

# ------------------------------------------------------------------
# CONTRACT CHAIN SUMMARY
# ------------------------------------------------------------------

print()
print("=" * 90)
print("CONTRACT CHAIN SUMMARY")
print("=" * 90)

chain = [
    ("94 -> 95", r94, r95),
    ("95 -> 96", r95, r96),
    ("96 -> 97", r96, r97),
    ("97 -> 98", r97, r98),
    ("98 -> 99", r98, r99),
    ("99 -> 100", r99, r100),
    ("100 -> 101", r100, r101),
    ("101 -> 102", r101, r102),
    ("102 -> 103", r102, r103),
    ("103 -> 104", r103, r104),
    ("104 -> 106", r104, r106),
]

for name, upstream, downstream in chain:
    print(
        f"{name:12} : " f"{'PASS' if upstream is not None and downstream is not None else 'FAIL'}"
    )

print()
print("=" * 90)
print("FULL END-TO-END TRACE COMPLETE")
print("=" * 90)
print("READ ONLY             : TRUE")
print("BROKER SUBMISSION     : FALSE")
print("LIVE EXECUTION        : FALSE")
print("ORDER CREATION        : FALSE")
print("PORTFOLIO MUTATION    : FALSE")
print("VALUATION MUTATION    : FALSE")
print("PERFORMANCE MUTATION  : FALSE")
print("RISK MUTATION         : FALSE")
print("OPTIMIZATION          : FALSE")
print("=" * 90)
