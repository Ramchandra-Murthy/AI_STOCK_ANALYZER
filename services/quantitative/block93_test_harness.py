"""
EROS 3.0 - BLOCK 93 TEST HARNESS.

Long-form adversarial contract suite for the Block 93
Performance Risk / Attribution Certification Engine.

The harness is intentionally self-contained and does not contact a broker,
submit orders, invoke live execution, or mutate portfolio state.
"""

from __future__ import annotations

from copy import deepcopy
from math import isfinite
from typing import Any

from .block93_performance_risk_attribution_engine import (
    STATUS_BLOCKED,
    STATUS_CERTIFIED,
    STATUS_DUPLICATE,
    EROSBlock93PerformanceRiskAttributionEngine,
)


def _base_performance() -> dict[str, Any]:
    return {
        "performance_id": "EROS92-PERF-001",
        "performance_status": "CERTIFIED",
        "valuation_id": "EROS91-VAL-001",
        "settlement_id": "EROS89-SET-001",
        "audit_id": "EROS88-AUDIT-001",
        "decision_id": "EROS86-DEC-001",
        "equity_history": [
            10000000.0,
            10100000.0,
            10050000.0,
            10200000.0,
            10400000.0,
        ],
        "performance_history": [
            {
                "period": "2026-01",
                "portfolio_return": 0.010,
                "benchmark_return": 0.008,
            },
            {
                "period": "2026-02",
                "portfolio_return": -0.005,
                "benchmark_return": -0.004,
            },
            {
                "period": "2026-03",
                "portfolio_return": 0.015,
                "benchmark_return": 0.010,
            },
            {
                "period": "2026-04",
                "portfolio_return": 0.020,
                "benchmark_return": 0.012,
            },
        ],
        "attribution": [
            {
                "symbol": "RELIANCE",
                "portfolio_weight": 0.40,
                "benchmark_weight": 0.35,
                "portfolio_return": 0.05,
                "benchmark_return": 0.04,
            },
            {
                "symbol": "TCS",
                "portfolio_weight": 0.35,
                "benchmark_weight": 0.30,
                "portfolio_return": 0.03,
                "benchmark_return": 0.025,
            },
            {
                "symbol": "HDFCBANK",
                "portfolio_weight": 0.25,
                "benchmark_weight": 0.35,
                "portfolio_return": 0.02,
                "benchmark_return": 0.018,
            },
        ],
    }


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _run_test(name: str, fn) -> dict[str, Any]:
    fn()
    return {"name": name, "status": "PASS"}


def test_certified_performance() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.certify(_base_performance())
    _assert(result["status"] == STATUS_CERTIFIED, "certification failed")
    _assert(result["non_bypass_invariant"] is True, "non-bypass missing")
    _assert(result["broker_submission"] is False, "broker invariant failed")
    _assert(result["live_order_submission"] is False, "live invariant failed")


def test_metrics_exist() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.certify(_base_performance())
    metrics = result["risk_metrics"]
    for key in (
        "volatility",
        "downside_volatility",
        "maximum_drawdown",
        "sharpe_ratio",
        "sortino_ratio",
        "beta",
        "alpha",
        "tracking_error",
        "information_ratio",
    ):
        _assert(key in metrics, f"missing metric: {key}")


def test_attribution_exists() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.certify(_base_performance())
    _assert(len(result["attribution"]) == 3, "attribution count mismatch")


def test_duplicate_performance() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    first = engine.certify(_base_performance())
    second = engine.certify(_base_performance())
    _assert(first["status"] == STATUS_CERTIFIED, "first certification failed")
    _assert(second["status"] == STATUS_DUPLICATE, "duplicate not blocked")


def test_blocked_status() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    payload = _base_performance()
    payload["performance_status"] = "BLOCKED"
    result = engine.certify(payload)
    _assert(result["status"] == STATUS_BLOCKED, "blocked status accepted")


def test_missing_performance_lineage() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    payload = _base_performance()
    del payload["performance_id"]
    result = engine.certify(payload)
    _assert(result["status"] == STATUS_BLOCKED, "missing performance lineage accepted")


def test_missing_valuation_lineage() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    payload = _base_performance()
    del payload["valuation_id"]
    result = engine.certify(payload)
    _assert(result["status"] == STATUS_BLOCKED, "missing valuation lineage accepted")


def test_missing_settlement_lineage() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    payload = _base_performance()
    del payload["settlement_id"]
    result = engine.certify(payload)
    _assert(result["status"] == STATUS_BLOCKED, "missing settlement lineage accepted")


def test_missing_audit_lineage() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    payload = _base_performance()
    del payload["audit_id"]
    result = engine.certify(payload)
    _assert(result["status"] == STATUS_BLOCKED, "missing audit lineage accepted")


def test_missing_decision_lineage() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    payload = _base_performance()
    del payload["decision_id"]
    result = engine.certify(payload)
    _assert(result["status"] == STATUS_BLOCKED, "missing decision lineage accepted")


