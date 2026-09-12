from __future__ import annotations

from backend.database.engine import SessionLocal, init_db
from backend.database.repositories.valuation_repository import ValuationRepository


def test_sqlalchemy_production_persistence() -> None:
    init_db()
    session = SessionLocal()
    try:
        record_id = "TCS.NS-SQL-2026"
        symbol = "TCS.NS"

        saved = ValuationRepository.save_valuation(
            session=session,
            record_id=record_id,
            symbol=symbol,
            intrinsic_value=4150.0,
            model_type="Professional DCF",
            margin_of_safety=0.25,
        )
        assert saved.id == record_id
        assert saved.intrinsic_value == 4150.0

        retrieved = ValuationRepository.get_valuation(session, record_id)
        assert retrieved is not None
        assert retrieved.symbol == symbol
        assert retrieved.model_type == "Professional DCF"
    finally:
        session.close()
