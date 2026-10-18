import streamlit as st

from portfolio.portfolio import delete_stock


def show_top_holdings(df, top_n=5):
    """
    Display Top Holdings.
    """

    if df.empty:
        st.info("No holdings available.")
        return

    valued_df = df.dropna(subset=["Current Value"])
    unpriced_count = len(df) - len(valued_df)
    if valued_df.empty:
        st.info("Top holdings are unavailable because no holdings have current prices.")
        return
    if unpriced_count:
        st.caption(f"Showing valued holdings only; {unpriced_count} holding(s) have unavailable prices.")

    table = valued_df.sort_values(by="Current Value", ascending=False).head(top_n).copy()

    # ----------------------------
    # Format numbers
    # ----------------------------

    display = table[
        [
            "symbol",
            "quantity",
            "buy_price",
            "CMP",
            "Current Value",
            "Profit",
            "Return %",
        ]
    ].copy()

    display.columns = [
        "Symbol",
        "Qty",
        "Buy Price",
        "CMP",
        "Current Value",
        "Profit",
        "Return %",
    ]

    display["Buy Price"] = display["Buy Price"].map(lambda x: f"₹{x:,.2f}")
    display["CMP"] = display["CMP"].map(lambda x: f"₹{x:,.2f}")
    display["Current Value"] = display["Current Value"].map(lambda x: f"₹{x:,.2f}")
    display["Profit"] = display["Profit"].map(lambda x: f"₹{x:,.2f}")
    display["Return %"] = display["Return %"].map(lambda x: f"{x:.2f}%")

    st.dataframe(display, use_container_width=True, hide_index=True)

    st.divider()

    # ----------------------------
    # Delete Holding
    # ----------------------------

    col1, col2 = st.columns([3, 1])

    with col1:

        selected = st.selectbox(
            "Delete Holding",
            table["id"],
            format_func=lambda x: table.loc[table["id"] == x, "symbol"].iloc[0],
        )

    with col2:

        st.write("")
        st.write("")

        if st.button("🗑 Delete", use_container_width=True):
            delete_stock(selected)
            st.success("Holding deleted.")
            st.rerun()
