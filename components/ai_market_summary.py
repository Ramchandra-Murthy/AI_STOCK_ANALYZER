import streamlit as st


def show_ai_market_summary():
    """
    Displays a simple AI-generated market outlook.
    """

    st.subheader("🤖 AI Market Summary")

    # Temporary logic (we'll replace this with real AI later)
    trend = "Bullish"
    confidence = 87
    risk = "Moderate"
    sectors = ["Banking", "IT"]
    avoid = ["Auto"]

    with st.container(border=True):

        st.metric("Market Trend", trend)
        st.metric("AI Confidence", f"{confidence}%")
        st.metric("Risk Level", risk)

        st.write("### ✅ Preferred Sectors")
        for sector in sectors:
            st.write(f"• {sector}")

        st.write("### ⚠️ Caution")
        for sector in avoid:
            st.write(f"• {sector}")