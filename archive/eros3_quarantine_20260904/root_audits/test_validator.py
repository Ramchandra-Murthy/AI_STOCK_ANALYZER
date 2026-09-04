import pytest

from services.financials.normalization import normalize_financial_statements
from services.financials.validator import validate_financial_statements


def test_valid_financial_statements_pass_validation():
    valid_fs = normalize_financial_statements(
        company_name="Tata Consultancy Services",
        ticker="TCS.NS",
        currency="INR",
        fiscal_year="FY2026",
        income_raw={
            "totalRevenue": 240000.0,
            "sharesOutstanding": 3600.0,
        },
        balance_raw={
            "totalAssets": 150000.0,
            "totalLiabilities": 50000.0,
            "totalEquity": 100000.0,
        },
        cashflow_raw={
            "operatingCashFlow": 40000.0,
        },
    )

    validate_financial_statements(valid_fs)


def test_broken_accounting_identity_is_rejected():
    invalid_fs = normalize_financial_statements(
        company_name="Corrupt Data Corp",
        ticker="BAD.NS",
        currency="INR",
        fiscal_year="FY2026",
        income_raw={
            "totalRevenue": 100.0,
            "sharesOutstanding": 10.0,
        },
        balance_raw={
            "totalAssets": 1000.0,
            "totalLiabilities": 400.0,
            "totalEquity": 500.0,
        },
        cashflow_raw={},
    )

    with pytest.raises(ValueError) as exc:
        validate_financial_statements(invalid_fs)

    assert "accounting" in str(exc.value).lower() or \
           "asset" in str(exc.value).lower()


def test_validator_contract_imports():
    assert callable(normalize_financial_statements)
    assert callable(validate_financial_statements)
