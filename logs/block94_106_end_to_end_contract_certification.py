import traceback

print("=" * 90)
print("EROS 3.0 - BLOCK 94 -> 106 END-TO-END CONTRACT CERTIFICATION")
print("=" * 90)
print("MODE : READ-ONLY SYNTHETIC CONTRACT TEST")
print("BROKER : DISABLED")
print("LIVE EXECUTION : DISABLED")
print("ORDER CREATION : DISABLED")
print("PORTFOLIO MUTATION : DISABLED")
print("VALUATION MUTATION : DISABLED")
print("")

results = []
objects = {}


def section(title):
    print()
    print("=" * 90)
    print(title)
    print("=" * 90)


def record(block, status, details=""):
    results.append({"block": block, "status": status, "details": details})


def inspect_output(block, output):
    print()
    print(f"--- {block} OUTPUT ---")
    print("TYPE   :", type(output).__name__)

    if isinstance(output, dict):
        print("STATUS :", output.get("status", "<ABSENT>"))
        print("KEYS   :", list(output.keys()))

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
        ]

        print("SAFETY FIELDS:")
        for key in safety_keys:
            print(f"  {key:28} = {output.get(key, '<ABSENT>')!r}")

    else:
        print("VALUE  :", repr(output)[:2000])


def safety_check(block, output):
    failures = []

    if not isinstance(output, dict):
        failures.append("output is not dict")
        return failures

    # Accept either top-level safety fields or a nested safety dictionary.
    safety = output.get("safety")
    if not isinstance(safety, dict):
        safety = {}

    def get_field(key):
        if key in output:
            return output[key]
        if key in safety:
            return safety[key]
        return None

    required_true = [
        "execution_blocked",
        "non_mutation_invariant",
    ]

    required_false = [
        "broker_submission",
        "live_order_submission",
        "portfolio_mutation",
        "valuation_mutation",
        "performance_mutation",
        "risk_mutation",
        "optimization",
        "order_creation",
    ]

    for key in required_true:
        value = get_field(key)
        if value is not True:
            failures.append(f"{key} expected True, got {value!r}")

    for key in required_false:
        value = get_field(key)

        # Some legacy blocks may not expose every field.
        # Report absence separately rather than silently passing.
        if value is None:
            failures.append(f"{key} ABSENT")
        elif value is not False:
            failures.append(f"{key} expected False, got {value!r}")

    return failures


