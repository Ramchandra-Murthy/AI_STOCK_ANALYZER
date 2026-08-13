from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List
from datetime import datetime
from services.monitoring.health import MonitoringPlatform
from services.monitoring.models import SystemHealthReport

@dataclass(frozen=True, slots=True)
class ProductionReadinessReport:
    system_status: str
    components_checked: int
    healthy_components: int
    is_production_ready: bool
    health_report: SystemHealthReport
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)

class ProductionReadinessEngine:
    """
    EROS 3.0 Block 21E Production Readiness Report Engine.
    Evaluates system telemetry, component health, and compliance status for live institutional deployment.
    """
    @staticmethod
    def evaluate_readiness() -> ProductionReadinessReport:
        health = MonitoringPlatform.get_system_health()
        
        total_comps = len(health.component_health)
        healthy_comps = sum(1 for status in health.component_health.values() if status == "HEALTHY")
        
        is_ready = health.status == "HEALTHY" and healthy_comps == total_comps and health.active_alerts == 0

        return ProductionReadinessReport(
            system_status=health.status,
            components_checked=total_comps,
            healthy_components=healthy_comps,
            is_production_ready=is_ready,
            health_report=health,
            details={
                "engine_version": "EROS-3.0-BLOCK-21E",
                "environment": "Institutional Production",
            }
        )
