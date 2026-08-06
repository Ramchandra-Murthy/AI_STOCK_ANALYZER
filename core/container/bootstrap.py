"""
==========================================================
Container Bootstrap / Composition Root
==========================================================
"""
from core.container.container import container
from core.container.registry import ServiceKey
from services.valuation.dispatcher import ValuationDispatcher

class ResearchServiceFacade:
    """Service wrapper for research pipeline execution."""
    def run_pipeline(self, ticker: str) -> dict:
        return {"ticker": ticker, "status": "analyzed"}

def bootstrap_container() -> None:
    """Wire up core services into the container."""
    try:
        container.register_singleton(ServiceKey.RESEARCH, ResearchServiceFacade())
        container.register_singleton("valuation_dispatcher", ValuationDispatcher())
    except Exception as e:
        print(f"Bootstrap warning: {e}")
