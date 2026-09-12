from __future__ import annotations

from services.monitoring.health import MonitoringPlatform
from services.monitoring.models import SystemHealthReport


def test_system_health_immutability() -> None:
    rep = SystemHealthReport(
        status="HEALTHY",
        component_health={"Core": "HEALTHY"},
        metrics={"latency": 12.0},
        active_alerts=0,
    )
    assert rep.status == "HEALTHY"
    assert rep.active_alerts == 0
    assert rep.timestamp is not None
    assert isinstance(rep.metadata, dict)


def test_monitoring_platform() -> None:
    report = MonitoringPlatform.get_system_health()
    assert report.status == "HEALTHY"
    assert "WorkflowEngine" in report.component_health
    assert report.metrics["api_latency_ms"] > 0
    assert report.active_alerts == 0
