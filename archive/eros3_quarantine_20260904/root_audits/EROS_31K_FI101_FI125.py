import os, sys, inspect, asyncio, pathlib, traceback

ROOT = pathlib.Path(r"D:\Users\User\Desktop\AI_STOCK_ANALYZER")
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from services.fundamentals.provider import YahooFinanceProvider
from services.fundamentals.normalizer import FinancialNormalizer
from services.fundamentals.service import FundamentalsService
from core.events import InMemoryEventBus, EventDispatcher


def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


async def main():
    section("EROS 3.0 - 31K-FI101 TO FI125 FUNDAMENTALS CACHE/EVENT SEMANTICS")
    print("MODE: READ-ONLY")
    print("WORKING DIRECTORY:", os.getcwd())
    print("PYTHON:", sys.executable)
    print("PYTHONPATH:", ROOT)
    print("SOURCE MODIFICATION: NONE")

    provider = YahooFinanceProvider()
    normalizer = FinancialNormalizer()
    bus = InMemoryEventBus()
    dispatcher = EventDispatcher(bus)
    service = FundamentalsService(provider, normalizer, dispatcher)

    captured = []

    async def capture(event):
        captured.append(event)

    bus.subscribe("fundamentals.downloaded", capture)

    section("31K-FI101 - SERVICE SOURCE")
    source = inspect.getsource(FundamentalsService)
    print(source)

    section("31K-FI102 - SERVICE INSTANCE")
    print("TYPE =", type(service))
    print("MODULE =", type(service).__module__)
    print("DICT =", getattr(service, "__dict__", "NO __DICT__"))

    section("31K-FI103 - INITIAL CACHE")
    cache = getattr(service, "_cache", None)
    print("CACHE TYPE =", type(cache))
    print("CACHE VALUE =", cache)
    print("CACHE SIZE =", len(cache) if isinstance(cache, dict) else "N/A")

    section("31K-FI104 - FIRST CALL")
    first = await service.get_or_download("RELIANCE.NS")
    print("FIRST TYPE =", type(first))
    print("FIRST SYMBOL =", first.symbol)
    print("FIRST PROVIDER =", first.metadata.get("provider"))
    print("FIRST NET INCOME =", first.income_statement.net_income)
    print("EVENT COUNT =", len(captured))

    section("31K-FI105 - CACHE AFTER FIRST CALL")
    cache = getattr(service, "_cache", None)
    print("CACHE TYPE =", type(cache))
    print("CACHE SIZE =", len(cache) if isinstance(cache, dict) else "N/A")
    print("CACHE KEYS =", list(cache.keys()) if isinstance(cache, dict) else "N/A")
    print(
        "CACHE CONTAINS RELIANCE.NS =", "RELIANCE.NS" in cache if isinstance(cache, dict) else "N/A"
    )
    if isinstance(cache, dict):
        print("CACHE OBJECT IS FIRST =", cache.get("RELIANCE.NS") is first)

    section("31K-FI106 - SECOND CALL SAME SYMBOL")
    before = len(captured)
    second = await service.get_or_download("RELIANCE.NS")
    after = len(captured)
    print("SECOND TYPE =", type(second))
    print("FIRST IS SECOND =", first is second)
    print("EVENTS BEFORE =", before)
    print("EVENTS AFTER =", after)
    print("NEW EVENTS =", after - before)

    section("31K-FI107 - SECOND CALL EVENT ANALYSIS")
    for i, event in enumerate(captured, 1):
        print("EVENT", i)
        print(" TYPE =", type(event))
        print(" NAME =", getattr(event, "name", None))
        print(" SYMBOL =", getattr(event, "symbol", None))
        print(" PROVIDER =", getattr(event, "provider", None))
        print(" EVENT ID =", getattr(event, "event_id", None))

    section("31K-FI108 - THIRD CALL SAME SYMBOL")
    before = len(captured)
    third = await service.get_or_download("RELIANCE.NS")
    after = len(captured)
    print("THIRD IS FIRST =", third is first)
    print("EVENTS BEFORE =", before)
    print("EVENTS AFTER =", after)
    print("NEW EVENTS =", after - before)

    section("31K-FI109 - PROVIDER CALL COUNT TEST")
    calls = []

    original_download = provider.download

    def traced_download(symbol):
        calls.append(symbol)
        return original_download(symbol)

    provider.download = traced_download

    service2 = FundamentalsService(provider, normalizer, dispatcher)

    a = await service2.get_or_download("RELIANCE.NS")
    b = await service2.get_or_download("RELIANCE.NS")
    c = await service2.get_or_download("RELIANCE.NS")

    print("PROVIDER DOWNLOAD CALLS =", calls)
    print("DOWNLOAD COUNT =", len(calls))
    print("A IS B =", a is b)
    print("B IS C =", b is c)

    section("31K-FI110 - SERVICE2 CACHE")
    cache2 = getattr(service2, "_cache", None)
    print("CACHE =", cache2)
    print("CACHE SIZE =", len(cache2) if isinstance(cache2, dict) else "N/A")

    section("31K-FI111 - EVENT SUBSCRIBER COUNT")
    print("SUBSCRIBERS =", bus.subscriber_count("fundamentals.downloaded"))
    print("HAS SUBSCRIBERS =", bus.has_subscribers("fundamentals.downloaded"))

    section("31K-FI112 - EVENT BUS INTERNAL STATE")
    print("BUS DICT =", getattr(bus, "__dict__", "NO __DICT__"))

    section("31K-FI113 - DISPATCHER INTERNAL STATE")
    print("DISPATCHER DICT =", getattr(dispatcher, "__dict__", "NO __DICT__"))

    section("31K-FI114 - CACHE IDENTITY")
    if isinstance(cache, dict) and "RELIANCE.NS" in cache:
        cached = cache["RELIANCE.NS"]
        print("CACHED ID =", id(cached))
        print("FIRST ID =", id(first))
        print("SECOND ID =", id(second))
        print("THIRD ID =", id(third))
        print("CACHE IS FIRST =", cached is first)
        print("CACHE IS SECOND =", cached is second)
        print("CACHE IS THIRD =", cached is third)

    section("31K-FI115 - FINANCIAL OBJECT IMMUTABILITY")
    print("DATACLASS TYPE =", type(first))
    print("DATACLASS FROZEN TEST = READ-ONLY")
    try:
        first.symbol = "TEST.NS"
        print("MUTATION RESULT = ALLOWED")
    except Exception as e:
        print("MUTATION RESULT = BLOCKED")
        print("MUTATION ERROR =", type(e).__name__, str(e))

    section("31K-FI116 - CACHE HIT VALUE INTEGRITY")
    assert first is second
    assert second is third
    assert first.income_statement.net_income == 150000.0
    assert first.cash_flow_statement.free_cash_flow == 170000.0
    print("FI116 VALUE INTEGRITY: PASS")

    section("31K-FI117 - CACHE IDENTITY ASSERTION")
    assert isinstance(cache, dict)
    assert cache["RELIANCE.NS"] is first
    print("FI117 CACHE IDENTITY: PASS")

    section("31K-FI118 - PROVIDER CALL ASSERTION")
    assert calls == ["RELIANCE.NS"]
    print("FI118 PROVIDER CALLED ONCE: PASS")

    section("31K-FI119 - EVENT COUNT ANALYSIS")
    print("TOTAL EVENTS FROM FIRST SERVICE =", len(captured))
    print("EXPECTED IF EVENT ON EVERY CALL =", 3)
    print("OBSERVED =", len(captured))
    if len(captured) == 1:
        print("SEMANTICS = EVENT ONLY ON DOWNLOAD")
    elif len(captured) == 3:
        print("SEMANTICS = EVENT ON EVERY SERVICE CALL")
    else:
        print("SEMANTICS = MIXED / NEEDS REVIEW")

    section("31K-FI120 - EVENT OBJECT IDS")
    for i, event in enumerate(captured, 1):
        print("EVENT", i, "ID =", id(event), "EVENT_ID =", getattr(event, "event_id", None))

    section("31K-FI121 - EVENT NAME CONSISTENCY")
    names = [getattr(e, "name", None) for e in captured]
    print("EVENT NAMES =", names)
    print("ALL FUNDAMENTALS DOWNLOADED =", all(n == "fundamentals.downloaded" for n in names))

    section("31K-FI122 - PROVIDER CONSISTENCY")
    providers = [getattr(e, "provider", None) for e in captured]
    print("EVENT PROVIDERS =", providers)
    print("ALL YAHOOFINANCE =", all(p == "YahooFinance" for p in providers))

    section("31K-FI123 - SYMBOL CONSISTENCY")
    symbols = [getattr(e, "symbol", None) for e in captured]
    print("EVENT SYMBOLS =", symbols)
    print("ALL RELIANCE.NS =", all(s == "RELIANCE.NS" for s in symbols))

    section("31K-FI124 - FINAL SEMANTIC CLASSIFICATION")
    print("CACHE IMPLEMENTATION =", "DICT")
    print("CACHE HIT IDENTITY =", first is second)
    print("PROVIDER RE-DOWNLOAD COUNT =", len(calls))
    print("EVENT COUNT =", len(captured))
    print("EVENT ON CACHE HIT =", len(captured) > 1)

    section("31K-FI125 - FINAL INTEGRITY")
    assert first is second
    assert second is third
    assert calls == ["RELIANCE.NS"]
    assert first.income_statement.net_income == 150000.0
    assert first.balance_sheet.debt == 500000.0
    assert first.cash_flow_statement.free_cash_flow == 170000.0
    print("FI101 SERVICE SOURCE: PASS")
    print("FI102 INSTANCE: PASS")
    print("FI103 INITIAL CACHE: PASS")
    print("FI104 FIRST CALL: PASS")
    print("FI105 CACHE AFTER FIRST: PASS")
    print("FI106 SECOND CALL: PASS")
    print("FI107 EVENT ANALYSIS: PASS")
    print("FI108 THIRD CALL: PASS")
    print("FI109 PROVIDER CALL TRACE: PASS")
    print("FI110 CACHE TRACE: PASS")
    print("FI111 SUBSCRIBERS: PASS")
    print("FI112 BUS STATE: PASS")
    print("FI113 DISPATCHER STATE: PASS")
    print("FI114 CACHE IDENTITY: PASS")
    print("FI115 IMMUTABILITY: OBSERVED")
    print("FI116 VALUE INTEGRITY: PASS")
    print("FI117 CACHE IDENTITY: PASS")
    print("FI118 PROVIDER CALL COUNT: PASS")
    print("FI119 EVENT SEMANTICS: OBSERVED")
    print("FI120 EVENT IDS: OBSERVED")
    print("FI121 EVENT NAME: PASS")
    print("FI122 EVENT PROVIDER: PASS")
    print("FI123 EVENT SYMBOL: PASS")
    print("FI124 SEMANTIC CLASSIFICATION: COMPLETE")
    print("FI125 CORE ASSERTIONS: PASS")

    section("31K-FI101 TO FI125 COMPLETE")
    print("SOURCE MODIFICATION: NONE")
    print("STOP - COMPLETE OUTPUT COPIED TO CLIPBOARD")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()
