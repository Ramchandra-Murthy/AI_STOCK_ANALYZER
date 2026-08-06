import streamlit as st

from services.research_service import get_stock_profile
from services.technical_service import get_price_history
from components.charts.candlestick_chart import plot_candlestick
from services.ai_service import get_ai_recommendation
from components.technical_summary import show_technical_summary


# ============================================================
# Helper Functions
# ============================================================

def format_market_cap(value):
    """Format Market Cap nicely."""

    if value in [None, "N/A"]:
        return "N/A"

    try:
        value = float(value)

        if value >= 1e12:
            return f"₹{value / 1e12:.2f} Lakh Cr"

        elif value >= 1e9:
            return f"₹{value / 1e7:.2f} Cr"

        elif value >= 1e6:
            return f"₹{value / 1e5:.2f} Lakh"

        return f"{value:,.0f}"

    except Exception:
        return str(value)


def format_percent(value):
    """Convert decimal values into percentage."""

    if value in [None, "N/A"]:
        return "N/A"

    try:
        return f"{float(value) * 100:.2f}%"

    except Exception:
        return str(value)


# ============================================================
# Main Screen
# ============================================================

def show():

    st.title("🔍 Stock Research Terminal")
    st.caption("Professional Equity Research Platform")

    st.divider()

    col1, col2 = st.columns([3, 1])

    with col1:
        symbol = st.text_input(
            "Enter NSE Symbol",
            value="RELIANCE"
        ).upper()

    with col2:
        st.write("")
        st.write("")
        analyze = st.button(
            "🔍 Analyze",
            use_container_width=True
        )

    if not analyze:
        return

    with st.spinner("Fetching stock information..."):

        data = get_stock_profile(symbol)
        history = get_price_history(symbol)

    if data is None:
        st.error("Unable to fetch stock information.")
        return

    ai_result = get_ai_recommendation(data, history)
    # ============================================================
    # Research Tabs
    # ============================================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Overview",
        "📊 Financials",
        "📈 Technical",
        "🤖 AI Analysis"
    ])

    # =====================================================
    # Company Profile
    # =====================================================

    st.subheader("🏢 Company Profile")

    c1, c2 = st.columns(2)

    with c1:
        st.metric("Company", data.get("company", "N/A"))
        st.metric("Sector", data.get("sector", "N/A"))
        st.metric("Industry", data.get("industry", "N/A"))

    with c2:
        st.metric("Current Price", data.get("price", "N/A"))
        st.metric(
            "Market Cap",
            format_market_cap(data.get("market_cap"))
        )
        st.metric("Currency", data.get("currency", "N/A"))

    st.divider()

    # =====================================================
    # AI Analysis Tab
    # =====================================================

    with tab4:

    st.subheader("🤖 AI Recommendation")

    score = ai_result["score"]
    recommendation = ai_result["recommendation"]
    risk = ai_result["risk"]
    reasons = ai_result["reasons"]

    left, right = st.columns([1, 2])

    with left:
        st.metric("AI Score", f"{score}/100")

    with right:

        if recommendation == "BUY":
            st.success("🟢 BUY")

        elif recommendation == "HOLD":
            st.warning("🟡 HOLD")

        else:
            st.error("🔴 SELL")

    st.write(f"### Risk Level: **{risk}**")

    st.write("### Reasons")

    if reasons:

        for reason in reasons:
            st.write(f"✅ {reason}")

    else:
        st.info("No AI reasons available.")

    st.divider()

    # =====================================================
    # Financials Tab
    # =====================================================

    with tab2:

    st.subheader("📊 Financial Ratios")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("PE Ratio", data.get("pe", "N/A"))

    with c2:
        st.metric("PB Ratio", data.get("pb", "N/A"))

    with c3:
        st.metric("EPS", data.get("eps", "N/A"))

    with c4:
        st.metric("Beta", data.get("beta", "N/A"))

    st.write("")

    c5, c6, c7, c8 = st.columns(4)

    with c5:
        st.metric("ROE", format_percent(data.get("roe")))

    with c6:
        st.metric("Profit Margin", format_percent(data.get("profit_margin")))

    with c7:
        st.metric("Operating Margin", format_percent(data.get("operating_margin")))

    with c8:
        st.metric("Dividend Yield", format_percent(data.get("dividend_yield")))
    st.divider()

    # =====================================================
    # Technical Tab
    # =====================================================

    with tab3:

    st.subheader("📈 Price Chart")
    
    if history is not None and not history.empty:

        fig = plot_candlestick(history)

        st.plotly_chart(,
            fig,
            use_container_width=True
        )

        # -----------------------------------------
        # Technical Summary
        # -----------------------------------------

        st.divider()

        show_technical_summary(history)

    else:
        st.warning("No historical price data available.")