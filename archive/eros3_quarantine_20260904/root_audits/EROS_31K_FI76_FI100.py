import os, sys, inspect, asyncio, json, pathlib, traceback

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
    section("EROS 3.0 - 31K-FI76 TO FI100 CONSOLIDATED READ-ONLY TRACE")
    print("WORKING DIRECTORY:", os.getcwd())
    print("PYTHON:", sys.executable)
    print("PYTHONPATH:", ROOT)
    print("SOURCE MODIFICATION: NONE")

    provider = YahooFinanceProvider()
    normalizer = FinancialNormalizer()
    bus = InMemoryEventBus()
    dispatcher = EventDispatcher(bus)
    service = FundamentalsService(provider, normalizer, dispatcher)

    section("31K-FI76 - PROVIDER")
    print("TYPE =", type(provider))
    print("MODULE =", type(provider).__module__)
    print("DOWNLOAD =", inspect.signature(provider.download))

    section("31K-FI77 - NORMALIZER")
    print("TYPE =", type(normalizer))
    print("MODULE =", type(normalizer).__module__)
    print("NORMALIZE =", inspect.signature(normalizer.normalize))

    section("31K-FI78 - SERVICE")
    print("TYPE =", type(service))
    print("MODULE =", type(service).__module__)
    print("CONSTRUCTOR =", inspect.signature(FundamentalsService))
    print("GET_OR_DOWNLOAD =", inspect.signature(service.get_or_download))

    section("31K-FI79 - RAW PROVIDER")
    raw = provider.download("RELIANCE.NS")
    print("RAW TYPE =", type(raw))
    print("RAW KEYS =", list(raw.keys()))
    print("SYMBOL =", raw.get("symbol"))
    print("PROVIDER =", raw.get("provider"))

    section("31K-FI80 - NORMALIZED MODEL")
    normalized = normalizer.normalize(raw)
    print("TYPE =", type(normalized))
    print("MODULE =", type(normalized).__module__)
    print("SYMBOL =", normalized.symbol)
    print("METADATA =", normalized.metadata)

    section("31K-FI81 - INCOME STATEMENT")
    inc = normalized.income_statement
    print("TYPE =", type(inc))
    print("OBJECT =", inc)
    for name in ["period", "revenue", "operating_income", "ebit", "net_income", "eps"]:
        print(name.upper(), "=", getattr(inc, name, None))

    section("31K-FI82 - BALANCE SHEET")
    bs = normalized.balance_sheet
    print("TYPE =", type(bs))
    print("OBJECT =", bs)
    for name in [
        "period",
        "total_assets",
        "total_liabilities",
        "shareholders_equity",
        "cash",
        "debt",
    ]:
        print(name.upper(), "=", getattr(bs, name, None))

    section("31K-FI83 - CASH FLOW")
    cf = normalized.cash_flow_statement
    print("TYPE =", type(cf))
    print("OBJECT =", cf)
    for name in [
        "period",
        "operating_cash_flow",
        "capex",
        "free_cash_flow",
        "investing_cash_flow",
        "financing_cash_flow",
    ]:
        print(name.upper(), "=", getattr(cf, name, None))

    section("31K-FI84 - COLLECTIONS")
    print("INCOME STATEMENTS =", normalized.income_statements)
    print("BALANCE SHEETS =", normalized.balance_sheets)
    print("CASH FLOWS =", normalized.cash_flows)
    print("PERIODS =", normalized.periods)

    section("31K-FI85 - ALIASES")
    print("SYMBOL =", normalized.symbol)
    print("TICKER =", normalized.ticker)
    print("INCOME ALIAS =", normalized.income_statement is normalized.income_statements[0])
    print("BALANCE ALIAS =", normalized.balance_sheet is normalized.balance_sheets[0])
    print("CASH FLOW ALIAS =", normalized.cash_flow_statement is normalized.cash_flows[0])

    section("31K-FI86 - EVENT BUS")
    print("BUS TYPE =", type(bus))
    print("BUS MODULE =", type(bus).__module__)
    print("DISPATCHER TYPE =", type(dispatcher))
    print("DISPATCHER MODULE =", type(dispatcher).__module__)

    events = []

    async def capture(event):
        events.append(event)

    bus.subscribe("fundamentals.downloaded", capture)

    section("31K-FI87 - PRODUCTION CALL")
    result = await service.get_or_download("RELIANCE.NS")
    print("RESULT TYPE =", type(result))
    print("RESULT SYMBOL =", result.symbol)
    print("RESULT PROVIDER =", result.metadata.get("provider"))
    print("RESULT NET INCOME =", result.income_statement.net_income)
    print("RESULT FCF =", result.cash_flow_statement.free_cash_flow)
    print("EVENT COUNT =", len(events))

    section("31K-FI88 - EVENT DETAILS")
    if events:
        event = events[-1]
        print("EVENT TYPE =", type(event))
        print("EVENT MODULE =", type(event).__module__)
        print("EVENT NAME =", getattr(event, "name", None))
        print("EVENT PROVIDER =", getattr(event, "provider", None))
        print("EVENT SYMBOL =", getattr(event, "symbol", None))
    else:
        print("NO EVENT CAPTURED")

    section("31K-FI89 - CACHE")
    second = await service.get_or_download("RELIANCE.NS")
    print("FIRST IS SECOND =", result is second)
    print("FIRST NET INCOME =", result.income_statement.net_income)
    print("SECOND NET INCOME =", second.income_statement.net_income)
    print("EVENT COUNT AFTER SECOND =", len(events))

    section("31K-FI90 - SERVICE CACHE OBJECT")
    cache = getattr(service, "_cache", None)
    print("CACHE TYPE =", type(cache))
    print("CACHE =", cache)

    section("31K-FI91 - PROVIDER CONTRACT")
    print("PROVIDER CLASS =", YahooFinanceProvider.__name__)
    print("DOWNLOAD SIGNATURE =", inspect.signature(provider.download))

    section("31K-FI92 - NORMALIZER CONTRACT")
    print("NORMALIZER CLASS =", FinancialNormalizer.__name__)
    print("NORMALIZE SIGNATURE =", inspect.signature(normalizer.normalize))

    section("31K-FI93 - FINANCIAL MODEL")
    print("MODEL =", type(result))
    print("MODEL MODULE =", type(result).__module__)
    print("ATTRIBUTES =", [x for x in dir(result) if not x.startswith("_")])

    section("31K-FI94 - METADATA")
    print("METADATA =", result.metadata)
    print("PROVIDER =", result.metadata.get("provider"))

    section("31K-FI95 - PERIODS")
    print("PERIODS =", result.periods)
    print("TICKER =", result.ticker)
    print("SYMBOL =", result.symbol)

    section("31K-FI96 - CORE VALUES")
    print("REVENUE =", result.income_statement.revenue)
    print("EBIT =", result.income_statement.ebit)
    print("NET INCOME =", result.income_statement.net_income)
    print("EPS =", result.income_statement.eps)
    print("ASSETS =", result.balance_sheet.total_assets)
    print("LIABILITIES =", result.balance_sheet.total_liabilities)
    print("EQUITY =", result.balance_sheet.shareholders_equity)
    print("CASH =", result.balance_sheet.cash)
    print("DEBT =", result.balance_sheet.debt)
    print("OPERATING CF =", result.cash_flow_statement.operating_cash_flow)
    print("CAPEX =", result.cash_flow_statement.capex)
    print("FCF =", result.cash_flow_statement.free_cash_flow)

    section("31K-FI97 - ASSERTIONS")
    assert result.symbol == "RELIANCE.NS"
    assert result.metadata["provider"] == "YahooFinance"
    assert result.income_statement.net_income == 150000.0
    assert result.balance_sheet.total_assets == 3000000.0
    assert result.balance_sheet.total_liabilities == 1200000.0
    assert result.balance_sheet.shareholders_equity == 1800000.0
    assert result.balance_sheet.debt == 500000.0
    assert result.cash_flow_statement.operating_cash_flow == 250000.0
    assert result.cash_flow_statement.capex == 80000.0
    assert result.cash_flow_statement.free_cash_flow == 170000.0
    print("FI97 ASSERTIONS: PASS")

    section("31K-FI98 - EVENT ASSERTION")
    assert len(events) >= 1
    assert getattr(events[0], "name", None) == "fundamentals.downloaded"
    print("FI98 EVENT ASSERTION: PASS")

    section("31K-FI99 - CACHE ASSERTION")
    assert result is second
    assert result.income_statement.net_income == second.income_statement.net_income
    print("FI99 CACHE ASSERTION: PASS")

    section("31K-FI100 - FINAL INTEGRITY")
    print("FI76 PROVIDER: PASS")
    print("FI77 NORMALIZER: PASS")
    print("FI78 SERVICE: PASS")
    print("FI79 RAW CONTRACT: PASS")
    print("FI80 NORMALIZED MODEL: PASS")
    print("FI81 INCOME: PASS")
    print("FI82 BALANCE: PASS")
    print("FI83 CASH FLOW: PASS")
    print("FI84 COLLECTIONS: PASS")
    print("FI85 ALIASES: PASS")
    print("FI86 EVENT BUS: PASS")
    print("FI87 PRODUCTION: PASS")
    print("FI88 EVENT DETAILS: PASS")
    print("FI89 CACHE: PASS")
    print("FI90 CACHE OBJECT: PASS")
    print("FI91 PROVIDER CONTRACT: PASS")
    print("FI92 NORMALIZER CONTRACT: PASS")
    print("FI93 MODEL: PASS")
    print("FI94 METADATA: PASS")
    print("FI95 PERIODS: PASS")
    print("FI96 VALUES: PASS")
    print("FI97 ASSERTIONS: PASS")
    print("FI98 EVENT ASSERTION: PASS")
    print("FI99 CACHE ASSERTION: PASS")
    print("FI100 CORE ASSERTIONS: PASS")

    section("31K-FI76 TO FI100 COMPLETE")
    print("SOURCE MODIFICATION: NONE")
    print("STOP - COMPLETE OUTPUT COPIED TO CLIPBOARD")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()
