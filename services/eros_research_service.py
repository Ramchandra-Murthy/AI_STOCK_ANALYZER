from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from services.ai_service import get_ai_recommendation
from services.fundamental_score_service import calculate_fundamental_score
from services.investment_thesis_service import generate_investment_thesis
from services.news_service import get_company_news
from services.recommendation_service import generate_recommendation
from services.research_service import get_stock_profile
from services.scenario_service import generate_scenario_analysis
from services.score_service import calculate_investment_score
from services.technical_score_service import calculate_technical_score
from services.technical_service import get_price_history
from services.trade_plan_service import generate_trade_plan
from services.valuation_service import generate_valuation_analysis
from services.valuation_v43_service import generate_valuation_v43

logger = logging.getLogger(__name__)


class EROSResearchService:
    """Application boundary for the legacy EROS research pipeline."""

    VERSION = "EROS-3.0-REPAIR"

    def run_pipeline(self, ticker: str) -> dict[str, Any]:
        symbol = self._normalize_symbol(ticker)
        data = get_stock_profile(symbol)
        if not data:
            raise RuntimeError(f"No stock profile data returned for {symbol}")

        history = get_price_history(symbol)
        errors: list[str] = []
        result: dict[str, Any] = {
            "status": "OK",
            "version": self.VERSION,
            "symbol": symbol,
            "data": data,
            "history": history,
            "errors": errors,
        }

        result["ai"] = self._safe("ai", lambda: get_ai_recommendation(data, history), {}, errors)
        result["news"] = self._safe("news", lambda: get_company_news(symbol), [], errors)

        technical_score, technical_reasons = self._safe(
            "technical_score",
            lambda: (
                calculate_technical_score(history)
                if history is not None and not history.empty
                else (0, ["Historical price data unavailable."])
            ),
            (0, ["Technical scoring unavailable."]),
            errors,
        )
        fundamental_score, fundamental_reasons = self._safe(
            "fundamental_score",
            lambda: calculate_fundamental_score(data),
            (0, ["Fundamental scoring unavailable."]),
            errors,
        )

        result["technical_score"] = technical_score
        result["technical_reasons"] = technical_reasons
        result["fundamental_score"] = fundamental_score
        result["fundamental_reasons"] = fundamental_reasons

        investment_score, score_breakdown = self._safe(
            "investment_score",
            lambda: calculate_investment_score(
                technical_score=technical_score,
                fundamental_score=fundamental_score,
                ai_result=result["ai"],
                data=data,
            ),
            (0, {}),
            errors,
        )
        result["investment_score"] = investment_score
        result["score_breakdown"] = score_breakdown

        result["recommendation"] = self._safe(
            "recommendation",
            lambda: generate_recommendation(investment_score=investment_score),
            {},
            errors,
        )
        result["trade_plan"] = self._safe(
            "trade_plan",
            lambda: generate_trade_plan(history=history, technical_score=technical_score),
            {},
            errors,
        )
        result["investment_thesis"] = self._safe(
            "investment_thesis",
            lambda: generate_investment_thesis(
                data=data,
                investment_score=investment_score,
                technical_score=technical_score,
                fundamental_score=fundamental_score,
                ai_result=result["ai"],
                score_breakdown=score_breakdown,
                technical_reasons=technical_reasons,
                fundamental_reasons=fundamental_reasons,
                trade_plan=result["trade_plan"],
            ),
            {},
            errors,
        )
        result["scenario_analysis"] = self._safe(
            "scenario_analysis",
            lambda: generate_scenario_analysis(
                data=data,
                investment_score=investment_score,
                technical_score=technical_score,
                fundamental_score=fundamental_score,
                ai_result=result["ai"],
                score_breakdown=score_breakdown,
                trade_plan=result["trade_plan"],
            ),
            {},
            errors,
        )
        result["valuation"] = self._safe(
            "valuation",
            lambda: generate_valuation_analysis(
                data=data, fundamental_score=fundamental_score, investment_score=investment_score
            ),
            {"status": "UNAVAILABLE"},
            errors,
        )
        result["valuation_v43"] = self._safe(
            "valuation_v43",
            lambda: generate_valuation_v43(symbol=symbol, company_data=data),
            {"status": "UNAVAILABLE"},
            errors,
        )

        if errors:
            result["status"] = "PARTIAL"
        return result

    @staticmethod
    def _normalize_symbol(ticker: str) -> str:
        symbol = str(ticker or "").strip().upper()
        if not symbol:
            raise ValueError("Ticker must not be empty.")
        return symbol

    @staticmethod
    def _safe(name: str, operation: Callable[[], Any], fallback: Any, errors: list[str]) -> Any:
        try:
            return operation()
        except Exception as exc:
            logger.exception("EROS stage '%s' failed", name)
            errors.append(f"{name}: {exc}")
            return fallback
