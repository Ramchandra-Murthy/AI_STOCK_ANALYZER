import streamlit as st


def show_portfolio_analytics(df):
    """
    Portfolio Analytics
    """

    if df.empty:
        st.info("No holdings available.")
        return

    valued_df = df.dropna(subset=["Return %", "Profit"])
    if valued_df.empty:
        st.info("Portfolio analytics are unavailable because no holdings have current prices.")
        return

    best = valued_df.loc[valued_df["Return %"].idxmax()]
    worst = valued_df.loc[valued_df["Return %"].idxmin()]

    # -----------------------------
    # Best & Worst Performer
    # -----------------------------

    st.metric("🏆 Best Performer", best["symbol"], f"{best['Return %']:.2f}%")

    st.metric("📉 Worst Performer", worst["symbol"], f"{worst['Return %']:.2f}%")

    st.divider()

    # -----------------------------
    # Portfolio Statistics
    # -----------------------------

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Average Return", f"{valued_df['Return %'].mean():.2f}%")

    with col2:
        st.metric("Total Profit", f"₹{valued_df['Profit'].sum():,.2f}")
