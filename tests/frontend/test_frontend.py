from __future__ import annotations

from frontend.src.pages.dashboard import InstitutionalDashboardComponent


def test_institutional_web_platform_dashboard() -> None:
    metrics = InstitutionalDashboardComponent.get_dashboard_metrics()

    assert metrics["market_regime"] == "Expansion"
    assert metrics["institutional_breadth_score"] == 82.0
    assert metrics["workflow_queue_status"] == "Idle"
    assert metrics["archived_reports_count"] == 128
    assert metrics["portfolio_alpha"] == 5.8
    assert "NIFTY50" in metrics["market_indices"]
