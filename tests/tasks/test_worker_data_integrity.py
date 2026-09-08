import pytest

from backend.exceptions import ValidationError
from backend.tasks.task_context import TaskContext
from backend.tasks.task_executor import BackgroundWorkers


def test_forecast_worker_rejects_missing_scenario_values():
    context = TaskContext(
        task_id="integrity-forecast-1",
        task_name="forecast.execute",
        user="integrity",
        workflow_id=None,
        payload={"symbol": "TCS.NS"},
    )
    with pytest.raises(ValidationError):
        BackgroundWorkers.execute_forecast_task(context)


def test_valuation_worker_rejects_missing_symbol():
    context = TaskContext(
        task_id="integrity-valuation-1",
        task_name="valuation.execute",
        user="integrity",
        workflow_id=None,
        payload={},
    )
    with pytest.raises(ValidationError):
        BackgroundWorkers.execute_valuation_task(context)
