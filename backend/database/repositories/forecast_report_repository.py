from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from backend.database.models.company import ForecastRecordModel, ReportRecordModel

logger = logging.getLogger(__name__)


class ForecastRepository:
    @staticmethod
    def save_forecast(
        session: Session,
        record_id: str,
        symbol: str,
        revenue_cagr: float,
        eps_forecast: float,
        confidence: float,
    ) -> ForecastRecordModel:
        logger.info("Persisting forecast record %s for symbol %s", record_id, symbol)
        forecast = ForecastRecordModel(
            id=record_id,
            symbol=symbol,
            revenue_cagr=revenue_cagr,
            eps_forecast=eps_forecast,
            confidence=confidence,
        )
        session.merge(forecast)
        session.commit()
        return forecast

    @staticmethod
    def get_forecast(session: Session, record_id: str) -> ForecastRecordModel | None:
        return (
            session.query(ForecastRecordModel).filter(ForecastRecordModel.id == record_id).first()
        )


class ReportRepository:
    @staticmethod
    def save_report(
        session: Session, report_id: str, symbol: str, report_type: str, content_summary: str
    ) -> ReportRecordModel:
        logger.info("Persisting report record %s for symbol %s", report_id, symbol)
        report = ReportRecordModel(
            id=report_id, symbol=symbol, report_type=report_type, content_summary=content_summary
        )
        session.merge(report)
        session.commit()
        return report

    @staticmethod
    def get_report(session: Session, report_id: str) -> ReportRecordModel | None:
        return session.query(ReportRecordModel).filter(ReportRecordModel.id == report_id).first()
