from backend.valuation.sotp import SOTPValuationEngine
from backend.valuation.adapter import adapt_sotp_to_valuation_payload

engine = SOTPValuationEngine(
    symbol="RELIANCE.NS",
    segments=[
        {"name": "Digital Services", "valuation": 850000.0},
        {"name": "Retail", "valuation": 650000.0},
        {"name": "O2C", "valuation": 900000.0}
    ],
    net_debt=250000.0,
    non_operating_assets=100000.0,
    shares_outstanding=6765.0
)

payload = adapt_sotp_to_valuation_payload(engine, "institutional_research_user")
print("ADAPTER PAYLOAD SUCCESS:")
for k, v in payload.items():
    print(f"  {k}: {v}")
