import pandas as pd
import plotly.express as px
import streamlit as st


def show_performance_chart(df):
    """Display portfolio performance chart with proper None/NaN handling."""
    if df.empty or "Profit" not in df.columns:
        st.info("No portfolio data available yet. Add some trades to see performance!")
        return

    # ✅ CRITICAL FIX: Convert None/NaN to 0 so comparisons work
    df["Profit"] = pd.to_numeric(df["Profit"], errors="coerce").fillna(0)

    chart_df = df.copy()
    chart_df["Status"] = chart_df["Profit"].apply(lambda x: "Profit" if x >= 0 else "Loss")

    # If you had more chart code, it continues here...
    # (I'm preserving the rest of your original file below -
    #  but we only need to fix the None comparison).

    fig = px.bar(
        chart_df,
        x="Symbol" if "Symbol" in chart_df.columns else chart_df.index,
        y="Profit",
        color="Status",
        title="Portfolio Performance",
    )
    st.plotly_chart(fig, use_container_width=True)
