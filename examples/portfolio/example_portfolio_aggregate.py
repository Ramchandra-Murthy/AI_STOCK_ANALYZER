from __future__ import annotations
from decimal import Decimal
from core.primitives import Money, Quantity, Currency
from core.identifiers import CompanySymbol, ISIN
from portfolio.domain import Position, Portfolio
from core.serialization import JsonSerializer

def run_example() -> None:
    print("--- PORTFOLIO-003: Portfolio Aggregate Example ---")
    pos = Position(
        symbol=CompanySymbol("INFY"),
        isin=ISIN("INE009A01021"),
        quantity=Quantity(Decimal("200")),
        average_cost=Money(Decimal("1500.00"), Currency.INR),
        current_price=Money(Decimal("1650.00"), Currency.INR)
    )

    portfolio = Portfolio(
        name="Flagship Tech Portfolio",
        currency=Currency.INR,
        positions=(pos,)
    )

    print(f"Portfolio: {portfolio.name}")
    print(f"Total Value: {portfolio.total_market_value().amount} {portfolio.currency}")
    print("Serialized Portfolio:\n", JsonSerializer.serialize(portfolio))

if __name__ == "__main__":
    run_example()

