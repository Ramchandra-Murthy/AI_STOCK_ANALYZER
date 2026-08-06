from services.valuation.dcf_engine import DCFEngine
from services.valuation.dispatcher import ValuationDispatcher
from services.valuation.nav_engine import NAVEngine
from services.valuation.sotp_engine import SOTPValuationEngine


def get_valuation_dispatcher() -> ValuationDispatcher:
    dispatcher = ValuationDispatcher()
    dispatcher.register(DCFEngine())
    dispatcher.register(NAVEngine())
    dispatcher.register(SOTPValuationEngine())
    return dispatcher


__all__ = [
    "ValuationDispatcher",
    "DCFEngine",
    "NAVEngine",
    "SOTPValuationEngine",
    "get_valuation_dispatcher",
]
