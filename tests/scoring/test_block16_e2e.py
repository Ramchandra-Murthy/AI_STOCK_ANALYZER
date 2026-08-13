from services.financials.financial_statement import (
    FinancialStatements,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
)
from services.market_data.models import PriceRecord
from services.risk_management.models import PortfolioRiskProfile
from services.scoring.engine import AIScoringEngine
from services.scoring.investment_decision import InvestmentDecisionOrchestrator

def test_block16e_e2e_strong_buy_allocation():
    income = IncomeStatement(
        revenue=250000.0, cost_of_goods_sold=120000.0, ebitda=65000.0,
        ebit=55000.0, net_income=42000.0, eps=42.0, shares_outstanding=1000.0,
    )
    balance = BalanceSheet(
        cash=50000.0, cash_equivalents=20000.0, accounts_receivable=30000.0,
        inventory=15000.0, total_assets=350000.0, total_liabilities=100000.0,
        total_equity=250000.0, short_term_debt=10000.0, long_term_debt=20000.0,
    )
    cashflow = CashFlowStatement(
        operating_cash_flow=48000.0, capital_expenditure=12000.0,
        beginning_cash=40000.0, net_change_in_cash=10000.0, ending_cash=50000.0,
    )
    statements = FinancialStatements(
        company_name="Infosys Limited", ticker="INFY.NS", currency="INR",
        fiscal_year="FY2025", income_statement=income, balance_sheet=balance,
        cash_flow_statement=cashflow, periods=[],
    )
    records = [
        PriceRecord(date=f"2026-06-{i+1:02d}", open=1700.0 + i * 5, high=1720.0 + i * 5, low=1690.0 + i * 5, close=1710.0 + i * 5, volume=2000000)
        for i in range(35)
    ]
    profile = PortfolioRiskProfile(
        portfolio_id="INFY-E2E-01", expected_volatility=0.15, value_at_risk=0.03,
        expected_shortfall=0.06, concentration_score=85.0, liquidity_score=92.0,
        diversification_score=88.0, resilience_score=94.0,
    )

    scoring_engine = AIScoringEngine()
    ai_score = scoring_engine.evaluate(statements, market_records=records, risk_profile=profile)
    orchestrator = InvestmentDecisionOrchestrator(policy_profile="Institutional", max_position_limit=0.10)
    decision = orchestrator.evaluate(ai_score, holdings=None, portfolio_weight=0.02)

    assert decision.symbol == "INFY.NS"
    assert decision.action in ["BUY", "STRONG BUY"]
    assert decision.composite_score == ai_score.composite_score
    assert decision.target_weight > 0.02
    assert decision.incremental_weight > 0.0
    assert decision.execution_cost > 0.0
    assert decision.net_expected_return < decision.expected_return
    assert decision.details["engine_version"] == "EROS-3.0-BLOCK-16D"
    assert "execution_details" in decision.details
    assert len(decision.details["execution_details"]["generated_orders"]) == 1

def test_block16e_e2e_concentration_downgrade():
    income = IncomeStatement(
        revenue=200000.0, cost_of_goods_sold=100000.0, ebitda=50000.0,
        ebit=40000.0, net_income=30000.0, eps=30.0, shares_outstanding=1000.0,
    )
    balance = BalanceSheet(
        cash=40000.0, cash_equivalents=10000.0, accounts_receivable=20000.0,
        inventory=10000.0, total_assets=300000.0, total_liabilities=100000.0,
        total_equity=200000.0, short_term_debt=10000.0, long_term_debt=20000.0,
    )
    cashflow = CashFlowStatement(
        operating_cash_flow=35000.0, capital_expenditure=10000.0,
        beginning_cash=30000.0, net_change_in_cash=5000.0, ending_cash=35000.0,
    )
    statements = FinancialStatements(
        company_name="Reliance Industries", ticker="RELIANCE.NS", currency="INR",
        fiscal_year="FY2025", income_statement=income, balance_sheet=balance,
        cash_flow_statement=cashflow, periods=[],
    )

    scoring_engine = AIScoringEngine()
    ai_score = scoring_engine.evaluate(statements)

    orchestrator = InvestmentDecisionOrchestrator(policy_profile="Institutional", max_position_limit=0.10)
    decision = orchestrator.evaluate(ai_score, holdings=None, portfolio_weight=0.18)

    assert decision.symbol == "RELIANCE.NS"
    assert decision.portfolio_weight == 0.18
    assert decision.action == "HOLD"
    assert decision.incremental_weight == 0.0
    assert decision.execution_cost == 0.0
