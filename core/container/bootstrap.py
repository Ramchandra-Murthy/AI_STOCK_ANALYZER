"""
Application Bootstrap
Registers core services into the global ServiceContainer.
"""
from __future__ import annotations

from core.container.container import container
from services.market_service import MarketService
from services.portfolio_service import PortfolioService
from services.research_service import ResearchService

def bootstrap_container() -> None:
    # Register core services as singletons or instances
    if "market" not in container.registered_services:
        container.register_instance("market", MarketService())
    if "portfolio" not in container.registered_services:
        container.register_instance("portfolio", PortfolioService())
    if "research" not in container.registered_services:
        container.register_instance("research", ResearchService())

# Automatically bootstrap upon import
bootstrap_container()
