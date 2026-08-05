from __future__ import annotations

from core.container.container import container
from services.valuation.dcf_engine import DCFValuationEngine
from services.valuation.dispatcher import ValuationDispatcher
from services.valuation.nav_engine import NAVValuationEngine
from services.valuation.sotp_engine import SOTPValuationEngine


def bootstrap_container() -> None:
    """Bootstrap and register all core application services into the container."""

    # Register Valuation Engines
    container.register_instance("dcf_engine", DCFValuationEngine())
    container.register_instance("nav_engine", NAVValuationEngine())
    container.register_instance("sotp_engine", SOTPValuationEngine())

    # Register Dispatcher via factory to inject registered engines
    def _create_dispatcher(c: container.__class__) -> ValuationDispatcher:
        dispatcher = ValuationDispatcher()
        dispatcher.register_engine("DCF", c.resolve("dcf_engine"))
        dispatcher.register_engine("NAV", c.resolve("nav_engine"))
        dispatcher.register_engine("SOTP", c.resolve("sotp_engine"))
        return dispatcher

    container.register_factory("valuation_dispatcher", _create_dispatcher)


# Automatically bootstrap on import
bootstrap_container()
