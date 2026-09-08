from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List

from services.valuation.dcf.professional_engine import ProfessionalDCFEngine, ProfessionalDCFResult
from services.valuation.relative.engine import RelativeValuationEngine
from services.valuation.sotp.engine import SOTPEngine

logger = logging.getLogger(__name__)

@dataclass
class BlendedValuationResult:
    symbol: str
    dcf_fair_value: float
    relative_fair_value: float
    sotp_fair_value: float
    blended_fair_value: float
    model_weights: Dict[str, float] = field(default_factory=lambda: {"DCF": 0.5, "Relative": 0.3, "SOTP": 0.2})

class BlendedValuationEngine:
    """Synthesizes DCF, Relative Valuation, and SOTP into a single institutional blended intrinsic value."""

    def __init__(self) -> None:
        self.dcf_engine = ProfessionalDCFEngine()
        self.relative_engine = RelativeValuationEngine()
        self.sotp_engine = SOTPEngine()

    def evaluate(
        self,
        symbol: str,
        fcff_projections: List[float],
        wacc: float,
        terminal_growth_rate: float,
        net_debt: float,
        shares_outstanding: float,
        current_price: float,
        financials: Any,
        weights: Dict[str, float] | None = None
    ) -> BlendedValuationResult:
        logger.info("Computing blended institutional valuation for %s", symbol)
        
        dcf_res = self.dcf_engine.calculate_fcff(
            symbol=symbol,
            fcff_projections=fcff_projections,
            wacc=wacc,
            terminal_growth_rate=terminal_growth_rate,
            net_debt=net_debt,
            shares_outstanding=shares_outstanding
        )
        
        rel_res = self.relative_engine.evaluate(financials, current_price=current_price)
        sotp_res = self.sotp_engine.calculate(financials, holding_discount=0.15)

        w = weights or {"DCF": 0.5, "Relative": 0.3, "SOTP": 0.2}
        
        dcf_val = dcf_res.fair_value_per_share
        rel_val = rel_res.blend_relative_value
        sotp_val = sotp_res.fair_value_per_share

        blended = (dcf_val * w.get("DCF", 0.5)) + (rel_val * w.get("Relative", 0.3)) + (sotp_val * w.get("SOTP", 0.2))

        return BlendedValuationResult(
            symbol=symbol,
            dcf_fair_value=dcf_val,
            relative_fair_value=rel_val,
            sotp_fair_value=sotp_val,
            blended_fair_value=round(blended, 2),
            model_weights=w
        )
