from __future__ import annotations

from typing import Any


class InstitutionalDashboardComponent:
    """Institutional Command Center Dashboard presentation model for the EROS Web Platform."""

    @staticmethod
    def get_dashboard_metrics() -> dict[str, Any]:
        return {
            "market_indices": {
                "NIFTY50": {"value": 24850.0, "change_pct": 0.81},
                "BANKNIFTY": {"value": 51200.0, "change_pct": 1.22},
            },
            "market_regime": "Expansion",
            "institutional_breadth_score": 82.0,
            "workflow_queue_status": "Idle",
            "archived_reports_count": 128,
            "portfolio_alpha": 5.8,
        }
