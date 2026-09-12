from __future__ import annotations

import logging
from typing import Any

from services.alerts.models import InstitutionalAlert

logger = logging.getLogger(__name__)


class InstitutionalAlertEngine:
    """Evaluates real-time market and fundamental triggers, routing proactive alerts across institutional channels."""

    @staticmethod
    def evaluate_valuation_alert(
        symbol: str, intrinsic_value: float, market_price: float
    ) -> InstitutionalAlert | None:
        logger.info(
            "Evaluating valuation alert trigger for %s (Intrinsic: %.2f, Market: %.2f)",
            symbol,
            intrinsic_value,
            market_price,
        )

        discount = (intrinsic_value - market_price) / intrinsic_value
        if discount > 0.25:
            return InstitutionalAlert(
                symbol=symbol,
                alert_type="VALUATION_DISCOUNT",
                severity="HIGH",
                message=f"Valuation discount of {discount*100:.1f}% exceeds institutional threshold (25%)",
                metadata={"discount_pct": discount},
            )
        return None

    @staticmethod
    def route_notification(alert: InstitutionalAlert, target: str = "Dashboard") -> dict[str, Any]:
        logger.info(
            "Routing institutional alert for %s to notification target: %s", alert.symbol, target
        )
        return {
            "target": target,
            "delivered": True,
            "symbol": alert.symbol,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
        }
