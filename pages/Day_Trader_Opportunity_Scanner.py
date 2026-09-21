"""Streamlit page for objective intraday opportunity screening."""

import pandas as pd
import streamlit as st

from scanner.day_trader_opportunity import scan_day_trader_opportunities
from services.intraday_auto_refresh import (
    ALLOWED_REFRESH_SECONDS,
    DEFAULT_REFRESH_SECONDS,
    market_is_open,
    next_refresh_seconds,
    refresh_label,
)
from services.intraday_dynamic_filter import filter_intraday_candidates
from services.intraday_health import assess_scan_health
from services.intraday_health_history import (
    health_history_frame,
    record_health_observation,
)
from services.intraday_multi_window import multi_window_frame, record_multi_window_outcomes
from services.intraday_quality_dashboard import dashboard_summary
from services.intraday_risk_planning import risk_plan_frame
from services.intraday_session import reset_intraday_session
from services.intraday_setup_evaluation import setup_statistics
from services.intraday_setup_monitor import monitor_frame, record_setup_observations
from services.intraday_setup_outcome import outcomes_frame, record_setup_outcomes
from services.intraday_setup_regime import regime_statistics
from services.intraday_state_history import (
    record_setup_state_transitions,
    transitions_frame,
)
from services.market_status import describe_market_status

