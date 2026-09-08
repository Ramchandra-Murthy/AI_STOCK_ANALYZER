import streamlit as st

from portfolio.portfolio import delete_stock


def _format_currency(value):
    """Format currency safely when value is None."""
    if value is None:
        return "₹—"

    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "₹—"


def _format_percent(value):
    """Format percentage safely when value is None."""
    if value is None:
        return "—"

    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "—"


def show_top_holdings(df, top_n=5):
    """
    Display Top Holdings.
    """

    if df.empty:
        st.info("No holdings available.")
        return

    table = df.sort_values(
        by="Current Value",
        ascending=False
    ).head(top_n).copy()

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

    display["Buy Price"] = display["Buy Price"].map(_format_currency)
    display["CMP"] = display["CMP"].map(_format_currency)
    display["Current Value"] = display["Current Value"].map(_format_currency)
    display["Profit"] = display["Profit"].map(_format_currency)
    display["Return %"] = display["Return %"].map(_format_percent)

    st.dataframe(
        display,
        width="stretch",
        hide_index=True,
    )

    st.divider()

    # ----------------------------
    # Delete Holding
    # ----------------------------

    col1, col2 = st.columns([3, 1])

    with col1:

        selected = st.selectbox(
            "Delete Holding",
            table["id"],
            format_func=lambda x: table.loc[
                table["id"] == x,
                "symbol"
            ].iloc[0],
        )

    with col2:

        st.write("")
        st.write("")

        if st.button(
            "🗑 Delete",
            width="stretch",
        ):
            delete_stock(selected)
            st.success("Holding deleted.")
            st.rerun()