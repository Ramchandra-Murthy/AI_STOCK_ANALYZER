from __future__ import annotations

import logging
from typing import Dict, Any, List
from services.portfolio_intelligence.models import Portfolio, Position, PortfolioDecision

logger = logging.getLogger(__name__)

class PortfolioIntelligenceService:
    """Institutional Portfolio Intelligence engine managing diversification, risk budgeting, and optimization."""

    @staticmethod
    def compute_sector_allocation(portfolio: Portfolio) -> Dict[str, float]:
        total_val = portfolio.total_portfolio_value
        if total_val <= 0:
            return {}
        
        sector_vals: Dict[str, float] = {}
        sector_vals["CASH"] = portfolio.cash

        for p in portfolio.positions:
            sector_vals[p.sector] = sector_vals.get(p.sector, 0.0) + p.market_value

        return {sector: round((val / total_val) * 100.0, 2) for sector, val in sector_vals.items()}

    @classmethod
    def evaluate_portfolio(cls, portfolio: Portfolio) -> PortfolioDecision:
        logger.info("Evaluating portfolio %s for %s", portfolio.portfolio_id, portfolio.owner)
        total_val = portfolio.total_portfolio_value
        if total_val <= 0:
            raise ValueError(f"Portfolio {portfolio.portfolio_id} has zero or negative total value.")

        sector_alloc = cls.compute_sector_allocation(portfolio)
        
        # Calculate weighted portfolio return and risk
        weighted_return_sum = sum(p.expected_return * p.market_value for p in portfolio.positions)
        weighted_risk_sum = sum(p.expected_risk * p.market_value for p in portfolio.positions)
        
        pos_val = portfolio.total_positions_value
        portfolio_return = round(weighted_return_sum / pos_val, 4) if pos_val > 0 else 0.0
        portfolio_risk = round(weighted_risk_sum / pos_val, 4) if pos_val > 0 else 0.0

        target_weights: Dict[str, float] = {}
        recommended_actions: List[Dict[str, Any]] = []

        for p in portfolio.positions:
            current_weight = round((p.market_value / total_val) * 100.0, 2)
            # Simple heuristic optimization target based on committee signal and valuation discount
            if p.committee_signal == "BUY" and p.intrinsic_value > p.current_price:
                target_weight = min(15.0, current_weight + 2.0)
                action = "INCREASE"
            elif p.committee_signal == "SELL":
                target_weight = max(0.0, current_weight - 3.0)
                action = "DECREASE"
            else:
                target_weight = current_weight
                action = "HOLD"

            target_weights[p.symbol] = target_weight
            recommended_actions.append({
                "symbol": p.symbol,
                "current_weight_pct": current_weight,
                "target_weight_pct": target_weight,
                "action": action,
                "rationale": f"Committee signal: {p.committee_signal}. Intrinsic value: ₹{p.intrinsic_value} vs Price: ₹{p.current_price}."
            })

        # Identify major concentration risks
        major_risks = [f"Sector concentration in {sec}: {wt}%" for sec, wt in sector_alloc.items() if wt > 30.0 and sec != "CASH"]
        if not major_risks:
            major_risks.append("Portfolio is reasonably diversified across sectors.")

        portfolio_score = round(min(100.0, max(0.0, (portfolio_return / max(portfolio_risk, 0.01)) * 50.0 + 50.0)), 2)
        confidence = 0.88

        rebalance_summary = (
            f"Portfolio evaluation complete. Total Value: ₹{total_val:,.2f}. "
            f"Expected Annual Return: {portfolio_return * 100.0:.1f}%, Expected Volatility: {portfolio_risk * 100.0:.1f}%. "
            f"Optimization recommends adjustments across {len([a for a in recommended_actions if a['action'] != 'HOLD'])} positions."
        )

        return PortfolioDecision(
            portfolio_id=portfolio.portfolio_id,
            recommended_actions=recommended_actions,
            target_weights=target_weights,
            expected_return=portfolio_return,
            expected_risk=portfolio_risk,
            portfolio_score=portfolio_score,
            confidence=confidence,
            major_risks=major_risks,
            rebalance_summary=rebalance_summary
        )
