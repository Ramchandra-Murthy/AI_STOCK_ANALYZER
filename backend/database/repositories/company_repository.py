from __future__ import annotations

import logging
from typing import Optional
from sqlalchemy.orm import Session
from backend.database.models.company import CompanyModel, PortfolioModel = PortfolioRecordModel, ForecastRecordModel

logger = logging.getLogger(__name__)

class CompanyRepository:
    @staticmethod
    def save_company(session: Session, symbol: str, name: str, sector: Optional[str] = None) -> CompanyModel:
        logger.info("Persisting company entity for %s", symbol)
        company = CompanyModel(symbol=symbol, name=name, sector=sector)
        session.merge(company)
        session.commit()
        return company

    @staticmethod
    def get_company(session: Session, symbol: str) -> Optional[CompanyModel]:
        return session.query(CompanyModel).filter(CompanyModel.symbol == symbol).first()

class PortfolioRepository:
    @staticmethod
    def save_portfolio(session: Session, portfolio_id: str, strategy_name: str, expected_return: float) -> PortfolioRecordModel:
        logger.info("Persisting portfolio entity for %s", portfolio_id)
        portfolio = PortfolioRecordModel(id=portfolio_id, strategy_name=strategy_name, expected_return=expected_return)
        session.merge(portfolio)
        session.commit()
        return portfolio

    @staticmethod
    def get_portfolio(session: Session, portfolio_id: str) -> Optional[PortfolioRecordModel]:
        return session.query(PortfolioRecordModel).filter(PortfolioRecordModel.id == portfolio_id).first()