"""Streamlit page for objective intraday opportunity screening."""

import pandas as pd
import streamlit as st

from scanner.day_trader_opportunity import scan_day_trader_opportunities
from services.market_status import describe_market_status

st.set_page_config(page_title="Day-Trader Opportunity Scanner", page_icon="⚡", layout="wide")

st.title("⚡ Day-Trader Opportunity Scanner")
st.caption(
    "Ranks observable intraday momentum, volume, range and breakout conditions. "
    "It is a screening tool, not a profit predictor or trade instruction."
)

st.info(
    "Low-priced stocks are shown using a configurable price threshold. "
    "There is no universal formal definition of a penny stock. "
    "The current candidate universe is limited to the symbols maintained by this app."
)

left, middle, right = st.columns(3)
with left:
    exchange = st.selectbox(
        "Exchange",
        ["Both", "NSE", "BSE"],
        format_func=lambda value: "NSE + BSE" if value == "Both" else value,
    )
with middle:
    price_limit = st.selectbox(
        "Low-price threshold",
        [10.0, 20.0, 50.0, 100.0],
        index=2,
        format_func=lambda value: f"₹{value:g}",
    )
with right:
    lookback = st.selectbox("Momentum window", [2, 3, 5], index=2)

low_price_only = st.checkbox(
    "Show low-price candidates only",
    value=False,
    help="Filter the ranked results to stocks at or below the selected threshold.",
)
limit = st.selectbox("Maximum results", [10, 20, 30, 50], index=1)
min_change = st.slider("Minimum price change (%)", 0.25, 3.0, 0.5, 0.25)
min_volume = st.slider("Minimum volume surge (x)", 1.0, 5.0, 1.2, 0.1)
exclude_flagged = st.checkbox(
    "Exclude known NSE surveillance flags",
    value=True,
    help=(
        "Removes NSE candidates carrying a known surveillance indicator in the "
        "latest available REG_IND archive. BSE candidates remain marked for manual "
        "review."
    ),
)

if st.button("Scan now", type="primary"):
    with st.spinner("Scanning the current NSE+BSE candidate universe…"):
        results = scan_day_trader_opportunities(
            limit=100,
            exchange_category=exchange,
            max_price=price_limit,
            lookback_minutes=lookback,
            min_change_percent=min_change,
            min_volume_surge=min_volume,
            low_price_only=low_price_only,
        )
    results = results.head(limit).reset_index(drop=True)
    st.session_state["day_trader_opportunities"] = results

raw_results = st.session_state.get("day_trader_opportunities")
if raw_results is None:
    st.info("Run a scan during market hours to populate the opportunity table.")
elif raw_results.empty:
    st.warning(
        "No candidates met the selected conditions. Try a lower threshold or scan again "
        "when intraday volume is active."
    )
else:
    results = raw_results.copy()
    if "Latest candle" in results.columns:
        observed = pd.to_datetime(results["Latest candle"], errors="coerce").dropna()
        if not observed.empty:
            status = describe_market_status(observed.max())
            st.info(f"**{status['label']}**\n\n{status['message']}")
    if exclude_flagged and "Safety flags" in results.columns:
        results = results[results["Safety flags"].fillna("").eq("")].copy()

    st.subheader("Current opportunity candidates")
    if results.empty:
        st.warning(
            "All scanned candidates were removed by the surveillance safety filter. "
            "Uncheck the filter only if you intend to review the flagged names separately."
        )
    else:
        st.dataframe(results, use_container_width=True, hide_index=True)
    st.download_button(
        "Download opportunity CSV",
        results.to_csv(index=False).encode("utf-8"),
        file_name="day_trader_opportunities.csv",
        mime="text/csv",
    )

    st.caption(
        "Opportunity score is descriptive: momentum 35%, volume surge 30%, session "
        "range 20%, breakout condition 15%. A higher score does not imply a higher "
        "probability of profit."
    )
    st.caption(
        "Safety status is a screening aid, not a clearance. NSE flags come from the "
        "latest available REG_IND archive; BSE candidates require a separate exchange check."
    )

st.divider()
st.subheader("Risk and data checks")
st.markdown("""
- Verify the latest candle timestamp before acting; Yahoo Finance may be delayed or incomplete.
- The safety filter checks the latest available NSE surveillance indicator archive (ASM/GSM/ESM and Trade-to-Trade where reported).
- Price bands, bid/ask spreads and BSE surveillance status still require broker/exchange confirmation.
- NSE surveillance measures can change after the archive snapshot; re-check before placing an order.
- Low price is not the same as low risk. A ₹10 stock can be substantially harder to trade than a liquid higher-priced stock.
- The scanner does not calculate guaranteed entries, targets or stop-losses and does not place trades.
""")
st.caption(
    "Use the results as candidates for further chart/order-book review and paper trading, "
    "not as guaranteed money-making selections."
)
