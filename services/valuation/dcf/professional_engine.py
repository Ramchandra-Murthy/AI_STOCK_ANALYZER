from __main__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

@dataclass
class ProfessionalDCFResult:
    symbol: str
    valuation_model: str
    enterprise_value: float
    equity_value: float
    fair_value_per_share: float
    wacc: float
    terminal_growth_rate: float
    pv_explicit_cash_flows: float
    pv_terminal_value: float
    sensitivity_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)

class ProfessionalDCFEngine:
    """Institutional-grade Multi-Stage DCF Engine supporting FCFF, FCFE, and sensitivity matrices."""

    def calculate_fcff(
        self,
        symbol: str,
        fcff_projections: List[float],
        wacc: float,
        terminal_growth_rate: float,
        net_debt: float,
        shares_outstanding: float
    ) -> ProfessionalDCFResult:
        logger.info("Executing Professional Multi-Stage FCFF DCF for %s", symbol)
        
        # Calculate Present Value of Explicit Cash Flows
        pv_explicit = sum(fcf / ((1.0 + wacc) ** (i + 1)) for i, fcf in enumerate(fcff_projections))
        
        # Terminal Value via Gordon Growth Model
        final_fcf = fcff_projections[-1] if fcff_projections else 0.0
        terminal_value = (final_fcf * (1.0 + terminal_growth_rate)) / (wacc - terminal_growth_rate)
        pv_terminal = terminal_value / ((1.0 + wacc) ** len(fcff_projections))
        
        enterprise_value = pv_explicit + pv_terminal
        equity_value = enterprise_value - net_debt
        fair_value_per_share = equity_value / shares_outstanding if shares_outstanding > 0 else 0.0

        # Generate WACC vs Terminal Growth Sensitivity Matrix
        sensitivity: Dict[str, Dict[str, float]] = {}
        wacc_variants = [wacc - 0.01, wacc, wacc + 0.01]
        tgr_variants = [terminal_growth_rate - 0.005, terminal_growth_rate, terminal_growth_rate + 0.005]

        for w in wacc_variants:
            w_key = f"{w*100:.1f}%"
            sensitivity[w_key] = {}
            for t in tgr_variants:
                t_key = f"{t*100:.1f}%"
                if w <= t:
                    sensitivity[w_key][t_key] = 0.0
                    continue
                tv = (final_fcf * (1.0 + t)) / (w - t)
                pv_t = tv / ((1.0 + w) ** len(fcff_projections))
                ev = sum(fcf / ((1.0 + w) ** (i + 1)) for i, fcf in enumerate(fcff_projections)) + pv_t
                eq = ev - net_debt
                val = eq / shares_outstanding if shares_outstanding > 0 else 0.0
                sensitivity[w_key][t_key] = round(val, 2)

        return ProfessionalDCFResult(
            symbol=symbol,
            valuation_model="FCFF Multi-Stage",
            enterprise_value=round(enterprise_value, 2),
            equity_value=round(equity_value, 2),
            fair_value_per_share=round(fair_value_per_share, 2),
            wacc=wacc,
            terminal_growth_rate=terminal_growth_rate,
            pv_explicit_cash_flows=round(pv_explicit, 2),
            pv_terminal_value=round(pv_terminal, 2),
            sensitivity_matrix=sensitivity
        )
