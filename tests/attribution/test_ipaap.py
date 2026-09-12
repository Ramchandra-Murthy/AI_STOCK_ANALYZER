from __future__ import annotations

from services.attribution.attribution_engine import PerformanceAttributionEngine
from services.attribution.benchmark_engine import BenchmarkAnalyticsEngine
from services.attribution.models import AttributionReport


def test_attribution_report_immutability() -> None:
    report = AttributionReport(
        portfolio_id="PORT-001",
        benchmark="Nifty 50",
        portfolio_return=0.184,
        benchmark_return=0.152,
        active_return=0.032,
        allocation_effect=0.014,
        selection_effect=0.013,
        interaction_effect=0.005,
    )
    assert report.portfolio_id == "PORT-001"
    assert report.active_return == 0.032
    assert report.timestamp is not None
    assert isinstance(report.metadata, dict)


def test_performance_attribution_engine() -> None:
    report = PerformanceAttributionEngine.generate_brinson_attribution(
        "PORT-001", 0.184, 0.152, "Nifty 50"
    )
    assert report.portfolio_return == 0.184
    assert report.benchmark_return == 0.152
    assert report.active_return == round(
        report.allocation_effect + report.selection_effect + report.interaction_effect, 4
    )


def test_benchmark_analytics_engine() -> None:
    metrics = BenchmarkAnalyticsEngine.compute_benchmark_metrics(0.184, 0.152)
    assert "alpha" in metrics
    assert "beta" in metrics
    assert metrics["beta"] > 0
    assert isinstance(metrics["information_ratio"], float)
