from __future__ import annotations

import pytest
from backend.database.engine import init_db, SessionLocal
from backend.database.repositories.forecast_report_repository import ForecastRepository, ReportRepository

def test_forecast_and_report_repositories() -> None:
    init_db()
    session = SessionLocal()
    try:
        # Test Forecast Repository
        forecast = ForecastRepository.save_forecast(
            session=session,
            record_id="FCST-RELIANCE-2026",
            symbol="RELIANCE.NS",
            revenue_cagr=0.145,
            eps_forecast=125.50,
            confidence=0.88
        )
        assert forecast.id == "FCST-RELIANCE-2026"
        fetched_fcst = ForecastRepository.get_forecast(session, "FCST-RELIANCE-2026")
        assert fetched_fcst is not None
        assert fetched_fcst.revenue_cagr == 0.145

        # Test Report Repository
        report = ReportRepository.save_report(
            session=session,
            report_id="REP-RELIANCE-Q4",
            symbol="RELIANCE.NS",
            report_type="Institutional Valuation Summary",
            content_summary="Strong operating margins across retail and O2C segments with robust DCF valuation support."
        )
        assert report.id == "REP-RELIANCE-Q4"
        fetched_rep = ReportRepository.get_report(session, "REP-RELIANCE-Q4")
        assert fetched_rep is not None
        assert fetched_rep.report_type == "Institutional Valuation Summary"
    finally:
        session.close()