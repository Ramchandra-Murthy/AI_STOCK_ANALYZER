from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from services.scoring.models import AIScoreResult
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
    """EROS 3.0 Block 16 evidence-bound investment decision and execution."""

    def __init__(
        self,
        policy_profile: str = "Institutional",
        max_position_limit: float = 0.12,
        aum_baseline: float = 100000000.0,
    ) -> None:
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
        details = dict(ai_score.breakdown_details or {})
        observed_price = details.get("current_price")
        market_state = str(
            details.get("market_data_state") or details.get("data_state") or ""
        ).upper()

        # Compatibility parameter: it may only repeat the canonical observed
        # price and may never override or introduce market evidence.
        if assumed_price is not None:
            try:
                supplied_price = float(assumed_price)
                canonical_price = float(observed_price)
            except (TypeError, ValueError):
                raise ValueError(
                    f"{symbol}: assumed_price is invalid; use canonical observed market evidence"
                ) from None
            if canonical_price <= 0.0 or supplied_price != canonical_price:
                raise ValueError(
                    f"{symbol}: assumed_price cannot override canonical market price"
                )

        try:
            live_price = float(observed_price)
        except (TypeError, ValueError):
            live_price = 0.0

        if live_price <= 0.0:
            raise ValueError(
                f"{symbol}: positive current market price is required for EROS decision/execution"
            )
        if market_state != "LIVE":
            raise ValueError(
                f"{symbol}: market data state must be LIVE for EROS decision/execution; "
                f"received {market_state or 'UNKNOWN'}"
            )

        portfolio_metrics: Dict[str, Any] = {}
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

        score = float(ai_score.composite_score)
        risk_score = float(ai_score.risk_score)
        momentum_score = float(ai_score.momentum_score)

        if score >= 75.0 and risk_score >= 60.0:
            action = "BUY"
            confidence = min(0.95, round(0.55 + (score - 75.0) / 100.0, 2))
            expected_return = round(max(0.05, (score - 50.0) / 250.0), 4)
            downside_risk = round(max(0.02, (100.0 - risk_score) / 1000.0), 4)
        elif score <= 35.0 or risk_score < 30.0:
            action = "SELL"
            confidence = min(
                0.90,
                round(0.55 + (35.0 - min(score, 35.0)) / 100.0, 2),
            )
            expected_return = round(min(-0.01, (score - 50.0) / 250.0), 4)
            downside_risk = round(max(0.08, (100.0 - risk_score) / 500.0), 4)
        else:
            action = "HOLD"
            confidence = min(0.85, round(0.55 + abs(score - 50.0) / 200.0, 2))
            expected_return = round((score - 50.0) / 500.0, 4)
            downside_risk = round(max(0.03, (100.0 - risk_score) / 1000.0), 4)

        rationale = [
            f"Composite score derived from observed EROS evidence: {score:.2f}/100.",
            f"Momentum score: {momentum_score:.2f}; market-risk score: {risk_score:.2f}.",
        ]
        if not details.get("fundamental_pillars_available", True):
            rationale.append(
                "Fundamental pillars were unavailable and were not synthesized."
            )

        evidence = [
            f"Scoring source: {details.get('scoring_source', 'unspecified')}",
            f"Observed pillars: {', '.join(details.get('observed_pillars', []))}",
            f"Market data state: {market_state}",
            f"Market price source: {details.get('market_price_source', 'unspecified')}",
        ]

        risk_adjustment = risk_score / 100.0
        conviction_factor = score / 100.0

        if action == "BUY" and score >= 60.0:
            raw_target = self.max_position_limit * conviction_factor * risk_adjustment
            target_weight = round(min(raw_target, self.max_position_limit), 4)
        elif action == "SELL":
            target_weight = 0.0
        else:
            target_weight = round(current_weight, 4)

        incremental_weight = round(target_weight - current_weight, 4)

        if current_weight > self.max_position_limit:
            rationale.append(
                f"Portfolio concentration warning: Current weight {current_weight*100:.1f}% "
                f"exceeds institutional limit ({self.max_position_limit*100:.1f}%)."
            )
            if action == "BUY":
                action = "HOLD"
                confidence = round(confidence * 0.85, 2)
                target_weight = current_weight
                incremental_weight = 0.0
                evidence.append("Action downgraded to HOLD due to concentration limit.")

        notional_trade_value = abs(incremental_weight) * self.aum_baseline
        order_action = (
            "BUY" if incremental_weight > 0
            else ("SELL" if incremental_weight < 0 else "HOLD")
        )

        execution_orders = []
        tca_result: Dict[str, Any] = {}
        total_execution_cost = 0.0

        if order_action in {"BUY", "SELL"} and notional_trade_value > 0.0:
            allocation_payload = [{
                "symbol": symbol,
                "action": order_action,
                "trade_weight": abs(incremental_weight),
                "current_price": live_price,
                "market_price_source": details.get("market_price_source"),
                "market_data_state": market_state,
            }]
            execution_orders = InstitutionalExecutionEngine.generate_orders(
                allocation_payload,
                execution_policy="VWAP-oriented",
                aum_baseline=self.aum_baseline,
            )
            tca_result = TransactionCostAnalyzer.analyze_order_costs(
                notional_trade_value,
                0.015,
            )
            total_execution_cost = tca_result.get("total_transaction_cost", 0.0)

        cost_percentage_of_aum = (
            total_execution_cost / self.aum_baseline
            if self.aum_baseline > 0
            else 0.0
        )
        net_expected_return = round(expected_return - cost_percentage_of_aum, 4)

        decision_details = {
            "engine_version": "EROS-3.0-BLOCK-16EVIDENCE-REPAIRED",
            "policy_profile": self.policy_profile,
            "max_position_limit": self.max_position_limit,
            "market_evidence": {
                "current_price": live_price,
                "market_data_state": market_state,
                "market_price_source": details.get("market_price_source"),
                "synthetic_price_used": False,
            },
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
            "underlying_scoring_breakdown": details,
        }

        return InvestmentDecisionResult(
            symbol=symbol,
            action=action,
            confidence=confidence,
            composite_score=score,
            rating=action,
            growth_score=ai_score.growth_score,
            quality_score=ai_score.quality_score,
            profitability_score=ai_score.profitability_score,
            capital_allocation_score=ai_score.capital_allocation_score,
            valuation_score=ai_score.valuation_score,
            momentum_score=momentum_score,
            risk_score=risk_score,
            expected_return=expected_return,
            downside_risk=downside_risk,
            portfolio_weight=current_weight,
            target_weight=target_weight,
            incremental_weight=incremental_weight,
            execution_cost=round(total_execution_cost, 2),
            net_expected_return=net_expected_return,
            rationale=rationale,
            evidence=evidence,
            details=decision_details,
        )
