from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from services.scoring.models import AIScoreResult
from services.decision.decision_engine import InstitutionalDecisionEngine
from services.portfolio.engine import PortfolioAnalyticsEngine
from services.execution.execution_engine import InstitutionalExecutionEngine
from services.execution.transaction_cost import TransactionCostAnalyzer

@dataclass(frozen=True, slots=True)
class InvestmentDecisionResult:
    symbol: str
    action: str
    confidence: float
    composite_score: float
    rating: str
    growth_score: float
    quality_score: float
    profitability_score: float
    capital_allocation_score: float
    valuation_score: float
    momentum_score: float
    risk_score: float
    expected_return: float
    downside_risk: float
    portfolio_weight: float
    target_weight: float
    incremental_weight: float
    execution_cost: float
    net_expected_return: float
    rationale: List[str]
    evidence: List[str]
    details: Dict[str, Any]

class InvestmentDecisionOrchestrator:
    """
    EROS 3.0 Block 16 Investment Decision, Position Sizing, Execution, & TCA Orchestration Layer.
    Consumes AIScoreResult, holdings, and integrates InstitutionalExecutionEngine & TransactionCostAnalyzer.
    """
    def __init__(self, policy_profile: str = "Institutional", max_position_limit: float = 0.12, aum_baseline: float = 100000000.0) -> None:
        self.policy_profile = policy_profile
        self.max_position_limit = max_position_limit
        self.aum_baseline = aum_baseline
        self.portfolio_engine = PortfolioAnalyticsEngine()

    def evaluate(
        self,
        ai_score: AIScoreResult,
        holdings: Optional[Dict[str, Dict[str, float]]] = None,
        current_weight: float = 0.0,
        portfolio_weight: Optional[float] = None,
        assumed_price: Optional[float] = None,
    ) -> InvestmentDecisionResult:
        if portfolio_weight is not None:
            current_weight = portfolio_weight

        symbol = ai_score.symbol

        # Market price must come from the canonical market-data path.
        # The old 2500.0 fallback could silently turn unavailable data into a
        # seemingly valid execution price, so it is intentionally removed.
        live_price = assumed_price
        if live_price is None:
            live_price = (ai_score.breakdown_details or {}).get("current_price")
        try:
            live_price = float(live_price)
        except (TypeError, ValueError):
            live_price = 0.0
        if live_price <= 0.0:
            raise ValueError(
                f"{symbol}: positive current market price is required for EROS decision/execution"
            )

        # 1. Run Portfolio Analytics if holdings provided
        portfolio_metrics = {}
        if holdings:
            p_result = self.portfolio_engine.analyze(holdings)
            portfolio_metrics = {
                "total_portfolio_value": p_result.total_portfolio_value,
                "portfolio_beta": p_result.portfolio_beta,
                "sharpe_ratio": p_result.sharpe_ratio,
                "value_at_risk_95": p_result.value_at_risk_95,
                "sector_allocation": p_result.sector_allocation,
            }
            if symbol in holdings:
                pos_data = holdings[symbol]
                mval = pos_data.get("shares", 0.0) * pos_data.get("price", live_price)
                if p_result.total_portfolio_value > 0:
                    current_weight = round(mval / p_result.total_portfolio_value, 4)

        # 2. Evaluate candidate institutional decision options
        options = InstitutionalDecisionEngine.evaluate_options(symbol=symbol, policy_profile=self.policy_profile)
        best_option = options[0] if options else None
        
        action = best_option.action if best_option else ai_score.breakdown_details.get("rating", "HOLD")
        confidence = best_option.confidence if best_option else 0.75
        expected_return = best_option.expected_return if best_option else 0.10
        downside_risk = best_option.downside_risk if best_option else 0.05
        rationale = list(best_option.rationale) if best_option else ["Default fallback rationale."]
        evidence = list(best_option.evidence) if best_option else [f"Composite Score: {ai_score.composite_score}"]

        # 3. Position Sizing & Risk-Budget Calculation
        risk_adjustment = ai_score.risk_score / 100.0
        conviction_factor = ai_score.composite_score / 100.0
        
        if action in ["BUY", "STRONG BUY"] and ai_score.composite_score >= 60.0:
            raw_target = self.max_position_limit * conviction_factor * risk_adjustment
            target_weight = round(min(raw_target, self.max_position_limit), 4)
        elif action in ["SELL", "STRONG SELL"]:
            target_weight = 0.0
        else:
            target_weight = round(current_weight, 4)

        incremental_weight = round(target_weight - current_weight, 4)

        # 4. Portfolio Concentration Constraint Check
        if current_weight > self.max_position_limit:
            rationale.append(f"Portfolio concentration warning: Current weight {current_weight*100:.1f}% exceeds institutional limit ({self.max_position_limit*100:.1f}%).")
            if action in ["BUY", "STRONG BUY"]:
                action = "HOLD"
                confidence = round(confidence * 0.85, 2)
                target_weight = current_weight
                incremental_weight = 0.0
                evidence.append("Action downgraded to HOLD and incremental target set to 0.0 due to concentration limit.")

        # 5. Block 16D Execution & Transaction Cost Integration
        notional_trade_value = abs(incremental_weight) * self.aum_baseline
        order_action = "BUY" if incremental_weight > 0 else ("SELL" if incremental_weight < 0 else "HOLD")
        
        execution_orders = []
        tca_result = {}
        total_execution_cost = 0.0

        if order_action in ["BUY", "SELL"] and notional_trade_value > 0.0:
            allocation_payload = [{
                "symbol": symbol,
                "action": order_action,
                "trade_weight": abs(incremental_weight),
                "current_price": live_price,
            }]
            execution_orders = InstitutionalExecutionEngine.generate_orders(allocation_payload, execution_policy="VWAP-oriented")
            
            adv_participation = 0.015
            tca_result = TransactionCostAnalyzer.analyze_order_costs(notional_trade_value, adv_participation)
            total_execution_cost = tca_result.get("total_transaction_cost", notional_trade_value * 0.0015)
        else:
            total_execution_cost = 0.0

        cost_percentage_of_aum = (total_execution_cost / self.aum_baseline) if self.aum_baseline > 0 else 0.0
        net_expected_return = round(expected_return - cost_percentage_of_aum, 4)

        details = {
            "engine_version": "EROS-3.0-BLOCK-16D",
            "policy_profile": self.policy_profile,
            "max_position_limit": self.max_position_limit,
            "portfolio_context": portfolio_metrics,
            "sizing_metrics": {
                "conviction_factor": conviction_factor,
                "risk_adjustment": risk_adjustment,
                "target_weight": target_weight,
                "incremental_weight": incremental_weight,
            },
            "execution_details": {
                "notional_trade_value": notional_trade_value,
                "generated_orders": [
                    {
                        "symbol": o.symbol,
                        "action": o.action,
                        "quantity": o.quantity,
                        "limit_price": o.limit_price,
                        "estimated_slippage": o.estimated_slippage,
                        "estimated_transaction_cost": o.estimated_transaction_cost,
                    }
                    for o in execution_orders
                ],
                "transaction_cost_analysis": tca_result,
            },
            "underlying_scoring_breakdown": ai_score.breakdown_details,
        }

        return InvestmentDecisionResult(
            symbol=symbol,
            action=action,
            confidence=confidence,
            composite_score=ai_score.composite_score,
            rating=ai_score.breakdown_details.get("rating", "HOLD"),
            growth_score=ai_score.growth_score,
            quality_score=ai_score.quality_score,
            profitability_score=ai_score.profitability_score,
            capital_allocation_score=ai_score.capital_allocation_score,
            valuation_score=ai_score.valuation_score,
            momentum_score=ai_score.momentum_score,
            risk_score=ai_score.risk_score,
            expected_return=expected_return,
            downside_risk=downside_risk,
            portfolio_weight=current_weight,
            target_weight=target_weight,
            incremental_weight=incremental_weight,
            execution_cost=round(total_execution_cost, 2),
            net_expected_return=net_expected_return,
            rationale=rationale,
            evidence=evidence,
            details=details,
        )
