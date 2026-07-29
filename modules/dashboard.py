import streamlit as st

from services.portfolio_service import get_portfolio, get_summary

from components.kpi_cards import show_kpi_cards
from components.ai_score import show_ai_score
from components.portfolio_allocation import show_portfolio_allocation
from components.top_holdings import show_top_holdings
from components.quick_actions import show_quick_actions
from components.add_holding_form import show_add_holding_form
from components.edit_holding_form import show_edit_holding_form
from components.export_portfolio import export_portfolio
from components.portfolio_analytics import show_portfolio_analytics
from components.performance_chart import show_performance_chart
from components.investment_chart import show_investment_chart
from components.market_overview import show_market_overview
from components.market_movers import show_market_movers
from components.ai_market_summary import show_ai_market_summary
from components.technical_summary import show_technical_summary
from reports.report_generator import ReportGenerator


def calculate_ai_score(summary):

    score = 100

    if summary["holdings"] < 5:
        score -= 20

    if summary["return"] < 0:
        score -= 10

    if summary["investment"] == 0:
        score = 0

    return max(score, 0)


def show():

    st.title("📈 AI Stock Analyzer Pro")
    st.caption("Professional Portfolio Dashboard")
    show_market_overview()

    st.divider()

    df = get_portfolio()
    summary = get_summary(df)

    summary["ai_score"] = calculate_ai_score(summary)

    # ============================
    # KPI CARDS
    # ============================

    show_kpi_cards(summary)

    st.divider()

    # ============================
    # ROW 1
    # ============================

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📈 Portfolio Performance")
        show_performance_chart(df)

    with col2:
        st.subheader("🤖 AI Portfolio Health")
        show_ai_score(summary["ai_score"])

    st.divider()

    # ============================
    # ROW 2
    # ============================

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🥧 Portfolio Allocation")
        show_portfolio_allocation(df)

    with col2:
        st.subheader("💰 Investment vs Current Value")
        show_investment_chart(df)

    st.divider()

    # ============================
    # ROW 3
    # ============================

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📋 Top Holdings")
        show_top_holdings(df)
        st.divider()

        show_market_movers()
        st.divider()

        show_ai_market_summary()
    with col2:
        st.subheader("📊 Portfolio Analytics")
        show_portfolio_analytics(df)

    st.divider()

    # ============================
    # QUICK ACTIONS
    # ============================

    st.subheader("⚡ Quick Actions")

    c1, c2 = st.columns([1, 1])

    with c1:
        show_quick_actions()

    with c2:
        export_portfolio(df)

    st.divider()

    # ============================
    # ADD / EDIT HOLDINGS
    # ============================

    with st.expander("➕ Add New Holding", expanded=False):
        show_add_holding_form()

    with st.expander("✏️ Edit Holding", expanded=False):
        show_edit_holding_form(df)