def test_insufficient_history() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine(minimum_history=2)
    payload = _base_performance()
    payload["performance_history"] = payload["performance_history"][:1]
    result = engine.certify(payload)
    _assert(result["status"] == STATUS_BLOCKED, "insufficient history accepted")


def test_malformed_history() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    payload = _base_performance()
    payload["performance_history"] = ["not-a-record"]
    result = engine.certify(payload)
    _assert(result["status"] == STATUS_BLOCKED, "malformed history accepted")


def test_invalid_date_order() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    payload = _base_performance()
    payload["performance_history"] = list(reversed(payload["performance_history"]))
    result = engine.certify(payload)
    _assert(result["status"] == STATUS_BLOCKED, "date order violation accepted")


def test_invalid_equity() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    payload = _base_performance()
    payload["equity_history"] = [10000000.0, 0.0, 10500000.0]
    result = engine.certify(payload)
    _assert(result["status"] == STATUS_BLOCKED, "invalid equity accepted")


def test_invalid_return() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    payload = _base_performance()
    payload["performance_history"][0]["portfolio_return"] = 999.0
    result = engine.certify(payload)
    _assert(result["status"] == STATUS_BLOCKED, "invalid return accepted")


def test_invalid_benchmark() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    payload = _base_performance()
    payload["performance_history"][0]["benchmark_return"] = 999.0
    result = engine.certify(payload)
    _assert(result["status"] == STATUS_BLOCKED, "invalid benchmark accepted")


def test_nan_rejection() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    payload = _base_performance()
    payload["performance_history"][0]["portfolio_return"] = float("nan")
    result = engine.certify(payload)
    _assert(result["status"] == STATUS_BLOCKED, "NaN accepted")


def test_infinity_rejection() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    payload = _base_performance()
    payload["performance_history"][0]["portfolio_return"] = float("inf")
    result = engine.certify(payload)
    _assert(result["status"] == STATUS_BLOCKED, "infinity accepted")


def test_baseline_controlled() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine(minimum_history=1)
    payload = _base_performance()
    payload["performance_history"] = payload["performance_history"][:1]
    result = engine.certify(payload)
    _assert(result["status"] == STATUS_CERTIFIED, "controlled one-period baseline failed")


def test_sharpe_is_finite() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.certify(_base_performance())
    value = result["risk_metrics"]["sharpe_ratio"]
    _assert(isfinite(float(value)), "Sharpe is not finite")


def test_sortino_is_finite() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.certify(_base_performance())
    value = result["risk_metrics"]["sortino_ratio"]
    _assert(isfinite(float(value)), "Sortino is not finite")


def test_beta_exists() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.certify(_base_performance())
    _assert("beta" in result["risk_metrics"], "beta missing")


def test_alpha_exists() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.certify(_base_performance())
    _assert("alpha" in result["risk_metrics"], "alpha missing")


def test_tracking_error_exists() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.certify(_base_performance())
    _assert("tracking_error" in result["risk_metrics"], "tracking error missing")


def test_information_ratio_exists() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.certify(_base_performance())
    _assert("information_ratio" in result["risk_metrics"], "information ratio missing")


def test_max_drawdown_is_nonnegative() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.certify(_base_performance())
    _assert(result["risk_metrics"]["maximum_drawdown"] >= 0, "drawdown sign invalid")


def test_benchmark_risk_exists() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.certify(_base_performance())
    _assert(
        "benchmark_volatility" in result["risk_metrics"],
        "benchmark risk missing",
    )


def test_certificate_hash_exists() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.certify(_base_performance())
    _assert(len(result["certificate_hash"]) == 64, "certificate hash invalid")


def test_certificate_id_exists() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.certify(_base_performance())
    _assert(
        result["certificate_id"].startswith("EROS93-"),
        "certificate ID invalid",
    )


def test_snapshot() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    engine.certify(_base_performance())
    snapshot = engine.snapshot()
    _assert(snapshot["certificate_count"] == 1, "snapshot count invalid")
    _assert(snapshot["history_count"] == 1, "snapshot history invalid")


def test_history() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    engine.certify(_base_performance())
    history = engine.certificate_history()
    _assert(len(history) == 1, "history length invalid")


def test_missing_certificate() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    _assert(engine.get_certificate("DOES-NOT-EXIST") is None, "unknown certificate resolved")


def test_forbidden_order_creation() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.create_order({"symbol": "RELIANCE"})
    _assert(result["status"] == STATUS_BLOCKED, "order creation bypass")


def test_forbidden_broker_submission() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.submit_broker_order({"symbol": "RELIANCE"})
    _assert(result["status"] == STATUS_BLOCKED, "broker bypass")


def test_forbidden_live_execution() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.execute_live_order({"symbol": "RELIANCE"})
    _assert(result["status"] == STATUS_BLOCKED, "live execution bypass")


