from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.decision.decision_engine import InstitutionalDecisionEngine
from services.execution.execution_engine import InstitutionalExecutionEngine
from services.execution.transaction_cost import TransactionCostAnalyzer
from services.portfolio.engine import PortfolioAnalyticsEngine
from services.scoring.models import AIScoreResult


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
    rationale: list[str]
    evidence: list[str]
    details: dict[str, Any]


class InvestmentDecisionOrchestrator:
    """Build an investment decision only from validated score/options inputs."""

    def __init__(
        self,
        policy_profile: str = "Institutional",
        max_position_limit: float = 0.12,
        aum_baseline: float = 100_000_000.0,
    ) -> None:
        if max_position_limit <= 0 or max_position_limit > 1:
            raise ValueError("max_position_limit must be between 0 and 1")
        if aum_baseline <= 0:
            raise ValueError("aum_baseline must be positive")
        self.policy_profile = policy_profile
        self.max_position_limit = float(max_position_limit)
        self.aum_baseline = float(aum_baseline)
        self.portfolio_engine = PortfolioAnalyticsEngine()

    def evaluate(
        self,
        ai_score: AIScoreResult,
        holdings: dict[str, dict[str, float]] | None = None,
        current_weight: float = 0.0,
        portfolio_weight: float | None = None,
        assumed_price: float | None = None,
    ) -> InvestmentDecisionResult:
        symbol = ai_score.symbol.strip().upper()
        if not symbol:
            raise ValueError("ai_score.symbol must be non-empty")
        if portfolio_weight is not None:
            current_weight = portfolio_weight
        current_weight = float(current_weight)
        if not 0 <= current_weight <= 1:
            raise ValueError("current_weight must be between 0 and 1")

        if assumed_price is None:
            value = ai_score.breakdown_details.get("current_price")
            assumed_price = float(value) if isinstance(value, (int, float)) else 0.0
        if assumed_price <= 0:
            raise ValueError("positive assumed_price is required")

        portfolio_metrics: dict[str, Any] = {}
        if holdings:
            result = self.portfolio_engine.analyze(holdings)
            portfolio_metrics = {
                "total_portfolio_value": result.total_portfolio_value,
                "portfolio_beta": result.portfolio_beta,
                "sharpe_ratio": result.sharpe_ratio,
                "value_at_risk_95": result.value_at_risk_95,
                "sector_allocation": result.sector_allocation,
            }
            for holding_symbol, data in holdings.items():
                if holding_symbol.strip().upper() == symbol and result.total_portfolio_value > 0:
                    current_weight = round(
                        float(data.get("shares", 0.0))
                        * float(data.get("price", 0.0))
                        / result.total_portfolio_value,
                        4,
                    )
                    break

        options = InstitutionalDecisionEngine.evaluate_options(
            symbol=symbol,
            policy_profile=self.policy_profile,
            options=None,
        )
        if options:
            best = options[0]
            action = best.action
            confidence = float(best.confidence)
            expected_return = float(best.expected_return)
            downside_risk = float(best.downside_risk)
            rationale = list(best.rationale)
            evidence = list(best.evidence)
        else:
            # No option generator has supplied a decision. A zero/incomplete score
            # remains explicitly HOLD rather than inventing a BUY/SELL conclusion.
            action = "HOLD"
            confidence = 0.0
            expected_return = 0.0
            downside_risk = 1.0
            rationale = ["No validated decision option was supplied."]
            evidence = ["Decision status: INCOMPLETE"]

        risk_factor = max(0.0, min(1.0, ai_score.risk_score / 100.0))
        conviction_factor = max(0.0, min(1.0, ai_score.composite_score / 100.0))
        if action in {"BUY", "STRONG BUY"} and ai_score.composite_score >= 60:
            target_weight = round(
                min(self.max_position_limit, self.max_position_limit * conviction_factor * risk_factor),
                4,
            )
        elif action in {"SELL", "STRONG SELL"}:
            target_weight = 0.0
        else:
            target_weight = round(min(current_weight, self.max_position_limit), 4)

        incremental_weight = round(target_weight - current_weight, 4)
        if current_weight > self.max_position_limit and action in {"BUY", "STRONG BUY"}:
            action = "HOLD"
            confidence = round(confidence * 0.85, 2)
            target_weight = current_weight
            incremental_weight = 0.0
            rationale.append("Incremental buying blocked by portfolio concentration limit.")

        notional_trade_value = abs(incremental_weight) * self.aum_baseline
        execution_orders: list[Any] = []
        tca_result: dict[str, float] = {}
        total_execution_cost = 0.0
        if incremental_weight != 0 and notional_trade_value > 0:
            order_action = "BUY" if incremental_weight > 0 else "SELL"
            execution_orders = InstitutionalExecutionEngine.generate_orders(
                [{
                    "symbol": symbol,
                    "action": order_action,
                    "trade_weight": abs(incremental_weight),
                    "current_price": assumed_price,
                }],
                execution_policy="VWAP-oriented",
                aum_baseline=self.aum_baseline,
            )
            tca_result = TransactionCostAnalyzer.analyze_order_costs(
                notional_trade_value,
                min(1.0, abs(incremental_weight)),
            )
            total_execution_cost = tca_result["total_transaction_cost"]

        cost_percentage_of_aum = total_execution_cost / self.aum_baseline
        net_expected_return = round(expected_return - cost_percentage_of_aum, 4)
        return InvestmentDecisionResult(
            symbol=symbol,
            action=action,
            confidence=confidence,
            composite_score=ai_score.composite_score,
            rating=str(ai_score.breakdown_details.get("rating", action)),
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
            details={
                "engine_version": "EROS-3.0-BLOCK-16D",
                "policy_profile": self.policy_profile,
                "portfolio_context": portfolio_metrics,
                "sizing_metrics": {
                    "conviction_factor": conviction_factor,
                    "risk_factor": risk_factor,
                },
                "execution_details": {
                    "notional_trade_value": notional_trade_value,
                    "generated_orders": [
                        {
                            "symbol": order.symbol,
                            "action": order.action,
                            "quantity": order.quantity,
                            "limit_price": order.limit_price,
                            "estimated_slippage": order.estimated_slippage,
                            "estimated_transaction_cost": order.estimated_transaction_cost,
                        }
                        for order in execution_orders
                    ],
                    "transaction_cost_analysis": tca_result,
                },
                "underlying_scoring_breakdown": ai_score.breakdown_details,
            },
        )
