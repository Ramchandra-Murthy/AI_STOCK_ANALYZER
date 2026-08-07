from __future__ import annotations

import logging
from typing import Dict, Any, List
from services.web_platform.models import WebPageDescriptor

logger = logging.getLogger(__name__)

class EnterpriseWebPlatform:
    """Institutional React/TypeScript web platform page registry and UI state coordinator."""

    @staticmethod
    def get_page_descriptor(page_name: str) -> WebPageDescriptor:
        logger.info("Retrieving institutional web platform descriptor for page: '%s'", page_name)

        routes_map = {
            "Dashboard": {"route": "/", "components": ["SummaryCards", "ActiveAlerts", "PortfolioPerformanceWidget"]},
            "Research": {"route": "/research", "components": ["DCFCalculator", "MoatAnalyzer", "KnowledgeGraphViewer"]},
            "Portfolio": {"route": "/portfolio", "components": ["AllocationTable", "RiskMetrics", "RebalanceButton"]},
            "StrategyLab": {"route": "/strategy", "components": ["FactorTiltMatrix", "StrategyBuilder", "BacktestChart"]},
            "Watchlists": {"route": "/watchlists", "components": ["RealTimeMonitor", "CatalystAlerts", "ScoringTable"]},
            "Compliance": {"route": "/compliance", "components": ["MandateValidator", "AuditLogs", "ExposureCharts"]},
            "Workflow": {"route": "/workflow", "components": ["DAGVisualizer", "QueueManager", "ExecutionTimeline"]}
        }

        cfg = routes_map.get(page_name, {"route": f"/{page_name.lower()}", "components": ["GenericContainer"]})

        return WebPageDescriptor(
            page_name=page_name,
            route=cfg["route"],
            components=cfg["components"],
            access_role="INSTITUTIONAL_PORTFOLIO_MANAGER"
        )
