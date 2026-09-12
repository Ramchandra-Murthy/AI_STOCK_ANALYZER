from services.validation.data_hardening import InstitutionalDataHardener
from services.validation.decision_robustness import DecisionRobustnessEngine


def test_block22a_data_sanitization_valid():
    clean_data = {"symbol": "TCS.NS", "price": 3500.0, "volume": 150000}
    res = InstitutionalDataHardener.sanitize_input(clean_data)
    assert res.is_valid is True
    assert len(res.errors) == 0


def test_block22a_data_sanitization_anomalies():
    dirty_data = {"symbol": "", "price": -50.0, "volume": -100}
    res = InstitutionalDataHardener.sanitize_input(dirty_data)
    assert res.is_valid is False
    assert len(res.errors) >= 2
    assert res.sanitized_data["price"] == 0.0
    assert res.sanitized_data["volume"] == 0


def test_block22b_conflicting_signals_growth_vs_valuation():
    eval_res = DecisionRobustnessEngine.evaluate_conflicting_signals(
        "INFY.NS", "high_valuation_strong_growth"
    )
    assert eval_res["symbol"] == "INFY.NS"
    assert eval_res["final_action"] in ["BUY", "STRONG BUY", "HOLD", "REDUCE"]
    assert eval_res["rationale_count"] > 0


def test_block22b_conflicting_signals_momentum_vs_fundamentals():
    eval_res = DecisionRobustnessEngine.evaluate_conflicting_signals(
        "RELIANCE.NS", "poor_fundamentals_strong_momentum"
    )
    assert eval_res["symbol"] == "RELIANCE.NS"
    assert eval_res["final_action"] in ["HOLD", "REDUCE", "SELL", "BUY"]
