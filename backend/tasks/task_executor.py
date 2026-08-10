from __future__ import annotations
import logging
import os
from typing import Dict, Any
from backend.tasks.task_context import TaskContext
from backend.services.valuation_service import ValuationService
from backend.database.engine import SessionLocal
from backend.database.repositories.forecast_report_repository import ForecastRepository, ReportRepository
from services.forecasting.models import ForecastScenario
from services.forecasting.scenario_engine import ScenarioIntelligenceEngine
from services.report.engine import ReportEngine

logger = logging.getLogger(__name__)

class BackgroundWorkers:
    @staticmethod
    def execute_report_task(context: TaskContext) -> Dict[str, Any]:
        logger.info("Worker processing report task %s for user %s with payload: %s", context.task_id, context.user, context.payload)
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
            "task_id": str(context.task_id),
            "user": str(context.user),
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
        logger.info("Worker processing forecast task %s for user %s with payload: %s", context.task_id, context.user, context.payload)
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
                intrinsic_value=float(context.payload.get("bull_value", 3450.0)),
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
                intrinsic_value=float(context.payload.get("base_value", 2900.0)),
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
                intrinsic_value=float(context.payload.get("bear_value", 2100.0)),
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
            "task_id": str(context.task_id),
            "user": str(context.user),
            "symbol": forecast.symbol,
            "expected_value": forecast.expected_value,
            "bull_value": float(context.payload.get("bull_value", forecast.bull_value)),
            "base_value": float(context.payload.get("base_value", forecast.base_value)),
            "bear_value": float(context.payload.get("bear_value", forecast.bear_value)),
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
        logger.info("Worker processing valuation task %s for user %s with payload: %s", context.task_id, context.user, context.payload)
        session = SessionLocal()
        try:
            symbol = context.payload.get("symbol", "TCS.NS")
            result = ValuationService.execute_and_persist_valuation(session, symbol, context.payload)
            return {
                "status": "SUCCESS",
                "task_id": str(context.task_id),
                "user": str(context.user),
                "symbol": symbol,
                "result": result
            }
        finally:
            session.close()

def _extract_context(*args, **kwargs):
    task_id = "UNKNOWN"
    try:
        from celery import current_task
        if current_task and current_task.request and current_task.request.id:
            task_id = str(current_task.request.id)
    except Exception:
        pass

    if task_id == "UNKNOWN" and len(args) > 0 and hasattr(args[0], "request") and args[0].request and args[0].request.id:
        task_id = str(args[0].request.id)

    task_name = "forecast.execute"
    user = "system"
    payload = {}

    remaining_args = list(args[1:]) if len(args) > 1 else []
    
    if len(remaining_args) >= 2:
        if isinstance(remaining_args[0], str):
            task_name = remaining_args[0]
        if isinstance(remaining_args[1], str):
            user = remaining_args[1]
        if len(remaining_args) >= 3 and isinstance(remaining_args[2], dict):
            payload = remaining_args[2]
    else:
        for arg in remaining_args:
            if isinstance(arg, str):
                if "." in arg and len(arg) < 35:
                    task_name = arg
                else:
                    user = arg
            elif isinstance(arg, dict):
                payload = arg

    if "task_name" in kwargs:
        task_name = kwargs["task_name"]
    if "user" in kwargs:
        user = kwargs["user"]
    if "payload" in kwargs and isinstance(kwargs["payload"], dict):
        payload = kwargs["payload"]

    if task_id == "UNKNOWN":
        if isinstance(payload, dict) and "task_id" in payload:
            task_id = payload["task_id"]

    return str(task_id), str(task_name), str(user), payload

def celery_valuation_wrapper(*args, **kwargs) -> Dict[str, Any]:
    task_id, task_name, user, payload = _extract_context(*args, **kwargs)
    context = TaskContext(task_id=task_id, task_name=task_name, user=user, payload=payload)
    return BackgroundWorkers.execute_valuation_task(context)

def celery_forecast_wrapper(*args, **kwargs) -> Dict[str, Any]:
    task_id, task_name, user, payload = _extract_context(*args, **kwargs)
    context = TaskContext(task_id=task_id, task_name=task_name, user=user, payload=payload)
    res = BackgroundWorkers.execute_forecast_task(context)
    res["task_id"] = task_id
    res["user"] = user
    return res

def celery_report_wrapper(*args, **kwargs) -> Dict[str, Any]:
    task_id, task_name, user, payload = _extract_context(*args, **kwargs)
    context = TaskContext(task_id=task_id, task_name=task_name, user=user, payload=payload)
    res = BackgroundWorkers.execute_report_task(context)
    res["task_id"] = task_id
    res["user"] = user
    return res
