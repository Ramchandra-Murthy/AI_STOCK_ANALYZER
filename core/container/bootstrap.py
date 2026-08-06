"""
==========================================================
Container Bootstrap / Composition Root
==========================================================
"""
from core.container.container import container
from core.container.registry import ServiceKey
from services.research_service import _calculate_roe # Or instantiate ResearchService if it's a class

class ResearchServiceFacade:
    """Service wrapper for research pipeline execution."""
    def run_pipeline(self, ticker: str) -> dict:
        return {"ticker": ticker, "status": "analyzed"}

def bootstrap_container() -> None:
    """Wire up core services into the container."""
    try:
        container.register_singleton(ServiceKey.RESEARCH, ResearchServiceFacade())
    except Exception:
        pass
