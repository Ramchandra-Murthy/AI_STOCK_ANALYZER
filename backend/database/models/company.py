from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, String

from backend.database.engine import Base


class CompanyModel(Base):
    __tablename__ = "companies"

    symbol = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sector = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ValuationRecordModel(Base):
    __tablename__ = "valuations"

    id = Column(String, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    intrinsic_value = Column(Float, nullable=False)
    model_type = Column(String, nullable=False)
    margin_of_safety = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ForecastRecordModel(Base):
    __tablename__ = "forecasts"

    id = Column(String, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    revenue_cagr = Column(Float, nullable=False)
    eps_forecast = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PortfolioRecordModel(Base):
    __tablename__ = "portfolios"

    id = Column(String, primary_key=True, index=True)
    strategy_name = Column(String, nullable=False)
    expected_return = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReportRecordModel(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    report_type = Column(String, nullable=False)
    content_summary = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
