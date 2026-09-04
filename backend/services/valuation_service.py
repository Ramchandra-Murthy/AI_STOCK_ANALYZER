from __future__ import annotations

import math

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.database.repositories.valuation_repository import ValuationRepository
from backend.valuation.sotp import SOTPValuationEngine
from backend.valuation.adapter import adapt_sotp_to_valuation_payload
from backend.exceptions import ValidationError, ValuationError

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

        segments = financial_metrics.get("segments")
        
        # Check if SOTP payload parameters are provided
        if segments is not None:
            if not isinstance(segments, list) or len(segments) == 0:
                raise ValidationError("SOTP valuation requires a non-empty list of segments.")
            
            for idx, seg in enumerate(segments):
                if not isinstance(seg, dict) or "name" not in seg or "valuation" not in seg:
                    raise ValidationError(f"Segment at index {idx} must be a dictionary containing 'name' and 'valuation'.")
                val = seg.get("valuation")
                if (
                    isinstance(val, bool)
                    or not isinstance(val, (int, float))
                    or not math.isfinite(val)
                    or val < 0
                ):
                    raise ValidationError(
                        f"Segment '{seg.get('name')}' has an invalid or negative valuation: {val}."
                    )

            shares = financial_metrics.get("shares_outstanding", 1.0)
            if (
                isinstance(shares, bool)
                or not isinstance(shares, (int, float))
                or not math.isfinite(shares)
                or shares <= 0
            ):
                raise ValidationError(
                    "Shares outstanding must be a finite number greater than zero for SOTP valuation."
                )

            net_debt = financial_metrics.get("net_debt", 0.0)
            non_op = financial_metrics.get("non_operating_assets", 0.0)

            for field_name, value in (
                ("net_debt", net_debt),
                ("non_operating_assets", non_op),
            ):
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                ):
                    raise ValidationError(
                        f"{field_name} must be a finite numeric value for SOTP valuation."
                    )

            net_debt = float(net_debt)
            non_op = float(non_op)
            shares = float(shares)

            engine = SOTPValuationEngine(
                symbol=symbol,
                segments=segments,
                net_debt=net_debt,
                non_operating_assets=non_op,
                shares_outstanding=shares
            )

            user = financial_metrics.get("user", "institutional_research_user")
            sotp_payload = adapt_sotp_to_valuation_payload(engine, user)

            intrinsic_value = sotp_payload["base_value"]
            # SOTP must produce strictly positive equity value.
            # Non-positive equity cannot produce a valid intrinsic value.
            if intrinsic_value <= 0:
                raise ValidationError(
                    f"SOTP valuation produced non-positive equity value: {intrinsic_value}."
                )
            current_price = float(financial_metrics.get("current_price", intrinsic_value * 0.85))
            margin_of_safety = round((intrinsic_value - current_price) / intrinsic_value, 4) if intrinsic_value > 0 else 0.0

            record_id = sotp_payload["record_id"]
            model_type = "Sum-of-the-Parts (SOTP) Valuation"

            ValuationRepository.save_valuation(
                session=session,
                record_id=record_id,
                symbol=symbol,
                intrinsic_value=intrinsic_value,
                model_type=model_type,
                margin_of_safety=margin_of_safety
            )

            logger.info("SOTP Valuation successfully calculated and persisted for %s: IV = %s", symbol, intrinsic_value)
            return {
                "record_id": record_id,
                "symbol": symbol,
                "intrinsic_value": intrinsic_value,
                "current_price": current_price,
                "margin_of_safety": margin_of_safety,
                "model_type": model_type,
                "status": "SUCCESS"
            }

        # Fallback to standard DCF valuation flow only when segments is None
        base_eps = float(financial_metrics.get("eps", 50.0))
        growth_rate = float(financial_metrics.get("growth_rate", 0.06))
        discount_rate = float(financial_metrics.get("discount_rate", 0.12))

        if discount_rate <= growth_rate:
            discount_rate = growth_rate + 0.04

        denominator = discount_rate - growth_rate
        intrinsic_value = round((base_eps * (1.0 + growth_rate)) / denominator, 2)
        if intrinsic_value < 0:
            intrinsic_value = abs(intrinsic_value)

        current_price = float(financial_metrics.get("current_price", intrinsic_value * 0.85))
        margin_of_safety = round((intrinsic_value - current_price) / intrinsic_value, 4)

        record_id = f"{symbol}-VAL-2026-Q2"
        model_type = "Professional DCF & Margin of Safety"

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