import plotly.graph_objects as go
import streamlit as st


def show_investment_chart(df):
    """
    Compare invested amount with current value for each holding.
    """

    if df.empty:
        st.info("No holdings available.")
        return

    chart_df = df.dropna(subset=["Current Value"]).copy()
    if chart_df.empty:
        st.info("Investment comparison is unavailable because no holdings have current prices.")
        return

    invested = chart_df["quantity"] * chart_df["buy_price"]

    fig = go.Figure()

    fig.add_bar(name="Investment", x=chart_df["symbol"], y=invested)
    fig.add_bar(name="Current Value", x=chart_df["symbol"], y=chart_df["Current Value"])

    fig.update_layout(
        barmode="group",
        height=320,
        xaxis_title="Stock",
        yaxis_title="Amount (₹)",
        margin=dict(l=12, r=12, t=16, b=36),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        autosize=True,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
        key="dashboard_investment_comparison_chart",
    )
