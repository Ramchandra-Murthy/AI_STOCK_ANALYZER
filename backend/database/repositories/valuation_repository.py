from __future__ import annotations

import logging
from typing import Optional
from sqlalchemy.orm import Session
from backend.database.models.company import ValuationRecordModel

logger = logging.getLogger(__name__)

class ValuationRepository:
    """Canonical repository for persisting and retrieving valuation records."""

    @staticmethod
    def save_valuation(
        session: Session,
        record_id: str,
        symbol: str,
        intrinsic_value: float,
        model_type: str,
        margin_of_safety: float
    ) -> ValuationRecordModel:
        logger.info("Persisting valuation record %s for symbol %s", record_id, symbol)
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
        return session.query(ValuationRecordModel).filter(ValuationRecordModel.id == record_id).first()