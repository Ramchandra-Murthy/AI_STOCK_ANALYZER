"""Streamlit dashboard for simulation-only NIFTY Options V2 paper trading."""

from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from engine.nifty_options_v2_live import LivePaperObservation, NiftyOptionsV2LivePaperSession
from engine.nifty_options_v2_market_data import select_deepest_itm_call
from engine.nifty_options_v2_refresh import is_market_hours, refresh_seconds
from services.options_analytics import fetch_option_chain

st.set_page_config(page_title="NIFTY V2 Paper Trading", page_icon="📈", layout="wide")

st.title("NIFTY Options V2 — Paper Trading")
st.caption(
    "Simulation only. Live observations refresh during NSE market hours. "
    "This page never submits broker orders."
)

if "nifty_v2_paper_session" not in st.session_state:
    st.session_state.nifty_v2_paper_session = NiftyOptionsV2LivePaperSession()

session: NiftyOptionsV2LivePaperSession = st.session_state.nifty_v2_paper_session


@st.fragment(run_every=f"{refresh_seconds()}s")
def show_live_observation() -> None:
    """Refresh the current NIFTY option observation without placing orders."""
    now = datetime.now().astimezone()
    if not is_market_hours(now):
        st.info("NSE market is outside configured market hours. Paper refresh is paused.")
        return

    try:
        result = fetch_option_chain("NIFTY")
        if result.status != "AVAILABLE" or result.spot is None or result.expiry is None:
            st.warning(f"Live option data unavailable: {result.message}")
            return

        expiry = date.fromisoformat(result.expiry)
        selected = select_deepest_itm_call(
            result.chain,
            spot=result.spot,
            expiry=expiry,
            observed_date=now.date(),
        )
        st.metric("NIFTY Spot", f"{result.spot:.2f}")
        st.metric(
            f"Selected ITM CALL {selected.contract.strike:.0f}",
            f"{selected.observation.ltp:.2f}",
        )

        active = session.trader.active_trade
        if active is not None:
            current_ltp = selected.observation.ltp
            st.metric(
                "Paper Unrealized P&L",
                f"{current_ltp - active.entry_ltp:+.2f} points",
            )
    except (ValueError, RuntimeError) as exc:
        st.warning(f"Live refresh failed: {exc}")


show_live_observation()

with st.expander("Manual paper controls"):
    expiry = st.date_input("Option expiry", value=date.today())
    strike = st.number_input("CALL strike", min_value=1.0, value=25000.0, step=50.0)
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

    if st.button("Close Paper Trade"):
        try:
            closed = session.close(observation)
            st.success(f"Paper trade closed: {closed.points_pnl:.2f} points")
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
        }
    )

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
