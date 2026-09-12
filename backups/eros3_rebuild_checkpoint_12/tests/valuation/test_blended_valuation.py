from services.financials.parser import parse_financial_statements, repository
from services.valuation.blended_engine import BlendedValuationEngine


def test_blended_valuation_engine() -> None:
    engine = BlendedValuationEngine()

    company_name = "Reliance Industries"
    ticker = "RELIANCE.NS"

    income = {
        "revenue": 100000.0,
        "ebitda": 20000.0,
        "netIncome": 10000.0,
        "eps": 10.0,
        "sharesOutstanding": 1000.0,
    }

    balance = {
        "cash": 10000.0,
        "totalAssets": 200000.0,
        "totalLiabilities": 100000.0,
        "totalEquity": 100000.0,
        "shortTermDebt": 20000.0,
        "longTermDebt": 40000.0,
    }

    cashflow = {
        "operatingCashFlow": 18000.0,
        "beginningCash": 9000.0,
        "changeInCash": 1000.0,
        "endingCash": 10000.0,
    }

    statements = parse_financial_statements(
        company_name=company_name,
        ticker=ticker,
        currency="INR",
        fiscal_year="FY2025",
        income_statement=income,
        balance_sheet=balance,
        cash_flow=cashflow,
    )

    projections = [13000.0, 14500.0, 16000.0, 18000.0, 20000.0]
    result = engine.evaluate(
        symbol=ticker,
        fcff_projections=projections,
        wacc=0.10,
        terminal_growth_rate=0.04,
        net_debt=50000.0,
        shares_outstanding=1000.0,
        current_price=1400.0,
        financials=statements,
    )

    assert result.symbol == ticker
    assert result.blended_fair_value > 0
    repository().clear()
