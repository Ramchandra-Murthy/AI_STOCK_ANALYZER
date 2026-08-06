from __future__ import annotations

import pytest
from services.valuation.dcf.professional_engine import ProfessionalDCFEngine

def test_professional_dcf_calculation() -> None:
    engine = ProfessionalDCFEngine()
    projections = [10000.0, 11500.0, 13200.0, 15100.0, 17300.0]
    result = engine.calculate_fcff(
        symbol="RELIANCE.NS",
        fcff_projections=projections,
        wacc=0.10,
        terminal_growth_rate=0.04,
        net_debt=50000.0,
        shares_outstanding=1000.0
    )
    assert result.symbol == "RELIANCE.NS"
    assert result.fair_value_per_share > 0
    assert len(result.sensitivity_matrix) > 0
    assert "10.0%" in result.sensitivity_matrix
