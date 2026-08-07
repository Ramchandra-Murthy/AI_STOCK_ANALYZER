from __future__ import annotations

import logging
from typing import Optional
from sqlalchemy.orm import Session
from backend.database.models.company import ValuationRecordModel

logger = logging.getLogger(__name__)

class ValuationRepository:
    """Repository handling production database operations for valuation records using SQLAlchemy."""

    @staticmethod
    def save_valuation(session: Session, record_id: str, symbol: str, intrinsic_value: float, model_type: str, margin_of_safety: float) -> ValuationRecordModel:
        logger.info("Saving valuation record %s for symbol %s to database", record_id, symbol)
        record = ValuationRecordModel(
            id=record_id,
            symbol=symbol,
            intrinsic_value=intrinsic_value,
            model_type=model_type,
            margin_of_safety=margin_of_safety
        )
        session.merge(record)
        session.commit()
        return record

    @staticmethod
    def get_valuation(session: Session, record_id: str) -> Optional[ValuationRecordModel]:
        logger.info("Querying valuation record %s from database", record_id)
        return session.query(ValuationRecordModel).filter(ValuationRecordModel.id == record_id).first()
