from services.monitoring.health import MonitoringPlatform
from services.monitoring.models import SystemHealthReport

def test_block21a_system_health_contract():
    result = MonitoringPlatform.get_system_health()
    assert isinstance(result, SystemHealthReport)
    assert result.status in [
        "HEALTHY",
        "DEGRADED",
        "CRITICAL",
    ]
    required_components = {
        "WorkflowEngine",
        "FeatureStore",
        "ModelRegistry",
        "ComplianceEngine",
        "EventBus",
    }
    assert required_components.issubset(
        set(result.component_health.keys())
    )
    required_metrics = {
        "api_latency_ms",
        "memory_usage_pct",
        "queue_depth",
        "active_workflows",
    }
    assert required_metrics.issubset(
        set(result.metrics.keys())
    )
    assert result.metrics["api_latency_ms"] >= 0.0
    assert 0.0 <= result.metrics["memory_usage_pct"] <= 100.0
    assert result.metrics["queue_depth"] >= 0.0
    assert result.metrics["active_workflows"] >= 0.0
    assert result.active_alerts >= 0
    assert result.timestamp
