"""Create, edit, select and delete reusable trading profiles."""

from __future__ import annotations

import streamlit as st

from algorithmic_trading.trading_profile import TradingProfile
from services.trading_profile_store import (
    TradingProfileStoreError,
    delete_profile,
    list_profiles,
    load_profile,
    save_profile,
)

st.set_page_config(page_title="Trading Profiles", page_icon="🛡️", layout="wide")
st.title("🛡️ Trading Profiles")
st.caption(
    "Save reusable risk settings locally. These profiles calculate research position sizes; they do not place orders."
)

try:
    names = list_profiles()
except TradingProfileStoreError as exc:
    st.error(str(exc))
    st.stop()

selected = st.selectbox("Saved profile", ["New profile", *names])
if selected == "New profile":
    profile = TradingProfile()
else:
    try:
        profile = load_profile(selected)
    except TradingProfileStoreError as exc:
        st.error(str(exc))
        st.stop()

with st.form("trading_profile_form"):
    name = st.text_input("Profile name", value=profile.name, max_chars=80)
    c1, c2, c3 = st.columns(3)
    style = c1.selectbox(
        "Trading style",
        ["intraday", "swing", "positional", "long_term"],
        index=["intraday", "swing", "positional", "long_term"].index(profile.style),
    )
    exchange = c2.selectbox(
        "Exchange", ["NSE", "BSE", "BOTH"], index=["NSE", "BSE", "BOTH"].index(profile.exchange)
    )
    timeframe = c3.text_input("Timeframe", value=profile.timeframe)
    c1, c2, c3 = st.columns(3)
    capital = c1.number_input(
        "Capital (₹)", min_value=1.0, value=float(profile.capital), step=1000.0
    )
    risk_mode = c2.selectbox(
        "Risk mode", ["percent", "fixed"], index=["percent", "fixed"].index(profile.risk_mode)
    )
    risk_value = c3.number_input(
        "Risk value (% or ₹)", min_value=0.01, value=float(profile.risk_value), step=0.1
    )
    c1, c2, c3 = st.columns(3)
    max_daily_loss_pct = c1.number_input(
        "Maximum daily loss (%)",
        min_value=0.01,
        max_value=100.0,
        value=float(profile.max_daily_loss_pct),
        step=0.25,
    )
    max_positions = c2.number_input(
        "Maximum positions", min_value=1, max_value=100, value=int(profile.max_positions), step=1
    )
    max_position_pct = c3.number_input(
        "Maximum position (%)",
        min_value=0.01,
        max_value=100.0,
        value=float(profile.max_position_pct),
        step=1.0,
    )
    c1, c2, c3 = st.columns(3)
    max_exposure_pct = c1.number_input(
        "Maximum exposure (%)",
        min_value=0.01,
        max_value=100.0,
        value=float(profile.max_exposure_pct),
        step=1.0,
    )
    cash_reserve_pct = c2.number_input(
        "Cash reserve (%)",
        min_value=0.0,
        max_value=99.99,
        value=float(profile.cash_reserve_pct),
        step=1.0,
    )
    estimated_round_trip_cost_pct = c3.number_input(
        "Estimated round-trip cost (%)",
        min_value=0.0,
        value=float(profile.estimated_round_trip_cost_pct),
        step=0.05,
    )
    c1, c2 = st.columns(2)
    stop_mode = c1.selectbox(
        "Stop policy",
        ["fixed", "percentage", "atr", "technical"],
        index=["fixed", "percentage", "atr", "technical"].index(profile.stop_mode),
    )
    stop_value = c2.number_input(
        "Stop value (₹ / % / ATR multiple)",
        min_value=0.01,
        value=float(profile.stop_value),
        step=0.1,
    )
    allow_short = st.checkbox("Allow short selling", value=bool(profile.allow_short))
    save_clicked = st.form_submit_button("Save profile", type="primary")

if save_clicked:
    try:
        updated = TradingProfile(
            name=name.strip(),
            style=style,
            exchange=exchange,
            timeframe=timeframe.strip(),
            capital=float(capital),
            risk_mode=risk_mode,
            risk_value=float(risk_value),
            max_daily_loss_pct=float(max_daily_loss_pct),
            max_positions=int(max_positions),
            max_position_pct=float(max_position_pct),
            max_exposure_pct=float(max_exposure_pct),
            cash_reserve_pct=float(cash_reserve_pct),
            stop_mode=stop_mode,
            stop_value=float(stop_value),
            allow_short=bool(allow_short),
            estimated_round_trip_cost_pct=float(estimated_round_trip_cost_pct),
        )
        save_profile(updated)
    except (ValueError, TradingProfileStoreError) as exc:
        st.error(f"Profile not saved: {exc}")
    else:
        st.success(f"Profile '{updated.name}' saved.")
        st.rerun()

if names and selected != "New profile":
    st.divider()
    if st.button("Delete selected profile", type="secondary"):
        try:
            delete_profile(selected)
        except TradingProfileStoreError as exc:
            st.error(str(exc))
        else:
            st.success(f"Deleted '{selected}'.")
            st.rerun()

st.info(
    "Storage: local SQLite database. For persistent deployments, set TRADING_PROFILES_DATABASE_PATH to a durable writable path. Do not expose this single-user app publicly without adding authentication and per-user access controls."
)
