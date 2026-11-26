from __future__ import annotations

import pytest

from core.exceptions import RepositoryError, ValidationError
from services.financials.builders import build_dcf_input
from services.financials.financial_statement import (
    BalanceSheet,
    CashFlowStatement,
    FinancialStatements,
    IncomeStatement,
)
from services.financials.repository import FinancialStatementRepository
from services.financials.validator import validate_financial_statements


@pytest.fixture
def valid_financial_statements() -> FinancialStatements:
    income = IncomeStatement(
        revenue=220000.0,
        cost_of_goods_sold=150000.0,
        operating_expenses=32000.0,
        depreciation_and_amortization=4000.0,
        tax_expense=7000.0,
        net_income=24000.0,
        shares_outstanding=140.0,
    )
    balance = BalanceSheet(
        cash_equivalents=15000.0,
        accounts_receivable=35000.0,
        inventory=20000.0,
        other_current_assets=10000.0,
        total_current_assets=80000.0,
        property_plant_equipment=120000.0,
        other_non_current_assets=20000.0,
        total_non_current_assets=140000.0,
        total_assets=220000.0,
        accounts_payable=30000.0,
        short_term_debt=10000.0,
        other_current_liabilities=10000.0,
        total_current_liabilities=50000.0,
        long_term_debt=40000.0,
        other_non_current_liabilities=10000.0,
        total_non_current_liabilities=50000.0,
        total_liabilities=100000.0,
        share_capital=2800.0,
        retained_earnings=117200.0,
        total_equity=120000.0,
    )
    cash_flow = CashFlowStatement(
        operating_cash_flow=28000.0,
        capital_expenditure=-8000.0,
        financing_cash_flow=-10000.0,
    )
    return FinancialStatements(
        company_name="Larsen & Toubro",
        ticker="LT.NS",
        fiscal_year="FY2025",
        currency="INR",
        income_statement=income,
        balance_sheet=balance,
        cash_flow_statement=cash_flow,
        metadata={
            "period_end": "2025-03-31",
            "period_type": "FY",
            "source_provider": "fixture",
            "source_type": "test",
        },
    )


def test_financial_statement_validation_success(valid_financial_statements):
    validate_financial_statements(valid_financial_statements)


def test_financial_statement_validation_unbalanced_failure(valid_financial_statements):
    valid_financial_statements.balance_sheet.total_assets += 5000.0
    with pytest.raises((ValueError, ValidationError)):
        validate_financial_statements(valid_financial_statements)


def test_dcf_builder_contract(valid_financial_statements):
    dcf_in = build_dcf_input(valid_financial_statements)
    assert dcf_in.company_name == "Larsen & Toubro"
    assert dcf_in.tax_rate == 0.25


def test_repository_lifecycle(valid_financial_statements, tmp_path):
    repo = FinancialStatementRepository(tmp_path / "financials.sqlite3")
    record_id = repo.save(valid_financial_statements)
    assert record_id > 0
    assert repo.exists("Larsen & Toubro", "FY2025")

    # A new repository instance must read the committed data from disk.
    reopened = FinancialStatementRepository(tmp_path / "financials.sqlite3")
    retrieved = reopened.get("Larsen & Toubro", "FY2025")
    assert retrieved.ticker == "LT.NS"
    assert retrieved.metadata["period_end"] == "2025-03-31"
    assert reopened.list_versions("Larsen & Toubro", "FY2025")[0]["version"] == 1


def test_repository_preserves_prior_versions(valid_financial_statements, tmp_path):
    repo = FinancialStatementRepository(tmp_path / "financials.sqlite3")
    first_id = repo.save(valid_financial_statements)

    revised = FinancialStatements(
        company_name=valid_financial_statements.company_name,
        ticker=valid_financial_statements.ticker,
        currency=valid_financial_statements.currency,
        fiscal_year=valid_financial_statements.fiscal_year,
        income_statement=IncomeStatement(
            **{
                **valid_financial_statements.income_statement.__dict__
            }
        ),
        balance_sheet=valid_financial_statements.balance_sheet,
        cash_flow_statement=valid_financial_statements.cash_flow_statement,
        metadata={
            **valid_financial_statements.metadata,
            "source_reference": "restated-filing",
        },
    )
    revised.income_statement.revenue = 225000.0
    second_id = repo.save(revised)

    assert second_id > first_id
    versions = repo.list_versions("Larsen & Toubro", "FY2025")
    assert [item["version"] for item in versions] == [2, 1]
    assert repo.get("Larsen & Toubro", "FY2025").income_statement.revenue == 225000.0


def test_repository_rejects_unknown_period_type(valid_financial_statements, tmp_path):
    repo = FinancialStatementRepository(tmp_path / "financials.sqlite3")
    valid_financial_statements.metadata["period_type"] = "MONTHLY"
    with pytest.raises(RepositoryError):
        repo.save(valid_financial_statements)
