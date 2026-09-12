from __future__ import annotations

from backend.database.engine import SessionLocal, init_db
from backend.database.repositories.company_repository import CompanyRepository, PortfolioRepository


def test_expanded_repositories_persistence() -> None:
    init_db()
    session = SessionLocal()
    try:
        # Test Company Repository
        company = CompanyRepository.save_company(
            session, "RELIANCE.NS", "Reliance Industries Limited", "Energy"
        )
        assert company.symbol == "RELIANCE.NS"
        fetched_company = CompanyRepository.get_company(session, "RELIANCE.NS")
        assert fetched_company is not None
        assert fetched_company.name == "Reliance Industries Limited"

        # Test Portfolio Repository
        portfolio = PortfolioRepository.save_portfolio(
            session, "PORT-INST-01", "Institutional Multi-Factor", 0.175
        )
        assert portfolio.id == "PORT-INST-01"
        fetched_portfolio = PortfolioRepository.get_portfolio(session, "PORT-INST-01")
        assert fetched_portfolio is not None
        assert fetched_portfolio.expected_return == 0.175
    finally:
        session.close()
