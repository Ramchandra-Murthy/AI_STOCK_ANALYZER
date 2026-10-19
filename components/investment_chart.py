import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def show_investment_chart(df):
    """
    Compare invested amount with current value for holdings with a valid cost basis.
    """

    if df.empty:
        st.info("No holdings available.")
        return

    priced_df = df.dropna(subset=["Current Value"]).copy()
    if priced_df.empty:
        st.info("Investment comparison is unavailable because no holdings have current prices.")
        return

    quantity = pd.to_numeric(priced_df["quantity"], errors="coerce")
    buy_price = pd.to_numeric(priced_df["buy_price"], errors="coerce")
    valid_cost_basis = (
        quantity.gt(0) & buy_price.gt(0) & np.isfinite(quantity) & np.isfinite(buy_price)
    )

    chart_df = priced_df.loc[valid_cost_basis].copy()
    if chart_df.empty:
        st.info(
            "Investment comparison is unavailable because purchase cost is missing or invalid "
            "for all priced holdings."
        )
        return

    if len(chart_df) < len(priced_df):
        excluded = len(priced_df) - len(chart_df)
        st.warning(
            f"Investment comparison excludes {excluded} priced holding(s) with missing or "
            "invalid purchase cost."
        )

    chart_df["Investment"] = quantity.loc[valid_cost_basis] * buy_price.loc[valid_cost_basis]

    fig = go.Figure()

    fig.add_bar(name="Investment", x=chart_df["symbol"], y=chart_df["Investment"])
    fig.add_bar(name="Current Value", x=chart_df["symbol"], y=chart_df["Current Value"])

    fig.update_layout(
        barmode="group",
        height=320,
        xaxis_title="Stock",
        yaxis_title="Amount (₹)",
        margin=dict(l=12, r=12, t=16, b=36),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        autosize=True,\n        xaxis=dict(automargin=True, tickangle=0),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
        key="dashboard_investment_comparison_chart",
    )
