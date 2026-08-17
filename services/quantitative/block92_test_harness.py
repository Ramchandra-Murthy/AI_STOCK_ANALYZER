from __future__ import annotations

from services.quantitative.block92_portfolio_performance_engine import (
    EROSBlock92PortfolioPerformanceEngine,
)


def _certified_valuation():
    return {
        "status": "PASS",
        "valuation": {
            "valuation_id": "EROS91-TEST-VALUATION",
            "portfolio_id": "EROS-TEST-PORTFOLIO",
            "portfolio_equity": 10_400_000.0,
            "market_value": 10_000_000.0,
            "realized_pnl": 100_000.0,
            "unrealized_pnl": 300_000.0,
            "total_pnl": 400_000.0,
            "return_pct": 4.0,
            "settlement_id": "EROS89-TEST-SETTLEMENT",
            "audit_id": "EROS88-TEST-AUDIT",
            "decision_id": "EROS86-TEST-DECISION",
        },
        "certificate": {
            "status": "CERTIFIED",
            "valuation_id": "EROS91-TEST-VALUATION",
            "settlement_id": "EROS89-TEST-SETTLEMENT",
            "audit_id": "EROS88-TEST-AUDIT",
            "decision_id": "EROS86-TEST-DECISION",
        },
    }


def _prior_valuation():
    return {
        "valuation_id": "EROS91-PRIOR-VALUATION",
        "portfolio_id": "EROS-TEST-PORTFOLIO",
        "portfolio_equity": 10_000_000.0,
    }


def _benchmark():
    return {
        "benchmark_name": "NIFTY50",
        "return_pct": 2.0,
        "beta": 1.05,
        "portfolio_returns": [
            0.010,
            0.020,
            0.015,
            0.025,
        ],
        "benchmark_returns": [
            0.008,
            0.015,
            0.010,
            0.020,
        ],
    }


def run_block92_self_test():
    engine = EROSBlock92PortfolioPerformanceEngine()

    valuation = _certified_valuation()
    prior = _prior_valuation()
    benchmark = _benchmark()

    # ------------------------------------------------------
    # TEST 1 - CERTIFIED VALUATION -> PERFORMANCE
    # ------------------------------------------------------

    result = engine.calculate_performance(
        valuation,
        prior_valuation=prior,
        benchmark=benchmark,
    )

    assert result["status"] == "PASS", result
    assert result["calculation_status"] == "CERTIFIED"

    performance = result["performance"]

    assert performance["current_equity"] == 10_400_000.0
    assert performance["prior_equity"] == 10_000_000.0
    assert performance["absolute_pnl"] == 400_000.0
    assert performance["return_pct"] == 4.0
    assert performance["benchmark_return_pct"] == 2.0
    assert performance["active_return_pct"] == 2.0
    assert performance["beta"] == 1.05

    assert result["certificate"]["status"] == "CERTIFIED"

    # ------------------------------------------------------
    # TEST 2 - READ-ONLY INVARIANT
    # ------------------------------------------------------

    assert result["mutation_allowed"] is False
    assert result["broker_submission"] is False
    assert result["live_order_submission"] is False

    # ------------------------------------------------------
    # TEST 3 - DUPLICATE
    # ------------------------------------------------------

    duplicate = engine.calculate_performance(
        valuation,
        prior_valuation=prior,
        benchmark=benchmark,
    )

    assert duplicate["status"] == "DUPLICATE"
    assert duplicate["calculation_status"] == "DUPLICATE"

    # ------------------------------------------------------
    # TEST 4 - BLOCKED VALUATION
    # ------------------------------------------------------

    blocked = _certified_valuation()
    blocked["status"] = "BLOCKED"
    blocked["certificate"]["status"] = "BLOCKED"

    blocked_result = engine.calculate_performance(
        blocked,
        prior_valuation=prior,
        benchmark=benchmark,
    )

    assert blocked_result["status"] == "BLOCKED"
    assert blocked_result["calculation_status"] == "BLOCKED"
    assert blocked_result["performance"] is None

    # ------------------------------------------------------
    # TEST 5 - MALFORMED VALUATION
    # ------------------------------------------------------

    malformed = _certified_valuation()
    del malformed["valuation"]["valuation_id"]

    malformed_result = engine.calculate_performance(
        malformed,
        prior_valuation=prior,
        benchmark=benchmark,
    )

    assert malformed_result["status"] == "BLOCKED"
    assert "MISSING_VALUATION_ID" in malformed_result["errors"]

    # ------------------------------------------------------
    # TEST 6 - MISSING LINEAGE
    # ------------------------------------------------------

    missing_lineage = _certified_valuation()
    missing_lineage["valuation"]["decision_id"] = ""

    missing_result = engine.calculate_performance(
        missing_lineage,
        prior_valuation=prior,
        benchmark=benchmark,
    )

    assert missing_result["status"] == "BLOCKED"
    assert "MISSING_DECISION_ID" in missing_result["errors"]

    # ------------------------------------------------------
    # TEST 7 - FIRST PERIOD CONTROLLED BASELINE
    # ------------------------------------------------------

    baseline_engine = EROSBlock92PortfolioPerformanceEngine()

    baseline = baseline_engine.calculate_performance(
        valuation,
        prior_valuation=None,
        benchmark=benchmark,
    )

    assert baseline["status"] == "PASS"
    assert baseline["performance"]["prior_equity"] == 0.0
    assert baseline["performance"]["return_pct"] == 0.0

    # ------------------------------------------------------
    # TEST 8 - HISTORY / SNAPSHOT
    # ------------------------------------------------------

    snapshot = engine.snapshot()

    assert snapshot["performance_count"] == 1
    assert snapshot["history_count"] == 1
    assert snapshot["mutation_allowed"] is False

    history = engine.performance_history()

    assert len(history) == 1
    assert history[0]["performance_id"] == (
        performance["performance_id"]
    )

    return {
        "status": "PASS",
        "valuation_status": "CERTIFIED",
        "performance_status": result["calculation_status"],
        "portfolio_equity": performance["current_equity"],
        "prior_equity": performance["prior_equity"],
        "absolute_pnl": performance["absolute_pnl"],
        "return_pct": performance["return_pct"],
        "benchmark_return_pct": performance[
            "benchmark_return_pct"
        ],
        "active_return_pct": performance[
            "active_return_pct"
        ],
        "duplicate_status": duplicate["status"],
        "blocked_status": blocked_result["status"],
        "malformed_status": malformed_result["status"],
        "missing_lineage_status": missing_result["status"],
        "baseline_status": baseline["status"],
        "non_bypass_invariant": (
            result["mutation_allowed"] is False
            and result["broker_submission"] is False
            and result["live_order_submission"] is False
        ),
        "broker_submission": result["broker_submission"],
        "live_order_submission": result[
            "live_order_submission"
        ],
    }


if __name__ == "__main__":
    print(run_block92_self_test())
