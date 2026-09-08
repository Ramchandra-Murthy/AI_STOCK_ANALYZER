from services.recommendation_service import generate_recommendation


def test_recommendation_bands():
    assert generate_recommendation(90)["recommendation"] == "STRONG BUY"
    assert generate_recommendation(70)["recommendation"] == "BUY"
    assert generate_recommendation(55)["recommendation"] == "HOLD"
    assert generate_recommendation(40)["recommendation"] == "SELL"
    assert generate_recommendation(39)["recommendation"] == "STRONG SELL"


def test_recommendation_clamps_score():
    assert generate_recommendation(150)["overall_score"] == 100
    assert generate_recommendation(-10)["overall_score"] == 0
