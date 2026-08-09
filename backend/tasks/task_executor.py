from __future__ import annotations
import logging
from typing import Dict, Any
from backend.tasks.task_context import TaskContext
from backend.services.valuation_service import ValuationService
from backend.database.engine import SessionLocal
from backend.database.repositories.forecast_report_repository import ForecastRepository, ReportRepository
from backend.database.repositories.forecast_report_repository import ForecastRepository
from services.forecasting.models import ForecastScenario
from services.forecasting.scenario_engine import ScenarioIntelligenceEngine
from services.report.engine import ReportEngine


logger = logging.getLogger(__name__)

class BackgroundWorkers:
    @staticmethod
    def execute_report_task(context: TaskContext) -> Dict[str, Any]:
        logger.info("Worker processing report task %s", context.task_id)
        symbol = context.payload.get("symbol", "TCS.NS")
        format_type = context.payload.get("format_type", "MULTI-FORMAT")
        analysis_data = context.payload.get("analysis_data", {})
        
        engine = ReportEngine()
        report = engine.generate(symbol=symbol, format_type=format_type, analysis_data=analysis_data)
        report_id = f"{symbol}-REPORT-2026-Q2"
        
        session = SessionLocal()
        try:
            saved_report = ReportRepository.save_report(
                session=session,
                report_id=report_id,
                symbol=report.symbol,
                report_type=report.format_type,
                content_summary=report.content,
            )
        finally:
            session.close()
            
        return {
            "status": "SUCCESS",
            "task_id": context.task_id,
            "symbol": report.symbol,
            "format_type": report.format_type,
            "file_path": report.file_path,
            "content": report.content,
            "metadata": report.metadata,
            "report_id": saved_report.id,
            "timestamp": context.payload.get("timestamp"),
        }
    @staticmethod
    def execute_forecast_task(context: TaskContext) -> Dict[str, Any]:
        logger.info("Worker processing forecast task %s", context.task_id)

        symbol = context.payload.get("symbol", "TCS.NS")

        scenarios = [
            ForecastScenario(
                scenario_id=f"{symbol}-BULL",
                name="BULL",
                probability=0.25,
                revenue_growth=0.15,
                margin=0.21,
                wacc=0.095,
                terminal_growth=0.045,
                inflation=0.04,
                interest_rate=0.065,
                intrinsic_value=float(
                    context.payload.get("bull_value", 3450.0)
                ),
                expected_return=0.22,
                risk_score=0.30,
            ),
            ForecastScenario(
                scenario_id=f"{symbol}-BASE",
                name="BASE",
                probability=0.50,
                revenue_growth=0.10,
                margin=0.18,
                wacc=0.10,
                terminal_growth=0.04,
                inflation=0.05,
                interest_rate=0.07,
                intrinsic_value=float(
                    context.payload.get("base_value", 2900.0)
                ),
                expected_return=0.15,
                risk_score=0.45,
            ),
            ForecastScenario(
                scenario_id=f"{symbol}-BEAR",
                name="BEAR",
                probability=0.25,
                revenue_growth=0.04,
                margin=0.14,
                wacc=0.115,
                terminal_growth=0.03,
                inflation=0.07,
                interest_rate=0.085,
                intrinsic_value=float(
                    context.payload.get("bear_value", 2100.0)
                ),
                expected_return=0.02,
                risk_score=0.70,
            ),
        ]

        forecast = ScenarioIntelligenceEngine.evaluate_scenarios(
            symbol=symbol,
            scenarios=scenarios,
        )

        record_id = f"{symbol}-FCST-2026-Q2"

        session = SessionLocal()
        try:
            ForecastRepository.save_forecast(
                session=session,
                record_id=record_id,
                symbol=symbol,
                revenue_cagr=scenarios[1].revenue_growth,
                eps_forecast=forecast.expected_value,
                confidence=forecast.confidence,
            )
        finally:
            session.close()

        return {
            "status": "SUCCESS",
            "task_id": context.task_id,
            "symbol": forecast.symbol,
            "expected_value": forecast.expected_value,
            "bull_value": forecast.bull_value,
            "base_value": forecast.base_value,
            "bear_value": forecast.bear_value,
            "confidence": forecast.confidence,
            "probability_distribution": forecast.probability_distribution,
            "key_drivers": forecast.key_drivers,
            "major_risks": forecast.major_risks,
            "assumptions": forecast.assumptions,
            "record_id": record_id,
            "timestamp": forecast.timestamp,
        }

    @staticmethod
    def execute_valuation_task(context: TaskContext) -> Dict[str, Any]:
        logger.info("Worker processing valuation task %s", context.task_id)
        session = SessionLocal()
        try:
            result = ValuationService.execute_and_persist_valuation(session, context.payload.get("symbol", "TCS.NS"), context.payload)
            return {"status": "SUCCESS", "task_id": context.task_id, "result": result}
        finally:
            session.close()

# The ultimate passthrough: ignores extra positional arguments injected by Celery
def celery_valuation_wrapper(*args, **kwargs) -> Dict[str, Any]:
    # We expect args to be (task_id, task_name, user, payload)
    # If Celery injects 'self' at args[0], we take the last 4
    if len(args) >= 4:
        task_id, task_name, user, payload = args[-4], args[-3], args[-2], args[-1]
    else:
        task_id, task_name, user, payload = "UNKNOWN", "valuation.execute", "system", {}
        
    context = TaskContext(task_id=task_id, task_name=task_name, user=user, payload=payload)
    return BackgroundWorkers.execute_valuation_task(context)

def celery_forecast_wrapper(*args, **kwargs) -> Dict[str, Any]:
    if len(args) >= 4:
        task_id, task_name, user, payload = args[-4:]
    else:
        task_id = kwargs.get("task_id", "UNKNOWN")
        task_name = kwargs.get("task_name", "forecast.execute")
        user = kwargs.get("user", "system")
        payload = kwargs.get("payload", {})

    context = TaskContext(
        task_id=task_id,
        task_name=task_name,
        user=user,
        payload=payload,
    )

    return BackgroundWorkers.execute_forecast_task(context)

def celery_report_wrapper(*args, **kwargs) -> Dict[str, Any]:
    if len(args) >= 4:
        task_id, task_name, user, payload = args[-4:]
    else:
        task_id = kwargs.get("task_id", "UNKNOWN")
        task_name = kwargs.get("task_name", "report.generate")
        user = kwargs.get("user", "system")
        payload = kwargs.get("payload", {})
    context = TaskContext(
        task_id=task_id,
        task_name=task_name,
        user=user,
        payload=payload,
    )
    return BackgroundWorkers.execute_report_task(context)



