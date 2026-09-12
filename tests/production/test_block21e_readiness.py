from services.production.readiness_report import (
    ProductionReadinessEngine,
    ProductionReadinessReport,
)


def test_block21e_production_readiness():
    report = ProductionReadinessEngine.evaluate_readiness()
    assert isinstance(report, ProductionReadinessReport)
    assert report.system_status == "HEALTHY"
    assert report.is_production_ready is True
    assert report.components_checked == report.healthy_components
    assert report.details["engine_version"] == "EROS-3.0-BLOCK-21E"
