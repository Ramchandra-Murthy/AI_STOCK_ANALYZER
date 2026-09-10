from __future__ import annotations

import logging
from typing import Any

from api.routes.health import get_health
from api.routes.workflow import run_workflow

logger = logging.getLogger(__name__)


class EROSAPIApp:
    """Enterprise API Gateway for EROS Institutional Research Platform."""

    @staticmethod
    def health_check() -> dict[str, Any]:
        response = get_health()
        return {"success": response.success, "version": response.version, "data": response.data}

    @staticmethod
    def trigger_workflow(symbol: str) -> dict[str, Any]:
        response = run_workflow(symbol)
        return {
            "success": response.success,
            "run_id": response.data.get("run_id"),
            "completed_steps": response.data.get("completed_steps"),
            "reports_generated": response.data.get("reports_generated"),
        }
