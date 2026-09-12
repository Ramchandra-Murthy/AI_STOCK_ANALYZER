from services.financials.parser import (
    parse_financial_statements,
    repository,
)
from services.scoring.engine import AIScoringEngine


def test_block10_fundamental_scoring() -> None:
    income = {
        "revenue": 100000.0,
        "costOfRevenue": 60000.0,
        "ebitda": 20000.0,
        "ebit": 15000.0,
        "netIncome": 10000.0,
        "eps": 10.0,
        "sharesOutstanding": 1000.0,
    }
    balance = {
        "cash": 10000.0,
        "cashEquivalents": 2000.0,
        "accountsReceivable": 15000.0,
        "inventory": 10000.0,
        "totalAssets": 200000.0,
        "totalLiabilities": 100000.0,
        "totalEquity": 100000.0,
        "shortTermDebt": 20000.0,
        "longTermDebt": 40000.0,
    }
    cashflow = {
        "operatingCashFlow": 18000.0,
        "capitalExpenditure": 5000.0,
        "beginningCash": 9000.0,
        "changeInCash": 1000.0,
        "endingCash": 10000.0,
    }

    statements = parse_financial_statements(
        company_name="Reliance Industries",
        ticker="RELIANCE.NS",
        currency="INR",
        fiscal_year="FY2025",
        income_statement=income,
        balance_sheet=balance,
        cash_flow=cashflow,
    )

    engine = AIScoringEngine()
    result = engine.evaluate(statements)

    # --------------------------------------------------
    # Identity contract
    # --------------------------------------------------
    assert result.symbol == "RELIANCE.NS"

    # --------------------------------------------------
    # Score range contract
    # --------------------------------------------------
    assert 0.0 <= result.growth_score <= 100.0
    assert 0.0 <= result.quality_score <= 100.0
    assert 0.0 <= result.profitability_score <= 100.0
    assert 0.0 <= result.capital_allocation_score <= 100.0
    assert 0.0 <= result.valuation_score <= 100.0
    assert 0.0 <= result.momentum_score <= 100.0
    assert 0.0 <= result.risk_score <= 100.0
    assert 0.0 <= result.composite_score <= 100.0

    # --------------------------------------------------
    # Fundamental integration contract
    # --------------------------------------------------
    assert result.quality_score > 0.0
    assert result.profitability_score > 0.0
    assert result.capital_allocation_score > 0.0
    assert result.risk_score > 0.0

    # --------------------------------------------------
    # Audit payload contract
    # --------------------------------------------------
    details = result.breakdown_details
    # AIScoringEngine is the unified Block 15 engine.
    assert details["engine_version"] == "EROS-3.0-BLOCK-15"

    # Fundamental scoring remains independently versioned as Block 10.
    assert details["fundamental_engine"]["engine_version"] == "EROS-3.0-BLOCK-10"
    assert "fundamental_engine" in details
    assert "raw_ratios" in details
    assert "quality_components" in details["fundamental_engine"]
    assert "profitability_components" in details["fundamental_engine"]
    assert "capital_allocation_components" in details["fundamental_engine"]
    assert "ebitda_margin" in details["raw_ratios"]
    assert "roe" in details["raw_ratios"]
    assert "roic" in details["raw_ratios"]

    # --------------------------------------------------
    # Weight contract
    # --------------------------------------------------
    weights = details["weights_used"]
    assert abs(sum(weights.values()) - 1.0) < 1e-9

    repository().clear()
