from modules.dashboard import calculate_ai_score


def test_calculate_ai_score_returns_none_when_portfolio_is_empty():
    summary = {
        "holdings": 0,
        "return": 0,
        "investment": 0,
    }

    assert calculate_ai_score(summary) is None


def test_calculate_ai_score_scores_portfolio_with_holdings():
    summary = {
        "holdings": 1,
        "return": 0,
        "investment": 1000,
    }

    assert calculate_ai_score(summary) == 80


def test_calculate_ai_score_keeps_existing_low_score_for_zero_investment():
    summary = {
        "holdings": 1,
        "return": 0,
        "investment": 0,
    }

    assert calculate_ai_score(summary) == 0
