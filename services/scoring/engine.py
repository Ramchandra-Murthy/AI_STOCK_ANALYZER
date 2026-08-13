from __future__ import annotations
import logging
from typing import Dict
from services.financials.financial_statement import FinancialStatements
from services.scoring.models import AIScoreResult
from services.scoring.growth import GrowthScoringEngine
from services.scoring.fundamental import FundamentalScoringEngine
from services.valuation.engine import ValuationEngine
from services.scoring.technical import MomentumScoringEngine
from services.scoring.risk_scoring import RiskScoringEngine
from services.market_data.models import PriceRecord
from services.risk_management.models import PortfolioRiskProfile

logger = logging.getLogger(__name__)

def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, float(value)))

def _score_valuation(margin_of_safety: float) -> float:
    score = 60.0 + (margin_of_safety / 30.0) * 40.0
    return _clamp(score)

class AIScoringEngine:
    """
    Institutional Fundamental, Growth, Valuation, Momentum, & Risk AI Scoring Engine.
    Block 15H integrates RiskScoringEngine for dynamic institutional risk scoring.
    """
    def __init__(self) -> None:
        self.fundamental_engine = FundamentalScoringEngine()
        self.growth_engine = GrowthScoringEngine()
        self.valuation_engine = ValuationEngine()
        self.momentum_engine = MomentumScoringEngine()
        self.risk_scoring_engine = RiskScoringEngine()

    def evaluate(
        self,
        financials: FinancialStatements,
        market_records: list[PriceRecord] | None = None,
        risk_profile: PortfolioRiskProfile | None = None,
    ) -> AIScoreResult:
        ticker = financials.ticker
        logger.info(
            "Running unified institutional AI scoring with valuation, momentum, and risk for symbol: %s",
            ticker,
        )

        # 1. Fundamental Scoring (Blocks 12A-12C)
        fund_res = self.fundamental_engine.evaluate(financials)

        profitability_score = fund_res.profitability_score
        quality_score = fund_res.quality_score
        capital_allocation_score = fund_res.cash_flow_quality_score

        # 2. Historical Growth Scoring (Block 11)
        growth_res = self.growth_engine.evaluate(financials)
        growth_score = growth_res.growth_score

        # 3. Dynamic Valuation Engine Integration (Block 13)
        val_res = self.valuation_engine.compute(symbol=ticker, forecast_data=financials)
        valuation_score = _score_valuation(val_res.margin_of_safety_pct)

        # 4. Dynamic Momentum Scoring Integration (Block 14H)
        if not market_records:
            base_price = 1000.0
            market_records = [
                PriceRecord(
                    date=f"2026-07-{i+1:02d}",
                    open=base_price + i,
                    high=base_price + i + 5,
                    low=base_price + i - 5,
                    close=base_price + i + 2,
                    volume=1000000 + i * 10000,
                )
                for i in range(30)
            ]

        mom_res = self.momentum_engine.evaluate(symbol=ticker, records=market_records)
        momentum_score = mom_res.momentum_score

        # 5. Dynamic Risk Scoring Integration (Block 15H)
        risk_res = self.risk_scoring_engine.evaluate(symbol=ticker, profile=risk_profile)
        risk_score = risk_res.risk_score

        # 6. Weighted Composite
        weights: Dict[str, float] = {
            "growth": 0.15,
            "quality": 0.20,
            "profitability": 0.20,
            "capital_allocation": 0.10,
            "valuation": 0.15,
            "momentum": 0.10,
            "risk": 0.10,
        }
        composite = (
            growth_score * weights["growth"]
            + quality_score * weights["quality"]
            + profitability_score * weights["profitability"]
            + capital_allocation_score * weights["capital_allocation"]
            + valuation_score * weights["valuation"]
            + momentum_score * weights["momentum"]
            + risk_score * weights["risk"]
        )
        composite = round(_clamp(composite), 2)

        if composite >= 75.0:
            rating = "STRONG BUY"
        elif composite >= 60.0:
            rating = "BUY"
        elif composite >= 45.0:
            rating = "HOLD"
        elif composite >= 30.0:
            rating = "SELL"
        else:
            rating = "STRONG SELL"

        details = {
            "rating": rating,
            "engine_version": "EROS-3.0-BLOCK-15",
            "weights_used": weights,
            "growth_engine": growth_res.growth_details,
            "fundamental_engine": fund_res.pillar_details,
            "valuation_engine": {
                "blended_fair_value": val_res.blended_fair_value,
                "current_market_price": val_res.current_market_price,
                "margin_of_safety_pct": val_res.margin_of_safety_pct,
                "recommendation": val_res.recommendation,
                "valuation_score": valuation_score,
            },
            "momentum_engine": mom_res.details,
            "risk_engine": risk_res.details,
        }

        return AIScoreResult(
            symbol=ticker,
            growth_score=round(growth_score, 2),
            quality_score=round(quality_score, 2),
            profitability_score=round(profitability_score, 2),
            capital_allocation_score=round(capital_allocation_score, 2),
            valuation_score=round(valuation_score, 2),
            momentum_score=round(momentum_score, 2),
            risk_score=round(risk_score, 2),
            composite_score=composite,
            breakdown_details=details,
        )
