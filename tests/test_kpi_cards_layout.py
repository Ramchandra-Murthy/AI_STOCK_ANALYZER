from unittest.mock import patch

from components.kpi_cards import show_kpi_cards


def test_kpi_cards_render_responsive_grid_and_empty_score_as_na():
    summary = {
        "ai_score": None,
        "holdings": 0,
        "investment": 0,
        "current_value": 0,
        "profit": 0,
        "return": 0,
        "unpriced_holdings": 0,
    }

    with patch("components.kpi_cards.st.markdown") as markdown:
        show_kpi_cards(summary)

    markup = markdown.call_args.args[0]
    assert "grid-template-columns: repeat(auto-fit, minmax(145px, 1fr))" in markup
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in markup
    assert "N/A" in markup
    assert "None/100" not in markup


def test_kpi_cards_render_numeric_score_and_portfolio_values():
    summary = {
        "ai_score": 80,
        "holdings": 2,
        "investment": 1500,
        "current_value": 1600,
        "profit": 100,
        "return": 6.67,
        "unpriced_holdings": 0,
    }

    with patch("components.kpi_cards.st.markdown") as markdown:
        show_kpi_cards(summary)

    markup = markdown.call_args.args[0]
    assert "80/100" in markup
    assert "₹1,500.00" in markup
    assert "₹1,600.00" in markup
    assert "2" in markup
