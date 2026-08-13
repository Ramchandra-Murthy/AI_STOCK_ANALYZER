from services.validation.backtest_engine import InstitutionalBacktestEngine
from services.monitoring.health import MonitoringPlatform

def test_block21d_system_health_under_degraded_load():
    health = MonitoringPlatform.get_system_health()
    # Verify telemetry invariants
    assert health.metrics["api_latency_ms"] >= 0.0
    assert health.metrics["memory_usage_pct"] <= 100.0

def test_block21d_backtest_edge_cases():
    engine = InstitutionalBacktestEngine()
    # Test flat price return
    res = engine.evaluate_signal(symbol="TEST.NS", signal_date="2026-01-01", entry_price=100.0, exit_price=100.0)
    assert res.return_pct == 0.0
    assert res.accuracy is False
