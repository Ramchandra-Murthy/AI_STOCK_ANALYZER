"""Streamlit dashboard for simulation-only NIFTY Options V2 paper trading."""

from __future__ import annotations

from datetime import date

import streamlit as st

from engine.nifty_options_v2_auto import NiftyOptionsV2AutoPaper
from engine.nifty_options_v2_auto_cycle import NiftyOptionsV2AutoCycle
from engine.nifty_options_v2_cycle_status import cycle_status
from engine.nifty_options_v2_live import (
    LivePaperObservation,
    NiftyOptionsV2LivePaperSession,
)
from engine.nifty_options_v2_market_data import (
    NiftyV2MarketObservation,
    select_deepest_itm_call,
)
from services.options_analytics import fetch_option_chain
from strategy.nifty_options_v2 import NiftyCallContract

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

st.subheader("Market Data Status")
status_left, status_mid, status_right = st.columns(3)
status_left.metric("Provider", provider.provider_symbol)
status_mid.metric("Data Status", provider.status)
status_right.metric("Spot", f"{provider.spot:.2f}" if provider.spot is not None else "Unavailable")
st.caption(provider.message)
if provider.expiry is not None:
    st.caption(f"Provider-selected expiry: {provider.expiry}")
active = session.trader.active_trade
active_expiry = active.contract.expiry if active is not None else None

cycle = cycle_status(
    expiries=provider.expiries,
    observed_date=date.today(),
    active_contract_expiry=active_expiry,
)
auto_cycle = NiftyOptionsV2AutoCycle(auto_paper=NiftyOptionsV2AutoPaper(session=session))
auto_strike = st.checkbox("Automatically select deepest ITM CALL from option chain", value=True)

if cycle is not None:
    st.subheader("Book V2 Monthly Cycle")
    cycle_left, cycle_mid, cycle_right = st.columns(3)
    cycle_left.metric("Current Monthly Expiry", cycle.current_expiry.isoformat())
    cycle_mid.metric("Next Monthly Expiry", cycle.next_expiry.isoformat())
    cycle_right.metric("Strategy Action", cycle.action.value.upper())
    st.caption(cycle.reason)
else:
    st.info("Monthly cycle status is unavailable.")
    st.caption("Two provider-reported monthly expiries are required.")

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

if st.button("Refresh Live Paper Observation"):
    st.rerun()

automatic_data_ready = provider.status == "AVAILABLE" and not provider.chain.empty\n\nif st.button(\n    "Run Automatic Book V2 Cycle",\n    type="primary",\n    disabled=not automatic_data_ready,\n):
    try:
        if cycle is None:
            st.warning("Automatic cycle unavailable: two monthly expiries are required.")
        else:
            if auto_strike:
                next_provider = fetch_option_chain("NIFTY", cycle.next_expiry.isoformat())
                if next_provider.status != "AVAILABLE" or next_provider.spot is None:
                    raise ValueError(
                        f"Next-series option chain unavailable: {next_provider.message}"
                    )
                market_observation = select_deepest_itm_call(
                    next_provider.chain,
                    spot=next_provider.spot,
                    expiry=cycle.next_expiry,
                    observed_date=observed_date,
                )
                st.info(
                    f"Auto-selected deepest ITM CALL: {market_observation.contract.strike:.0f} "
                    f"@ LTP {market_observation.observation.ltp:.2f}"
                )
            else:
                market_observation = NiftyV2MarketObservation(
                    contract=NiftyCallContract(
                        expiry=cycle.next_expiry,
                        strike=strike,
                    ),
                    observation=observation,
                )
            result = auto_cycle.process(
                expiries=provider.expiries,
                observed_date=observed_date,
                observation=market_observation,
            )
            if result is None:
                st.warning("Automatic cycle could not be evaluated.")
            else:
                st.success(f"Book V2 action: {result.action.value.upper()} — {result.reason}")
    except ValueError as exc:
        st.error(str(exc))

if st.button("Start Paper Trade", type="secondary"):
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