st.set_page_config(
    page_title="Day-Trader Opportunity Scanner",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ Day-Trader Opportunity Scanner")
control_left, control_right = st.columns([3, 1])
with control_left:
    st.caption(
        "Session data is local to this Streamlit session and should be refreshed for a new "
        "trading session."
    )
with control_right:
    if st.button("Reset intraday session", type="secondary"):
        reset_intraday_session(st.session_state)
        st.rerun()

st.caption(
    "Ranks observable intraday momentum, volume, range and breakout conditions. "
    "It is a screening tool, not a profit predictor or trade instruction."
)

st.info(
    "The scanner rescans the selected NSE/BSE candidate universe on each run. "
    "Results can change as intraday price, volume and setup conditions change. "
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
    cap_category = st.selectbox(
        "Market-cap basket",
        ["All caps", "Large cap", "Mid cap", "Small cap"],
    )
with right:
    price_limit = st.selectbox(
        "Low-price threshold",
        [10.0, 20.0, 50.0, 100.0],
        index=2,
        format_func=lambda value: f"₹{value:g}",
    )
lookback = st.selectbox("Momentum window", [2, 3, 5], index=2)

low_price_only = st.checkbox(
    "Show low-price candidates only",
    value=False,
    help="Filter the ranked results to stocks at or below the selected threshold.",
)
limit = st.selectbox("Maximum results", [10, 20, 30, 50], index=1)
min_change = st.slider("Minimum price change (%)", 0.25, 3.0, 0.5, 0.25)
min_volume = st.slider("Minimum volume surge (x)", 1.0, 5.0, 1.2, 0.1)
refresh_left, refresh_right = st.columns(2)
with refresh_left:
    auto_refresh = st.checkbox(
        "Auto-refresh and rescan",
        value=False,
        help="Refreshes the intraday scan at the selected interval during NSE market hours.",
    )
with refresh_right:
    refresh_interval = st.selectbox(
        "Refresh interval",
        list(ALLOWED_REFRESH_SECONDS),
        index=list(ALLOWED_REFRESH_SECONDS).index(DEFAULT_REFRESH_SECONDS),
        format_func=lambda value: f"{value // 60} minute" + ("s" if value != 60 else ""),
    )
exclude_flagged = st.checkbox(
    "Exclude known NSE surveillance flags",
    value=True,
    help=(
        "Removes NSE candidates carrying a known surveillance indicator in the "
        "latest available REG_IND archive. BSE candidates remain marked for manual "
        "review."
    ),
)

scan_requested = st.button("Scan now", type="primary")
auto_scan_requested = st.session_state.pop("intraday_auto_refresh_pending", False)

if scan_requested or auto_scan_requested:
    with st.spinner("Scanning the current NSE+BSE candidate universe…"):
        results = scan_day_trader_opportunities(
            limit=100,
            exchange_category=exchange,
            cap_category=cap_category,
            max_price=price_limit,
            lookback_minutes=lookback,
            min_change_percent=min_change,
            min_volume_surge=min_volume,
            low_price_only=low_price_only,
        )
    results = results.head(limit).reset_index(drop=True)
    st.session_state["day_trader_opportunities"] = results
    scan_at = pd.Timestamp.now(tz="Asia/Kolkata")
    st.session_state["intraday_last_scan_at"] = scan_at
    scan_health = assess_scan_health(results, scan_at.to_pydatetime())
    health_history = st.session_state.get("intraday_health_history", [])
    st.session_state["intraday_health_history"] = record_health_observation(
        health_history,
        scan_health,
        scan_at.to_pydatetime(),
    )
    previous_states = st.session_state.get("intraday_setup_states", {})
    updated_states, transitions = record_setup_state_transitions(
        previous_states,
        results,
        pd.Timestamp.now(tz="Asia/Kolkata").to_pydatetime(),
    )
    st.session_state["intraday_setup_states"] = updated_states
    previous_monitor = st.session_state.get("intraday_setup_monitor", {})
    st.session_state["intraday_setup_monitor"] = record_setup_observations(
        previous_monitor,
        results,
        pd.Timestamp.now(tz="Asia/Kolkata").to_pydatetime(),
    )
    previous_outcomes = st.session_state.get("intraday_setup_outcomes", {})
    st.session_state["intraday_setup_outcomes"] = record_setup_outcomes(
        previous_outcomes,
        results,
        pd.Timestamp.now(tz="Asia/Kolkata").to_pydatetime(),
    )
    previous_windows = st.session_state.get("intraday_multi_window_outcomes", {})
    st.session_state["intraday_multi_window_outcomes"] = record_multi_window_outcomes(
        previous_windows,
        results,
        pd.Timestamp.now(tz="Asia/Kolkata").to_pydatetime(),
    )
    history = st.session_state.get("intraday_state_transitions", [])
    st.session_state["intraday_state_transitions"] = transitions + history

raw_results = st.session_state.get("day_trader_opportunities")
last_scan_at = st.session_state.get("intraday_last_scan_at")
if last_scan_at is not None:
    st.caption(f"Last scan: {pd.Timestamp(last_scan_at).strftime('%d %b %Y, %H:%M:%S IST')}")

health = assess_scan_health(
    raw_results,
    pd.Timestamp(last_scan_at).to_pydatetime() if last_scan_at is not None else None,
)
if health["status"] == "HEALTHY":
    st.success(f"Data health: {health['message']}")
elif health["status"] == "STALE":
    st.warning(f"Data health: {health['message']} Re-scan before reviewing candidates.")
elif health["status"] != "NO_SCAN":
    st.warning(f"Data health: {health['message']}")

health_history = health_history_frame(st.session_state.get("intraday_health_history", []))
st.subheader("Intraday scan health history")
st.caption(
    "This session-local history records the descriptive health state of each completed scan. "
    "It does not assess trade quality or predict market outcomes."
)
if health_history.empty:
    st.caption("No completed scan health observations are available yet.")
else:
    st.dataframe(health_history.head(50), use_container_width=True, hide_index=True)
    st.download_button(
        "Download scan health history CSV",
        health_history.to_csv(index=False).encode("utf-8"),
        file_name="intraday_scan_health_history.csv",
        mime="text/csv",
    )

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

    quality_summary = dashboard_summary(
        st.session_state.get("intraday_setup_states", {}),
        st.session_state.get("intraday_setup_monitor", {}),
        st.session_state.get("intraday_setup_outcomes", {}),
        st.session_state.get("intraday_state_transitions", []),
        st.session_state.get("intraday_multi_window_outcomes", {}),
    )

    filter_left, filter_mid, filter_right = st.columns(3)
    with filter_left:
        live_direction = st.selectbox(
            "Live direction filter",
            ["All", "LONG", "SHORT", "NEUTRAL"],
        )
    with filter_mid:
        live_state_options = ["All"]
        if "Plan state" in results.columns:
            live_state_options.extend(sorted(results["Plan state"].dropna().astype(str).unique()))
        live_state = st.selectbox("Live setup-state filter", live_state_options)
    with filter_right:
        live_exchange_options = ["All"]
        if "Exchange" in results.columns:
            live_exchange_options.extend(sorted(results["Exchange"].dropna().astype(str).unique()))
        live_exchange = st.selectbox("Live exchange filter", live_exchange_options)
    risk_left, risk_right = st.columns(2)
    with risk_left:
        risk_budget = st.number_input(
            "Risk budget per candidate (₹)",
            min_value=0.0,
            value=1000.0,
            step=100.0,
        )
    with risk_right:
        capital_limit = st.number_input(
            "Capital limit per candidate (₹)",
            min_value=0.0,
            value=100000.0,
            step=5000.0,
        )
    minimum_live_score = st.slider(
        "Minimum composite score",
        0.0,
        100.0,
        0.0,
        5.0,
        help="Filters the latest scan; it does not create a new score or predict returns.",
    )
    filtered_results = filter_intraday_candidates(
        results,
        direction=live_direction,
        setup_state=live_state,
        exchange=live_exchange,
        minimum_score=minimum_live_score,
        limit=limit,
    )

    risk_results = risk_plan_frame(
        filtered_results,
        risk_budget=risk_budget,
        capital_limit=capital_limit,
    )

    st.subheader("Intraday quality dashboard")
    st.caption(
        "Consolidated session metrics from the observed setup history. "
        "These metrics describe the current session and do not predict future returns."
    )
    st.dataframe(quality_summary, use_container_width=True, hide_index=True)

    st.subheader("Current opportunity candidates")
    state_counts = (
        filtered_results["Plan state"].value_counts()
        if "Plan state" in filtered_results.columns
        else pd.Series(dtype="int64")
    )
    if not state_counts.empty:
        st.caption(
            "Setup state is a snapshot of the latest observed price versus the calculated "
            "reference levels; it is not a prediction of future price movement."
        )
        metrics = st.columns(min(4, len(state_counts)))
        for column, (state, count) in zip(metrics, state_counts.head(4).items(), strict=False):
            column.metric(str(state), int(count))
    preferred_columns = [
        "Symbol",
        "Exchange",
        "Market-cap basket",
        "Price",
        "5-min change %",
        "Volume surge x",
        "Day-trading setup",
        "Direction",
        "Setup state",
        "Composite score",
        "RVOL",
        "Trend",
        "VWAP",
        "EMA 9/20",
        "Evidence",
        "Plan",
        "Plan state",
        "Entry reference",
        "Stop reference",
        "Target 1",
        "Target 2",
        "Target 3",
        "R:R T1",
        "R:R T2",
        "R:R T3",
        "Breakout",
        "Strategy breakdown",
        "Liquidity",
    ]
    if filtered_results.empty:
        st.warning(
            "No candidates match the current live filters. "
            "Uncheck the filter only if you intend to review the flagged names separately."
        )
    else:
        display_columns = [column for column in preferred_columns if column in results.columns]
        risk_columns = display_columns + [
            column
            for column in [
                "Risk-based quantity",
                "Capital-based quantity",
                "Suggested quantity",
                "Planned capital",
                "Planned risk",
            ]
            if column in risk_results.columns
        ]
        st.dataframe(
            risk_results[risk_columns],
            use_container_width=True,
            hide_index=True,
        )
    st.download_button(
        "Download opportunity CSV",
        risk_results.to_csv(index=False).encode("utf-8"),
        file_name="day_trader_opportunities.csv",
        mime="text/csv",
    )

    transition_history = transitions_frame(st.session_state.get("intraday_state_transitions", []))
    st.subheader("Intraday setup state changes")
    if transition_history.empty:
        st.caption("No setup-state changes have been observed in this session yet.")
    else:
        st.dataframe(transition_history.head(50), use_container_width=True, hide_index=True)
        st.download_button(
            "Download state-change history CSV",
            transition_history.to_csv(index=False).encode("utf-8"),
            file_name="intraday_setup_state_changes.csv",
            mime="text/csv",
        )

    monitor = monitor_frame(
        st.session_state.get("intraday_setup_monitor", {}),
        pd.Timestamp.now(tz="Asia/Kolkata").to_pydatetime(),
    )
    st.subheader("Intraday setup monitoring")
    st.caption(
        "This view shows how long each observed setup has persisted in this Streamlit session. "
        "It records observations; it does not predict future price movement."
    )
    if monitor.empty:
        st.caption("No setup observations are available yet.")
    else:
        st.dataframe(monitor.head(50), use_container_width=True, hide_index=True)
        st.download_button(
            "Download setup monitoring CSV",
            monitor.to_csv(index=False).encode("utf-8"),
            file_name="intraday_setup_monitoring.csv",
            mime="text/csv",
        )

    outcomes = outcomes_frame(st.session_state.get("intraday_setup_outcomes", {}))
    statistics = setup_statistics(st.session_state.get("intraday_setup_outcomes", {}))
    regime = regime_statistics(st.session_state.get("intraday_setup_outcomes", {}))
    st.subheader("Observed setup outcomes")
    st.caption(
        "Price change is measured from the first observation of the current setup state. "
        "It describes observed movement and is not a forecast or performance guarantee."
    )
    if outcomes.empty:
        st.caption("No repeated setup observations are available yet.")
    else:
        st.dataframe(outcomes.head(50), use_container_width=True, hide_index=True)
        st.download_button(
            "Download setup outcome CSV",
            outcomes.to_csv(index=False).encode("utf-8"),
            file_name="intraday_setup_outcomes.csv",
            mime="text/csv",
        )

    window_outcomes = multi_window_frame(st.session_state.get("intraday_multi_window_outcomes", {}))
    st.subheader("Multi-window setup outcomes")
    st.caption(
        "Observed price change is measured from the start of the current setup state. "
        "A window is filled when a later scan reaches that elapsed time."
    )
    if window_outcomes.empty:
        st.caption("No multi-window observations are available yet.")
    else:
        st.dataframe(window_outcomes.head(50), use_container_width=True, hide_index=True)
        st.download_button(
            "Download multi-window outcome CSV",
            window_outcomes.to_csv(index=False).encode("utf-8"),
            file_name="intraday_multi_window_outcomes.csv",
            mime="text/csv",
        )

    st.subheader("Setup evaluation statistics")
    st.caption(
        "These statistics summarize observed session outcomes by setup state. "
        "They are descriptive and are not a prediction or guarantee of future returns."
    )
    if statistics.empty:
        st.caption("Not enough observed outcomes for statistics yet.")
    else:
        st.dataframe(statistics, use_container_width=True, hide_index=True)
        st.download_button(
            "Download setup statistics CSV",
            statistics.to_csv(index=False).encode("utf-8"),
            file_name="intraday_setup_statistics.csv",
            mime="text/csv",
        )

    st.subheader("Session-phase setup analysis")
    st.caption(
        "Observed outcomes are grouped by the session phase in which the setup state "
        "was first observed. This is descriptive session context, not a prediction."
    )
    if regime.empty:
        st.caption("Not enough observations for session-phase analysis yet.")
    else:
        st.dataframe(regime, use_container_width=True, hide_index=True)
        st.download_button(
            "Download session-phase statistics CSV",
            regime.to_csv(index=False).encode("utf-8"),
            file_name="intraday_session_phase_statistics.csv",
            mime="text/csv",
        )

    st.caption(
        "Entry, stop and target columns are conditional reference levels calculated from "
        "the current setup, support/resistance and ATR. They are not guaranteed execution "
        "levels and should be rechecked against live market data. "
    )
    st.caption(
        "Composite score combines the existing opportunity score with the book-based "
        "day-trading setup score. Higher scores describe more observed conditions; they "
        "do not imply a higher probability of profit. "
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

if auto_refresh:
    @st.fragment(run_every=30)
    def intraday_auto_refresh_fragment():
        last_scan = st.session_state.get("intraday_last_scan_at")
        remaining = next_refresh_seconds(last_scan, refresh_interval)
        if not market_is_open():
            st.info("Auto-refresh paused: NSE market is closed.")
            return
        st.caption(f"🔄 Auto-refresh active • next scan in {refresh_label(remaining)}")
        if remaining <= 0:
            st.session_state["intraday_auto_refresh_pending"] = True
            st.rerun()

    intraday_auto_refresh_fragment()

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