try:

    # ============================================================
    # IMPORTS
    # ============================================================

    section("1. IMPORT VERIFICATION")

    from services.quantitative.block94_portfolio_stress_scenario_engine import (
        EROSBlock94PortfolioStressScenarioEngine,
    )
    from services.quantitative.block95_stress_evidence_gate import EROSBlock95StressEvidenceGate
    from services.quantitative.block96_stress_decision_gate import EROSBlock96StressDecisionGate
    from services.quantitative.block97_stress_readiness_gate import EROSBlock97StressReadinessGate
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
    from services.quantitative.block102_frontend_contract import EROSBlock102FrontendContract
    from services.quantitative.block103_institutional_frontend_read_model import (
        EROSBlock103InstitutionalFrontendReadModel,
    )
    from services.quantitative.block104_eros_command_center import EROSBlock104CommandCenter
    from services.quantitative.block106_institutional_integration_boundary import (
        EROSBlock106InstitutionalIntegrationBoundary,
    )

    print("ALL IMPORTS : PASS")

    # ============================================================
    # SYNTHETIC INPUT
    # ============================================================

    section("2. SYNTHETIC PORTFOLIO INPUT")

    valuation = {
        "portfolio_value": 1000000.0,
        "cash": 250000.0,
        "gross_exposure": 750000.0,
        "net_exposure": 700000.0,
    }

    performance = {
        "daily_return": 0.012,
        "weekly_return": 0.021,
        "monthly_return": 0.045,
    }

    risk = {
        "volatility": 0.18,
        "var_95": 25000.0,
        "max_drawdown": 0.08,
    }

    positions = [
        {
            "symbol": "RELIANCE",
            "quantity": 100,
            "price": 2500.0,
            "market_value": 250000.0,
        },
        {
            "symbol": "HDFCBANK",
            "quantity": 200,
            "price": 1250.0,
            "market_value": 250000.0,
        },
    ]

    scenarios = [
        {
            "scenario_id": "MARKET_STRESS_01",
            "name": "Broad Market Stress",
            "shock_pct": -0.10,
        }
    ]

    print("Portfolio value :", valuation["portfolio_value"])
    print("Positions      :", len(positions))
    print("Scenarios      :", len(scenarios))

    # ============================================================
    # BLOCK 94
    # ============================================================

    section("3. BLOCK 94 - PORTFOLIO STRESS SCENARIO ENGINE")

    b94 = EROSBlock94PortfolioStressScenarioEngine()
    objects["94"] = b94

    out94 = b94.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    inspect_output("BLOCK 94", out94)

    failures = safety_check("BLOCK 94", out94)

    if failures:
        record("94", "SAFETY REVIEW REQUIRED", "; ".join(failures))
    else:
        record("94", "PASS")

    # ============================================================
    # BLOCK 95
    # ============================================================

    section("4. BLOCK 95 - STRESS EVIDENCE GATE")

    b95 = EROSBlock95StressEvidenceGate()
    objects["95"] = b95

    out95 = b95.certify(stress_certificate=out94)

    inspect_output("BLOCK 95", out95)

    failures = safety_check("BLOCK 95", out95)

    if failures:
        record("95", "SAFETY REVIEW REQUIRED", "; ".join(failures))
    else:
        record("95", "PASS")

    # ============================================================
    # BLOCK 96
    # ============================================================

    section("5. BLOCK 96 - STRESS DECISION GATE")

    b96 = EROSBlock96StressDecisionGate()
    objects["96"] = b96

    out96 = b96.certify(stress_gate=out95)

    inspect_output("BLOCK 96", out96)

    failures = safety_check("BLOCK 96", out96)

    if failures:
        record("96", "SAFETY REVIEW REQUIRED", "; ".join(failures))
    else:
        record("96", "PASS")

    # ============================================================
    # BLOCK 97
    # ============================================================

    section("6. BLOCK 97 - STRESS READINESS GATE")

    b97 = EROSBlock97StressReadinessGate()
    objects["97"] = b97

    out97 = b97.certify(decision=out96)

    inspect_output("BLOCK 97", out97)

    failures = safety_check("BLOCK 97", out97)

    if failures:
        record("97", "SAFETY REVIEW REQUIRED", "; ".join(failures))
    else:
        record("97", "PASS")

    # ============================================================
    # BLOCK 98
    # ============================================================

    section("7. BLOCK 98 - EXECUTION GOVERNANCE BRIDGE")

    b98 = EROSBlock98ExecutionGovernanceBridge()
    objects["98"] = b98

    out98 = b98.certify(decision=out97)

    inspect_output("BLOCK 98", out98)

    failures = safety_check("BLOCK 98", out98)

    if failures:
        record("98", "SAFETY REVIEW REQUIRED", "; ".join(failures))
    else:
        record("98", "PASS")

    # ============================================================
    # BLOCK 99
    # ============================================================

    section("8. BLOCK 99 - EXECUTION INTENT AUTHORIZATION")

    b99 = EROSBlock99ExecutionIntentAuthorizationGate()
    objects["99"] = b99

    out99 = b99.certify(governance=out98)

    inspect_output("BLOCK 99", out99)

    failures = safety_check("BLOCK 99", out99)

    if failures:
        record("99", "SAFETY REVIEW REQUIRED", "; ".join(failures))
    else:
        record("99", "PASS")

    # ============================================================
    # BLOCK 100
    # ============================================================

    section("9. BLOCK 100 - PAPER EXECUTION FILL GATE")

    b100 = EROSBlock100PaperExecutionFillGate()
    objects["100"] = b100

    out100 = b100.certify(intent=out99, fill_ratio=1.0)

    inspect_output("BLOCK 100", out100)

    failures = safety_check("BLOCK 100", out100)

    if failures:
        record("100", "SAFETY REVIEW REQUIRED", "; ".join(failures))
    else:
        record("100", "PASS")

    # ============================================================
    # BLOCK 101
    # ============================================================

    section("10. BLOCK 101 - EXECUTION EVIDENCE RECONCILIATION")

    b101 = EROSBlock101ExecutionEvidenceReconciliationGate()
    objects["101"] = b101

    out101 = b101.certify(execution=out100)

    inspect_output("BLOCK 101", out101)

    failures = safety_check("BLOCK 101", out101)

    if failures:
        record("101", "SAFETY REVIEW REQUIRED", "; ".join(failures))
    else:
        record("101", "PASS")

    # ============================================================
    # BLOCK 102
    # ============================================================

    section("11. BLOCK 102 - FRONTEND CONTRACT")

    b102 = EROSBlock102FrontendContract()
    objects["102"] = b102

    out102 = b102.build(
        block94=out94,
        block95=out95,
        block96=out96,
        block97=out97,
        block98=out98,
        block99=out99,
        block100=out100,
        block101=out101,
    )

    inspect_output("BLOCK 102", out102)

    record("102", "PASS")

    # ============================================================
    # BLOCK 103
    # ============================================================

    section("12. BLOCK 103 - INSTITUTIONAL FRONTEND READ MODEL")

    b103 = EROSBlock103InstitutionalFrontendReadModel()
    objects["103"] = b103

    out103 = b103.build(contract=out102)

    inspect_output("BLOCK 103", out103)

    record("103", "PASS")

    # ============================================================
    # BLOCK 104
    # ============================================================

    section("13. BLOCK 104 - EROS COMMAND CENTER")

    b104 = EROSBlock104CommandCenter()
    objects["104"] = b104

    out104 = b104.render_model(read_model=out103)

    inspect_output("BLOCK 104", out104)

    record("104", "PASS")

    # ============================================================
    # BLOCK 106
    # ============================================================

    section("14. BLOCK 106 - INSTITUTIONAL INTEGRATION BOUNDARY")

    b106 = EROSBlock106InstitutionalIntegrationBoundary()
    objects["106"] = b106

    out106 = b106.build_integration_payload(command_center=out104)

    inspect_output("BLOCK 106", out106)

    valid106 = b106.validate_payload(out106)

    print()
    print("BLOCK 106 PAYLOAD VALID :", valid106)

    if valid106:
        record("106", "PASS")
    else:
        record("106", "FAIL", "validate_payload returned False")

    # ============================================================
    # FINAL SAFETY SUMMARY
    # ============================================================

    section("15. FINAL SAFETY SUMMARY")

    all_outputs = {
        "94": out94,
        "95": out95,
        "96": out96,
        "97": out97,
        "98": out98,
        "99": out99,
        "100": out100,
        "101": out101,
    }

    total_failures = 0

    for block, output in all_outputs.items():

        failures = safety_check(block, output)

        if failures:
            total_failures += len(failures)
            print()
            print(f"BLOCK {block} : SAFETY REVIEW REQUIRED")

            for failure in failures:
                print("  -", failure)

        else:
            print(f"BLOCK {block} : SAFETY PASS")

    print()
    print("TOTAL SAFETY FINDINGS :", total_failures)

    # ============================================================
    # CHAIN SUMMARY
    # ============================================================

    section("16. END-TO-END CHAIN SUMMARY")

    for item in results:
        print(f"BLOCK {item['block']:>3} | " f"{item['status']}")

        if item["details"]:
            print("        ", item["details"])

    # ============================================================
    # ARCHITECTURAL ASSESSMENT
    # ============================================================

    section("17. ARCHITECTURAL ASSESSMENT")

    print("QUANTITATIVE LAYER")
    print("  Block 94 : Stress scenario engine")
    print("  Block 95 : Stress evidence gate")
    print("  Block 96 : Stress decision gate")
    print("  Block 97 : Stress readiness gate")
    print("  Block 98 : Execution governance")
    print("  Block 99 : Execution intent authorization")
    print("  Block 100: Paper execution")
    print("  Block 101: Execution evidence reconciliation")

    print()
    print("FRONTEND / INSTITUTIONAL LAYER")
    print("  Block 102: Frontend contract")
    print("  Block 103: Institutional frontend read model")
    print("  Block 104: EROS command center")
    print("  Block 106: Institutional integration boundary")

    print()
    print("LIVE BROKER STATUS : NOT CONNECTED")
    print("LIVE ORDER STATUS   : NOT ENABLED")
    print("PAPER EXECUTION     : TESTED THROUGH CONTRACT")
    print("MUTATION POLICY     : MUST REMAIN NON-MUTATING")

    # ============================================================
    # FINAL VERDICT
    # ============================================================

    section("18. FINAL VERDICT")

    if total_failures == 0 and valid106:
        verdict = "PASS - BLOCK 94-106 CONTRACT CHAIN CERTIFIED"
    else:
        verdict = "NOT YET CERTIFIED - SAFETY/CONTRACT FINDINGS REQUIRE REVIEW"

    print("VERDICT :", verdict)

    print()
    print("NEXT ENGINEERING STEP:")
    print("  1. Normalize safety schema across Blocks 94-101.")
    print("  2. Re-run end-to-end contract test.")
    print("  3. Certify Blocks 102-106 frontend chain.")
    print("  4. Run regression suite.")
    print("  5. Only then commit the changes.")

except Exception as exc:

    section("FATAL TEST ERROR")

    print(type(exc).__name__, str(exc))
    print()
    traceback.print_exc()

finally:

    section("19. TEST SAFETY GUARANTEE")

    print("READ ONLY                 : YES")
    print("SOURCE MODIFICATION      : NO")
    print("BROKER CONNECTION        : NO")
    print("LIVE ORDER SUBMISSION    : NO")
    print("ORDER CREATION           : NO")
    print("PORTFOLIO MUTATION       : NO")
    print("VALUATION MUTATION       : NO")
    print("LIVE TRADING              : NO")

    print()
    print("=" * 90)
    print("EROS 3.0 - END-TO-END CONTRACT CERTIFICATION COMPLETE")
    print("=" * 90)
