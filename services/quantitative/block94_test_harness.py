"""
EROS 3.0 - Block 94 Self-Test Harness

The harness intentionally tests the architectural contract, not only the
arithmetic. It verifies:
    * certified upstream evidence is accepted
    * blocked evidence is rejected
    * malformed evidence is rejected
    * missing lineage is rejected
    * invalid scenarios are rejected
    * duplicate scenarios are controlled
    * price / market / volatility / benchmark / sector / liquidity /
      correlation shocks work
    * downside / upside / combined scenarios work
    * scenario contribution is generated
    * input objects are not mutated
    * certificate history is isolated
    * execution semantics are forbidden
    * deterministic certificate generation works
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List

from .block94_portfolio_stress_scenario_engine import (
    EROSBlock94PortfolioStressScenarioEngine,
    STATUS_BLOCKED,
    STATUS_CERTIFIED,
    STATUS_DUPLICATE,
    STATUS_PASS,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _base_valuation() -> Dict[str, Any]:
    return {
        "status": "CERTIFIED",
        "valuation_id": "EROS91-VAL-001",
        "portfolio_equity": 10_000_000.0,
        "market_value": 10_000_000.0,
    }


def _base_performance() -> Dict[str, Any]:
    return {
        "status": "CERTIFIED",
        "performance_id": "EROS92-PERF-001",
        "valuation_id": "EROS91-VAL-001",
        "return_pct": 4.0,
    }


def _base_risk() -> Dict[str, Any]:
    return {
        "status": "CERTIFIED",
        "certificate_id": "EROS93-RISK-001",
        "performance_id": "EROS92-PERF-001",
        "volatility": 0.0108,
        "maximum_drawdown": 0.00495,
        "beta": 1.2,
        "sharpe_ratio": 0.92,
    }


def _base_positions() -> List[Dict[str, Any]]:
    return [
        {
            "symbol": "ALPHA",
            "quantity": 4000,
            "price": 1000,
            "market_value": 4_000_000,
            "sector": "BANKING",
            "beta": 1.25,
            "volatility": 0.20,
            "liquidity_factor": 0.90,
            "benchmark": "NIFTY50",
        },
        {
            "symbol": "BETA",
            "quantity": 3000,
            "price": 1000,
            "market_value": 3_000_000,
            "sector": "IT",
            "beta": 1.10,
            "volatility": 0.18,
            "liquidity_factor": 0.80,
            "benchmark": "NIFTY50",
        },
        {
            "symbol": "GAMMA",
            "quantity": 3000,
            "price": 1000,
            "market_value": 3_000_000,
            "sector": "ENERGY",
            "beta": 0.95,
            "volatility": 0.15,
            "liquidity_factor": 0.95,
            "benchmark": "NIFTY50",
        },
    ]


def _scenario(
    scenario_id: str,
    scenario_type: str,
    name: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    payload = {
        "scenario_id": scenario_id,
        "scenario_type": scenario_type,
        "name": name,
    }
    payload.update(kwargs)
    return payload


def run_block94_self_test() -> Dict[str, Any]:
    valuation = _base_valuation()
    performance = _base_performance()
    risk = _base_risk()
    positions = _base_positions()

    engine = EROSBlock94PortfolioStressScenarioEngine()

    tests_run = 0
    tests_passed = 0

    def check(condition: bool, message: str) -> None:
        nonlocal tests_run, tests_passed
        tests_run += 1
        _assert(condition, message)
        tests_passed += 1

    # --------------------------------------------------------
    # 1. Certified baseline
    # --------------------------------------------------------

    baseline_scenario = _scenario(
        "SCN-001",
        "PRICE",
        "Base Price Shock",
        price_shock_pct=-10.0,
    )

    result = engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=baseline_scenario,
    )

    check(
        result["status"] == STATUS_PASS,
        "certified baseline scenario should pass",
    )

    # --------------------------------------------------------
    # 2. Blocked valuation
    # --------------------------------------------------------

    blocked_valuation = copy.deepcopy(valuation)
    blocked_valuation["status"] = "BLOCKED"

    result = engine.run_scenario(
        valuation=blocked_valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=baseline_scenario,
    )

    check(
        result["status"] == STATUS_PASS,
        "run_scenario is analytical and should calculate with structurally valid inputs",
    )

    blocked_cert = engine.certify(
        valuation=blocked_valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=[baseline_scenario],
    )

    check(
        blocked_cert["status"] == STATUS_BLOCKED,
        "blocked valuation must block certification",
    )

    # --------------------------------------------------------
    # 3. Missing valuation lineage
    # --------------------------------------------------------

    missing_lineage = copy.deepcopy(valuation)
    del missing_lineage["valuation_id"]

    result = engine.certify(
        valuation=missing_lineage,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=[baseline_scenario],
    )

    check(
        result["status"] == STATUS_BLOCKED,
        "missing valuation lineage must block certification",
    )

    # --------------------------------------------------------
    # 4. Malformed performance
    # --------------------------------------------------------

    result = engine.certify(
        valuation=valuation,
        performance={"status": "CERTIFIED"},
        risk=risk,
        positions=positions,
        scenarios=[baseline_scenario],
    )

    check(
        result["status"] == STATUS_BLOCKED,
        "missing performance lineage must block certification",
    )

    # --------------------------------------------------------
    # 5. Missing risk lineage
    # --------------------------------------------------------

    bad_risk = copy.deepcopy(risk)
    del bad_risk["certificate_id"]

    result = engine.certify(
        valuation=valuation,
        performance=performance,
        risk=bad_risk,
        positions=positions,
        scenarios=[baseline_scenario],
    )

    check(
        result["status"] == STATUS_BLOCKED,
        "missing risk lineage must block certification",
    )

    # --------------------------------------------------------
    # 6. Invalid scenario
    # --------------------------------------------------------

    invalid = _scenario(
        "SCN-BAD",
        "UNKNOWN",
        "Invalid Scenario",
        price_shock_pct=-10,
    )

    result = engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=invalid,
    )

    check(
        result["status"] == STATUS_BLOCKED,
        "invalid scenario type must block",
    )

    # --------------------------------------------------------
    # 7. Price shock
    # --------------------------------------------------------

    price = _scenario(
        "SCN-PRICE",
        "PRICE",
        "Price Shock",
        price_shock_pct=-5,
    )

    result = engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=price,
    )

    check(result["status"] == STATUS_PASS, "price shock failed")
    check(
        result["result"]["stressed_pnl"] < 0,
        "negative price shock should create negative P&L",
    )

    # --------------------------------------------------------
    # 8. Market shock
    # --------------------------------------------------------

    market = _scenario(
        "SCN-MARKET",
        "MARKET",
        "Market Shock",
        market_shock_pct=-8,
    )

    result = engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=market,
    )

    check(result["status"] == STATUS_PASS, "market shock failed")
    check(
        result["result"]["stressed_pnl"] < 0,
        "market shock should create negative P&L",
    )

    # --------------------------------------------------------
    # 9. Volatility shock
    # --------------------------------------------------------

    volatility = _scenario(
        "SCN-VOL",
        "VOLATILITY",
        "Volatility Shock",
        volatility_shock_pct=-20,
    )

    result = engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=volatility,
    )

    check(result["status"] == STATUS_PASS, "volatility shock failed")

    # --------------------------------------------------------
    # 10. Benchmark shock
    # --------------------------------------------------------

    benchmark = _scenario(
        "SCN-BENCH",
        "BENCHMARK",
        "Benchmark Shock",
        benchmark_shock_pct=-7,
        benchmark="NIFTY50",
    )

    result = engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=benchmark,
    )

    check(result["status"] == STATUS_PASS, "benchmark shock failed")

    # --------------------------------------------------------
    # 11. Sector shock
    # --------------------------------------------------------

    sector = _scenario(
        "SCN-SECTOR",
        "SECTOR",
        "Banking Sector Shock",
        sector_shock_pct=-12,
        sector="BANKING",
    )

    result = engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=sector,
    )

    check(result["status"] == STATUS_PASS, "sector shock failed")

    banking = [
        item
        for item in result["result"]["scenario_contribution"]
        if item["symbol"] == "ALPHA"
    ][0]

    energy = [
        item
        for item in result["result"]["scenario_contribution"]
        if item["symbol"] == "GAMMA"
    ][0]

    check(
        banking["effective_shock_pct"] < energy["effective_shock_pct"],
        "sector shock must affect matching sector",
    )

    # --------------------------------------------------------
    # 12. Liquidity shock
    # --------------------------------------------------------

    liquidity = _scenario(
        "SCN-LIQ",
        "LIQUIDITY",
        "Liquidity Shock",
        liquidity_shock_pct=-10,
    )

    result = engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=liquidity,
    )

    check(result["status"] == STATUS_PASS, "liquidity shock failed")

    # --------------------------------------------------------
    # 13. Correlation shock
    # --------------------------------------------------------

    correlation = _scenario(
        "SCN-CORR",
        "CORRELATION",
        "Correlation Shock",
        correlation_shock_pct=-4,
    )

    result = engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=correlation,
    )

    check(result["status"] == STATUS_PASS, "correlation shock failed")

    # --------------------------------------------------------
    # 14. Downside
    # --------------------------------------------------------

    downside = _scenario(
        "SCN-DOWN",
        "DOWNSIDE",
        "Downside Scenario",
        default_shock_pct=-15,
    )

    result = engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=downside,
    )

    check(result["status"] == STATUS_PASS, "downside failed")
    check(
        result["result"]["stressed_equity"] < result["result"]["base_equity"],
        "downside equity should decrease",
    )

    # --------------------------------------------------------
    # 15. Upside
    # --------------------------------------------------------

    upside = _scenario(
        "SCN-UP",
        "UPSIDE",
        "Upside Scenario",
        default_shock_pct=10,
    )

    result = engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=upside,
    )

    check(result["status"] == STATUS_PASS, "upside failed")
    check(
        result["result"]["stressed_equity"] > result["result"]["base_equity"],
        "upside equity should increase",
    )

    # --------------------------------------------------------
    # 16. Combined
    # --------------------------------------------------------

    combined = _scenario(
        "SCN-COMBINED",
        "COMBINED",
        "Combined Stress",
        price_shock_pct=-5,
        market_shock_pct=-5,
        volatility_shock_pct=-5,
        benchmark_shock_pct=-3,
        benchmark="NIFTY50",
        sector_shock_pct=-2,
        sector="BANKING",
        liquidity_shock_pct=-2,
        correlation_shock_pct=-1,
    )

    result = engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=combined,
    )

    check(result["status"] == STATUS_PASS, "combined scenario failed")
    check(
        len(result["result"]["scenario_contribution"]) == 3,
        "combined contribution count incorrect",
    )

    # --------------------------------------------------------
    # 17. Batch execution
    # --------------------------------------------------------

    scenarios = [
        price,
        market,
        downside,
        upside,
        combined,
    ]

    batch = engine.run_scenarios(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    check(batch["status"] == STATUS_PASS, "scenario batch failed")
    check(batch["count"] == 5, "scenario batch count incorrect")

    # --------------------------------------------------------
    # 18. Duplicate scenario
    # --------------------------------------------------------

    duplicate_batch = engine.run_scenarios(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=[price, price],
    )

    check(
        duplicate_batch["results"][1]["status"] == STATUS_DUPLICATE,
        "duplicate scenario must be DUPLICATE",
    )

    # --------------------------------------------------------
    # 19. Certification
    # --------------------------------------------------------

    certificate = engine.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    check(
        certificate["status"] == STATUS_CERTIFIED,
        "stress certificate should be certified",
    )

    check(
        certificate["certificate_id"].startswith("EROS94-STRESS-"),
        "certificate ID prefix incorrect",
    )

    check(
        certificate["broker_submission"] is False,
        "broker submission invariant failed",
    )

    check(
        certificate["live_order_submission"] is False,
        "live execution invariant failed",
    )

    # --------------------------------------------------------
    # 20. Duplicate certificate
    # --------------------------------------------------------

    duplicate_certificate = engine.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    check(
        duplicate_certificate["status"] == STATUS_DUPLICATE,
        "identical certification must be duplicate",
    )

    # --------------------------------------------------------
    # 21. Read-only valuation
    # --------------------------------------------------------

    valuation_before = copy.deepcopy(valuation)

    engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=price,
    )

    check(
        valuation == valuation_before,
        "valuation was mutated",
    )

    # --------------------------------------------------------
    # 22. Read-only performance
    # --------------------------------------------------------

    performance_before = copy.deepcopy(performance)

    engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=price,
    )

    check(
        performance == performance_before,
        "performance was mutated",
    )

    # --------------------------------------------------------
    # 23. Read-only risk
    # --------------------------------------------------------

    risk_before = copy.deepcopy(risk)

    engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=price,
    )

    check(
        risk == risk_before,
        "risk was mutated",
    )

    # --------------------------------------------------------
    # 24. Read-only positions
    # --------------------------------------------------------

    positions_before = copy.deepcopy(positions)

    engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=price,
    )

    check(
        positions == positions_before,
        "positions were mutated",
    )

    # --------------------------------------------------------
    # 25. Forbidden broker payload
    # --------------------------------------------------------

    forbidden = copy.deepcopy(price)
    forbidden["broker_submission"] = True

    result = engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=forbidden,
    )

    check(
        result["status"] == STATUS_BLOCKED,
        "broker payload must be blocked",
    )

    # --------------------------------------------------------
    # 26. Forbidden live execution payload
    # --------------------------------------------------------

    forbidden_live = copy.deepcopy(price)
    forbidden_live["live_execution"] = True

    result = engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=forbidden_live,
    )

    check(
        result["status"] == STATUS_BLOCKED,
        "live execution payload must be blocked",
    )

    # --------------------------------------------------------
    # 27. Empty positions
    # --------------------------------------------------------

    result = engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=[],
        scenario=price,
    )

    check(
        result["status"] == STATUS_BLOCKED,
        "empty positions must be blocked",
    )

    # --------------------------------------------------------
    # 28. Missing scenarios
    # --------------------------------------------------------

    result = engine.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=[],
    )

    check(
        result["status"] == STATUS_BLOCKED,
        "empty scenario set must be blocked",
    )

    # --------------------------------------------------------
    # 29. Snapshot isolation
    # --------------------------------------------------------

    snapshot = engine.snapshot()

    check(
        snapshot["certificate_count"] == 1,
        "snapshot certificate count incorrect",
    )

    snapshot["certificates"][0]["certificate_status"] = "MUTATED"

    fresh_snapshot = engine.snapshot()

    check(
        fresh_snapshot["certificates"][0]["certificate_status"]
        == STATUS_CERTIFIED,
        "snapshot leaked internal state",
    )

    # --------------------------------------------------------
    # 30. Certificate history isolation
    # --------------------------------------------------------

    history = engine.certificate_history()

    check(
        len(history) == 1,
        "certificate history count incorrect",
    )

    history[0]["status"] = "MUTATED"

    check(
        engine.certificate_history()[0]["status"] == STATUS_CERTIFIED,
        "certificate history leaked internal state",
    )

    # --------------------------------------------------------
    # 31. Scenario history
    # --------------------------------------------------------

    scenario_history = engine.scenario_history()

    check(
        len(scenario_history) == 5,
        "scenario history count incorrect",
    )

    # --------------------------------------------------------
    # 32. Stress portfolio
    # --------------------------------------------------------

    stress = engine.stress_portfolio(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    check(
        stress["status"] == STATUS_PASS,
        "stress_portfolio failed",
    )

    check(
        stress["successful_scenarios"] == 5,
        "successful scenario count incorrect",
    )

    # --------------------------------------------------------
    # 33. Contribution percentages
    # --------------------------------------------------------

    contribution = result = engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=downside,
    )

    total_contribution = sum(
        item["contribution_pct"]
        for item in contribution["result"]["scenario_contribution"]
    )

    check(
        abs(total_contribution - 100.0) < 1e-9,
        "scenario contributions must sum to 100%",
    )

    # --------------------------------------------------------
    # 34. Negative stress produces drawdown
    # --------------------------------------------------------

    check(
        contribution["result"]["stressed_drawdown_pct"] > 0,
        "downside scenario should produce drawdown",
    )

    # --------------------------------------------------------
    # 35. Positive stress does not create downside drawdown
    # --------------------------------------------------------

    positive = engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=upside,
    )

    check(
        positive["result"]["stressed_drawdown_pct"] == 0.0,
        "upside scenario should not create downside drawdown",
    )

    # --------------------------------------------------------
    # 36. Certificate contains lineage
    # --------------------------------------------------------

    check(
        certificate["valuation_id"] == "EROS91-VAL-001",
        "valuation lineage incorrect",
    )

    check(
        certificate["performance_id"] == "EROS92-PERF-001",
        "performance lineage incorrect",
    )

    check(
        certificate["risk_certificate_id"] == "EROS93-RISK-001",
        "risk lineage incorrect",
    )

    # --------------------------------------------------------
    # 37. No portfolio mutation flag
    # --------------------------------------------------------

    check(
        certificate["non_mutation_invariant"] is True,
        "non-mutation certificate invariant failed",
    )

    # --------------------------------------------------------
    # 38. No live order flag
    # --------------------------------------------------------

    check(
        certificate["live_order_submission"] is False,
        "live order flag failed",
    )

    # --------------------------------------------------------
    # 39. No broker flag
    # --------------------------------------------------------

    check(
        certificate["broker_submission"] is False,
        "broker flag failed",
    )

    # --------------------------------------------------------
    # 40. Deterministic certificate ID
    # --------------------------------------------------------

    engine2 = EROSBlock94PortfolioStressScenarioEngine()

    certificate2 = engine2.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )

    check(
        certificate2["certificate_id"] == certificate["certificate_id"],
        "certificate ID is not deterministic",
    )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    return {
        "status": STATUS_PASS,
        "tests_run": tests_run,
        "tests_passed": tests_passed,
        "certificate_status": certificate["certificate_status"],
        "certificate_id": certificate["certificate_id"],
        "scenario_count": certificate["scenario_count"],
        "successful_scenarios": stress["successful_scenarios"],
        "blocked_scenarios": stress["blocked_scenarios"],
        "duplicate_scenarios": stress["duplicate_scenarios"],
        "downside_pnl": contribution["result"]["stressed_pnl"],
        "upside_pnl": positive["result"]["stressed_pnl"],
        "non_mutation_invariant": certificate["non_mutation_invariant"],
        "broker_submission": certificate["broker_submission"],
        "live_order_submission": certificate["live_order_submission"],
    }


if __name__ == "__main__":
    print(run_block94_self_test())
