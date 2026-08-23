from services.recommendation_service import generate_recommendation


def test_strong_buy():
    result = generate_recommendation(88)

    assert result["recommendation"] == "STRONG BUY"
    assert result["confidence"] == 88
    assert result["overall_score"] == 88.0


def test_buy():
    result = generate_recommendation(75)

    assert result["recommendation"] == "BUY"
    assert result["confidence"] == 75


def test_hold():
    result = generate_recommendation(60)

    assert result["recommendation"] == "HOLD"
    assert result["confidence"] == 60


def test_sell():
    result = generate_recommendation(45)

    assert result["recommendation"] == "SELL"
    assert result["confidence"] == 45


def test_strong_sell():
    result = generate_recommendation(20)

    assert result["recommendation"] == "STRONG SELL"
    assert result["confidence"] == 20


def test_score_is_clamped():
    high = generate_recommendation(150)
    low = generate_recommendation(-20)

    assert high["overall_score"] == 100.0
    assert high["recommendation"] == "STRONG BUY"

    assert low["overall_score"] == 0.0
    assert low["recommendation"] == "STRONG SELL"


def test_invalid_score_uses_default():
    result = generate_recommendation("invalid")

    assert result["overall_score"] == 50.0
    assert result["recommendation"] == "SELL"
    assert result["confidence"] == 50