def test_forbidden_portfolio_mutation() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.mutate_portfolio({"symbol": "RELIANCE"})
    _assert(result["status"] == STATUS_BLOCKED, "portfolio mutation bypass")


def test_forbidden_valuation_mutation() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.mutate_valuation({"valuation_id": "X"})
    _assert(result["status"] == STATUS_BLOCKED, "valuation mutation bypass")


def test_forbidden_optimization() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    result = engine.optimize_portfolio({"symbol": "RELIANCE"})
    _assert(result["status"] == STATUS_BLOCKED, "optimization bypass")


def test_input_is_not_mutated() -> None:
    engine = EROSBlock93PerformanceRiskAttributionEngine()
    payload = _base_performance()
    before = deepcopy(payload)
    engine.certify(payload)
    _assert(payload == before, "input payload mutated")


def test_two_independent_engines() -> None:
    first = EROSBlock93PerformanceRiskAttributionEngine()
    second = EROSBlock93PerformanceRiskAttributionEngine()
    a = first.certify(_base_performance())
    b = second.certify(_base_performance())
    _assert(a["certificate_id"] == b["certificate_id"], "determinism failed")


def run_block93_self_test() -> dict[str, Any]:
    tests = [
        ("certified_performance", test_certified_performance),
        ("metrics_exist", test_metrics_exist),
        ("attribution_exists", test_attribution_exists),
        ("duplicate_performance", test_duplicate_performance),
        ("blocked_status", test_blocked_status),
        ("missing_performance_lineage", test_missing_performance_lineage),
        ("missing_valuation_lineage", test_missing_valuation_lineage),
        ("missing_settlement_lineage", test_missing_settlement_lineage),
        ("missing_audit_lineage", test_missing_audit_lineage),
        ("missing_decision_lineage", test_missing_decision_lineage),
        ("insufficient_history", test_insufficient_history),
        ("malformed_history", test_malformed_history),
        ("invalid_date_order", test_invalid_date_order),
        ("invalid_equity", test_invalid_equity),
        ("invalid_return", test_invalid_return),
        ("invalid_benchmark", test_invalid_benchmark),
        ("nan_rejection", test_nan_rejection),
        ("infinity_rejection", test_infinity_rejection),
        ("baseline_controlled", test_baseline_controlled),
        ("sharpe_is_finite", test_sharpe_is_finite),
        ("sortino_is_finite", test_sortino_is_finite),
        ("beta_exists", test_beta_exists),
        ("alpha_exists", test_alpha_exists),
        ("tracking_error_exists", test_tracking_error_exists),
        ("information_ratio_exists", test_information_ratio_exists),
        ("max_drawdown_is_nonnegative", test_max_drawdown_is_nonnegative),
        ("benchmark_risk_exists", test_benchmark_risk_exists),
        ("certificate_hash_exists", test_certificate_hash_exists),
        ("certificate_id_exists", test_certificate_id_exists),
        ("snapshot", test_snapshot),
        ("history", test_history),
        ("missing_certificate", test_missing_certificate),
        ("forbidden_order_creation", test_forbidden_order_creation),
        ("forbidden_broker_submission", test_forbidden_broker_submission),
        ("forbidden_live_execution", test_forbidden_live_execution),
        ("forbidden_portfolio_mutation", test_forbidden_portfolio_mutation),
        ("forbidden_valuation_mutation", test_forbidden_valuation_mutation),
        ("forbidden_optimization", test_forbidden_optimization),
        ("input_is_not_mutated", test_input_is_not_mutated),
        ("two_independent_engines", test_two_independent_engines),
    ]

    passed: list[str] = []
    for name, fn in tests:
        _run_test(name, fn)
        passed.append(name)

    engine = EROSBlock93PerformanceRiskAttributionEngine()
    final = engine.certify(_base_performance())

    return {
        "status": "PASS",
        "tests_run": len(tests),
        "tests_passed": len(passed),
        "valuation_lineage": final["valuation_id"],
        "performance_id": final["performance_id"],
        "certificate_status": final["status"],
        "certificate_id": final["certificate_id"],
        "volatility": final["risk_metrics"]["volatility"],
        "maximum_drawdown": final["risk_metrics"]["maximum_drawdown"],
        "sharpe_ratio": final["risk_metrics"]["sharpe_ratio"],
        "sortino_ratio": final["risk_metrics"]["sortino_ratio"],
        "beta": final["risk_metrics"]["beta"],
        "alpha": final["risk_metrics"]["alpha"],
        "tracking_error": final["risk_metrics"]["tracking_error"],
        "information_ratio": final["risk_metrics"]["information_ratio"],
        "attribution_count": len(final["attribution"]),
        "duplicate_status": engine.certify(_base_performance())["status"],
        "broker_submission": False,
        "live_order_submission": False,
        "portfolio_mutation": False,
        "valuation_mutation": False,
        "non_bypass_invariant": True,
    }


if __name__ == "__main__":
    print(run_block93_self_test())
