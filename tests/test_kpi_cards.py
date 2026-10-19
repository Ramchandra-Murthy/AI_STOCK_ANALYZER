from components.kpi_cards import format_ai_score


def test_format_ai_score_shows_not_available_for_empty_portfolio():
    assert format_ai_score(None) == "N/A"


def test_format_ai_score_formats_numeric_score():
    assert format_ai_score(80) == "80/100"


def test_format_ai_score_formats_zero_score():
    assert format_ai_score(0) == "0/100"
