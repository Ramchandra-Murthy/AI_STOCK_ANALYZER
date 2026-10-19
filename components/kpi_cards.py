import streamlit as st

from components.metric_card import metric_card


def format_ai_score(score):
    """Format an AI score without implying a score exists for an empty portfolio."""
    return "N/A" if score is None else f"{score}/100"


def show_kpi_cards(summary):
    """
    Display portfolio KPI cards.
    """

    ai_score = summary.get("ai_score", 80)
    has_unpriced_holdings = summary.get("unpriced_holdings", 0) > 0
    investment_label = "💰 Valued Investment" if has_unpriced_holdings else "💰 Investment"
    value_label = "📈 Valued Current Value" if has_unpriced_holdings else "📈 Current Value"
    profit_label = "💵 Profit / Loss (valued)" if has_unpriced_holdings else "💵 Profit / Loss"

    c1, c2, c3 = st.columns(3)

    with c1:
        metric_card(investment_label, f"₹{summary['investment']:,.2f}")

    with c2:
        metric_card(value_label, f"₹{summary['current_value']:,.2f}")

    with c3:
        metric_card(profit_label, f"₹{summary['profit']:,.2f}")

    st.write("")

    c4, c5, c6 = st.columns(3)

    with c4:
        return_label = "📊 Return (valued)" if has_unpriced_holdings else "📊 Return"
        metric_card(return_label, f"{summary['return']:.2f}%")

    with c5:
        metric_card("📁 Holdings", str(summary["holdings"]))

    with c6:
        metric_card("🤖 AI Score", format_ai_score(ai_score))
