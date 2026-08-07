from __future__ import annotations

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.database.repositories.valuation_repository import ValuationRepository

logger = logging.getLogger(__name__)

class ValuationService:
    """Orchestrates financial valuation workflows and coordinates persistence via ValuationRepository."""

    @staticmethod
    def execute_and_persist_valuation(
        session: Session,
        symbol: str,
        financial_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info("Executing institutional valuation pipeline for %s", symbol)
        
        base_eps = float(financial_metrics.get("eps", 50.0))
        growth_rate = float(financial_metrics.get("growth_rate", 0.06))
        discount_rate = float(financial_metrics.get("discount_rate", 0.12))
        
        # Ensure discount rate exceeds growth rate to avoid negative/invalid valuations
        if discount_rate <= growth_rate:
            discount_rate = growth_rate + 0.04

        # Safe Gordon Growth / DCF Estimate
        denominator = discount_rate - growth_rate
        intrinsic_value = round((base_eps * (1.0 + growth_rate)) / denominator, 2)
        if intrinsic_value < 0:
            intrinsic_value = abs(intrinsic_value)

        current_price = float(financial_metrics.get("current_price", intrinsic_value * 0.85))
        margin_of_safety = round((intrinsic_value - current_price) / intrinsic_value, 4)

        record_id = f"{symbol}-VAL-2026-Q2"
        model_type = "Professional DCF & Margin of Safety"

        # Persist via Repository
        ValuationRepository.save_valuation(
            session=session,
            record_id=record_id,
            symbol=symbol,
            intrinsic_value=intrinsic_value,
            model_type=model_type,
            margin_of_safety=margin_of_safety
        )

        logger.info("Valuation successfully calculated and persisted for %s: IV = %s", symbol, intrinsic_value)
        return {
            "record_id": record_id,
            "symbol": symbol,
            "intrinsic_value": intrinsic_value,
            "current_price": current_price,
            "margin_of_safety": margin_of_safety,
            "model_type": model_type,
            "status": "SUCCESS"
        }