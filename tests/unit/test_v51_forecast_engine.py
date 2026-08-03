import pytest
from services.forecast.confidence_engine import ConfidenceEngine, ConfidenceLevel
from services.forecast.terminal_growth import TerminalGrowthEngine
from services.forecast.assumption_engine import AssumptionEngine, ManagementGuidance

def test_confidence_engine_high_and_low():
    engine = ConfidenceEngine()
    
    # Stable revenues
    stable_revs = [100.0, 105.0, 110.0, 115.0, 121.0]
    stable_ebits = [15.0, 15.8, 16.5, 17.2, 18.2]
    res_high = engine.evaluate_confidence(stable_revs, stable_ebits)
    assert res_high.level == ConfidenceLevel.HIGH
    assert res_high.score >= 0.85

    # Volatile revenues
    volatile_revs = [100.0, 150.0, 90.0, 180.0]
    volatile_ebits = [10.0, 25.0, 5.0, 30.0]
    res_low = engine.evaluate_confidence(volatile_revs, volatile_ebits)
    assert res_low.level in (ConfidenceLevel.LOW, ConfidenceLevel.MEDIUM)

def test_terminal_growth_caps():
    engine = TerminalGrowthEngine()
    
    # G-Sec GDP cap at 5%, inflation at 3%
    growth = engine.estimate_terminal_growth(country_gdp_growth=0.05, long_term_inflation=0.03)
    assert growth == pytest.approx(0.04)

    # Manual override
    override = engine.estimate_terminal_growth(manual_override=0.025)
    assert override == 0.025

def test_assumption_engine_overrides():
    engine = AssumptionEngine()
    base_revs = [100.0, 110.0, 120.0]
    base_margins = [0.15, 0.15, 0.15]

    guidance = ManagementGuidance(revenue_cagr_override=0.20, target_ebit_margin_override=0.18)
    adj_revs, adj_margins = engine.apply_overrides(base_revs, base_margins, guidance)

    assert adj_margins[0] == 0.18
    assert adj_revs[1] > base_revs[1]
