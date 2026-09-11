from services.scenario_service import generate_scenario_analysis
from services.valuation_service import generate_valuation_analysis


def test_scenario_analysis_does_not_fabricate_missing_core_scores():
    result = generate_scenario_analysis(
        data={},
        investment_score=70,
        technical_score=None,
        fundamental_score=70,
        ai_result={},
        score_breakdown={},
        trade_plan={},
    )
    assert result["status"] == "INSUFFICIENT DATA"
    assert result["bull"] is None
    assert result["base"] is None
    assert result["bear"] is None


def test_scenario_analysis_rejects_invalid_price_levels():
    result = generate_scenario_analysis(
        data={},
        investment_score=70,
        technical_score=70,
        fundamental_score=70,
        ai_result={},
        score_breakdown={},
        trade_plan={
            "current_price": 100,
            "target_price": 0,
            "stop_loss": 90,
        },
    )
    assert result["status"] == "INSUFFICIENT DATA"
    assert result["reward_risk"] is None


def test_valuation_analysis_does_not_invent_missing_pe():
    result = generate_valuation_analysis(
        data={"price": 100, "eps": 10},
        fundamental_score=70,
        investment_score=70,
    )
    assert result["status"] == "INSUFFICIENT DATA"
    assert "P/E" in result["message"]


def test_valuation_analysis_rejects_missing_price_or_eps():
    result = generate_valuation_analysis(
        data={"price": None, "eps": 10, "pe": 15},
        fundamental_score=70,
        investment_score=70,
    )
    assert result["status"] == "UNAVAILABLE"
