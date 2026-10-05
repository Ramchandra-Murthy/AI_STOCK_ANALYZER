"""Streamlit dashboard for simulation-only NIFTY Options V2 paper trading."""

from __future__ import annotations

from datetime import date

import streamlit as st

from engine.nifty_options_v2_cycle_status import cycle_status
from engine.nifty_options_v2_live import (
    LivePaperObservation,
    NiftyOptionsV2LivePaperSession,
)
from services.options_analytics import fetch_option_chain

st.set_page_config(page_title="NIFTY V2 Paper Trading", page_icon="📈", layout="wide")

st.title("NIFTY Options V2 — Paper Trading")
st.caption(
    "Simulation only. Enter current market observations manually. "
    "This page never submits broker orders."
)

if "nifty_v2_paper_session" not in st.session_state:
    st.session_state.nifty_v2_paper_session = NiftyOptionsV2LivePaperSession()

session: NiftyOptionsV2LivePaperSession = st.session_state.nifty_v2_paper_session

provider = fetch_option_chain("NIFTY")
active = session.trader.active_trade
active_expiry = active.contract.expiry if active is not None else None

cycle = cycle_status(
    expiries=provider.expiries,
    observed_date=date.today(),
    active_contract_expiry=active_expiry,
)

if cycle is not None:
    st.subheader("Book V2 Monthly Cycle")
    cycle_left, cycle_mid, cycle_right = st.columns(3)
    cycle_left.metric("Current Monthly Expiry", cycle.current_expiry.isoformat())
    cycle_mid.metric("Next Monthly Expiry", cycle.next_expiry.isoformat())
    cycle_right.metric("Strategy Action", cycle.action.value.upper())
    st.caption(cycle.reason)
else:
    st.info("Monthly cycle status is unavailable until two provider-reported monthly expiries exist.")

left, right = st.columns(2)

with left:
    expiry = st.date_input("Option expiry", value=date.today())
    strike = st.number_input("CALL strike", min_value=1.0, value=25000.0, step=50.0)

with right:
    observed_date = st.date_input("Observation date", value=date.today())
    spot = st.number_input("NIFTY spot", min_value=0.01, value=25000.0, step=1.0)
    ltp = st.number_input("CALL LTP", min_value=0.0, value=500.0, step=0.05)

observation = LivePaperObservation(
    observed_date=observed_date,
    spot=spot,
    ltp=ltp,
)

if st.button("Start Paper Trade", type="primary"):
    try:
        session.start(expiry=expiry, strike=strike, observation=observation)
        st.success("Paper trade started. No broker order was submitted.")
    except ValueError as exc:
        st.error(str(exc))

active = session.trader.active_trade
if active is not None:
    st.subheader("Active Paper Trade")
    st.write(
        {
            "expiry": active.contract.expiry.isoformat(),
            "strike": active.contract.strike,
            "entry_date": active.entry_date.isoformat(),
            "entry_ltp": active.entry_ltp,
            "current_ltp": ltp,
            "unrealized_points": ltp - active.entry_ltp,
        }
    )

    if st.button("Close Paper Trade"):
        try:
            closed = session.close(observation)
            st.success(f"Paper trade closed: {closed.points_pnl:.2f} points")
        except ValueError as exc:
            st.error(str(exc))

if session.trader.completed_trades:
    st.subheader("Completed Paper Trades")
    st.dataframe(
        [
            {
                "Expiry": trade.contract.expiry,
                "Strike": trade.contract.strike,
                "Entry": trade.entry_ltp,
                "Exit": trade.exit_ltp,
                "Points P&L": trade.points_pnl,
            }
            for trade in session.trader.completed_trades
        ],
        use_container_width=True,
    )
