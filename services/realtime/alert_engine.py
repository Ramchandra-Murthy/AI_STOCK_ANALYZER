from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class InstitutionalAlert:
    alert_id: str
    symbol: str
    severity: str # "HIGH", "MEDIUM", "LOW"
    category: str # "VALUATION", "RISK", "COMPLIANCE"
    message: str
    suggested_action: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

class RealTimeAlertEngine:
    """Real-time alert engine monitoring live portfolio and market conditions for threshold breaches."""

    @staticmethod
    def evaluate_alert(symbol: str, current_price: float, intrinsic_value: float) -> InstitutionalAlert | None:
        logger.info("Evaluating real-time alerts for %s (Price: %s, Intrinsic Value: %s)", symbol, current_price, intrinsic_value)
        
        if current_price < intrinsic_value * 0.75:
            return InstitutionalAlert(
                alert_id=f"ALT-{symbol}-VAL",
                symbol=symbol,
                severity="HIGH",
                category="VALUATION",
                message=f"Stock {symbol} is trading at ₹{current_price}, representing a >25% discount to intrinsic value ₹{intrinsic_value}.",
                suggested_action="Increase portfolio weight toward target maximum."
            )
        return None
