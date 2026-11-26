from services.financials.normalization import normalize_financial_statements
from services.financials.repository import FinancialStatementRepository

repo = FinancialStatementRepository()

fs = normalize_financial_statements(
    company_name="State Bank of India",
    ticker="SBIN.NS",
    currency="INR",
    fiscal_year="FY2026",
    income_raw={"totalRevenue": 380000.0, "sharesOutstanding": 8920.0},
    balance_raw={
        "totalAssets": 6000000.0,
        "totalLiabilities": 5600000.0,
        "shareholdersEquity": 400000.0,
    },
    cashflow_raw={"operatingCashFlow": 45000.0},
    )
fs.metadata.update(
    {
        "period_type": "FY",
        "source_type": "manual_demo",
    }
)

print("=== SQLITE REPOSITORY VERIFICATION ===")

record_id = repo.save(fs)
print(f"Saved record: {record_id} | {fs.company_name} ({fs.fiscal_year})")

loaded = repo.get("State Bank of India", "FY2026")
print(
    f"Loaded: {loaded.company_name} | "
    f"Assets: ₹{loaded.balance_sheet.total_assets:,.2f}"
)

versions = repo.list_versions("State Bank of India", "FY2026")
print(f"Preserved versions: {[item['version'] for item in versions]}")

latest_statements = repo.list(ticker="SBIN.NS")
print(f"Latest statement packages for SBIN.NS: {len(latest_statements)}")
