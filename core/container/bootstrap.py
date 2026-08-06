"""
==========================================================
Container Bootstrap / Composition Root
==========================================================
"""
from core.container.container import container
from core.container.registry import ServiceKey

class DummyService:
    def __init__(self, name: str):
        self.name = name

def bootstrap_container() -> None:
    """Wire up core services into the container."""
    # Prevent duplicate bootstrap registrations if called multiple times
    try:
        container.register_singleton(ServiceKey.RESEARCH, DummyService("ResearchService"))
        container.register_singleton(ServiceKey.MARKET, DummyService("MarketService"))
        container.register_singleton(ServiceKey.PORTFOLIO, DummyService("PortfolioService"))
    except Exception:
        pass
