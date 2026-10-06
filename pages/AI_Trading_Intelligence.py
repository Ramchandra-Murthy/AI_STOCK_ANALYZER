"""Streamlit page for the separate AI trading intelligence module."""

from __future__ import annotations

import pandas as pd
import streamlit as st
import yfinance as yf

from ai_trading.ai_scanner import scan_universe
from ai_trading.decision_engine import build_signal_decision
from ai_trading.features import build_features
from ai_trading.ml_model import predict_latest, train_model
from ai_trading.ml_scanner import scan_universe as scan_ml_universe
from ai_trading.signal_history import attach_outcomes, record_signal
from ai_trading.walk_forward import walk_forward_backtest
from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES
from services.resilient_market_data import download_symbol_frames

st.set_page_config(page_title="AI Trading Intelligence", page_icon="🧠", layout="wide")

st.title("🧠 AI Trading Intelligence")
st.caption("AI-oriented market feature and signal research. No broker orders are submitted.")

left, right = st.columns(2)
with left:
    exchange = st.selectbox("Exchange", ["NSE", "BSE"])
    universe = NSE_CANDIDATES if exchange == "NSE" else BSE_CANDIDATES
    count = st.slider("Symbols to scan", 10, min(50, len(universe)), 20, 5)
with right:
    period = st.selectbox("Training / analysis history", ["6mo", "1y", "2y"], index=1)

if st.button("Run AI Trading Scan", type="primary"):
    with st.spinner(f"Analyzing {count} {exchange} symbols..."):
        result = scan_universe(universe[:count], exchange=exchange, period=period)

    diagnostics = result.attrs.get("scan_diagnostics", {})
    if result.empty:
        missing = diagnostics.get("missing", [])
        detail = f" Missing/unresolved: {len(missing)} symbols." if missing else ""
        st.error("AI scan returned no usable market data after bounded retries." + detail)
        st.caption(
            "No signal was generated from missing or synthetic data; " "retry during market hours."
        )
        st.stop()

    usable = diagnostics.get("usable", len(result))
    requested = diagnostics.get("requested", count)
    if usable < requested:
        st.warning(
            f"Partial market-data coverage: {usable}/{requested} symbols. "
            "Results are research-only until coverage is complete."
        )
    else:
        st.success(f"Analyzed {len(result)} symbols with complete market-data coverage.")
    st.subheader("AI Trading Opportunities")
    st.dataframe(result.head(10), use_container_width=True, hide_index=True)

    st.subheader("Signal distribution")
    st.bar_chart(result["signal"].value_counts())

    st.subheader("AI confidence")
    st.bar_chart(result.set_index("symbol")["confidence_pct"].head(10))

    st.info(
        "The scanner above is the deterministic baseline. The ML validation panel below "
        "trains a separate leakage-safe model using a chronological holdout; it does not "
        "place broker orders."
    )

st.divider()
st.subheader("🔎 Multi-Stock ML Scanner")
st.caption(
    "Trains a separate leakage-safe model for each selected symbol and combines ML probability, "
    "validation quality, trend and market-regime context into the final AI decision. "
    "When enough completed signal history exists, learned outcome data also adjusts confidence "
    "within a bounded range without changing the signal direction."
)

scan_left, scan_mid, scan_right = st.columns(3)
with scan_left:
    ml_count = st.slider(
        "ML symbols",
        5,
        min(30, len(universe)),
        min(10, len(universe)),
        5,
        key="ml_scan_count",
    )
with scan_mid:
    scan_horizon = st.slider(
        "ML horizon (days)",
        1,
        20,
        5,
        key="ml_scan_horizon",
    )
with scan_right:
    scan_threshold = st.slider(
        "ML threshold (%)",
        0.0,
        5.0,
        1.0,
        0.5,
        key="ml_scan_threshold",
    )

if st.button("Run ML Scanner", type="secondary"):
    with st.spinner(f"Training {ml_count} {exchange} ML models..."):
        result = scan_ml_universe(
            universe[:ml_count],
            exchange=exchange,
            period=period,
            horizon=scan_horizon,
            threshold=scan_threshold / 100.0,
        )
    if result.empty:
        st.warning("No ML predictions were produced for the selected universe.")
    else:
        st.dataframe(result, use_container_width=True, hide_index=True)

st.divider()
st.subheader("🧪 Walk-Forward Backtest")
st.caption(
    "Chronological backtest for one symbol. The model is retrained on each step to avoid "
    "future leakage. Transaction costs are applied per side."
)

bt_left, bt_mid, bt_right = st.columns(3)
with bt_left:
    ml_symbol = st.selectbox("Backtest symbol", universe[: min(50, len(universe))], key="bt_symbol")
    bt_horizon = st.slider("Backtest horizon (days)", 1, 20, 5, key="bt_horizon")
    bt_initial_train = st.slider(
        "Initial training rows",
        100,
        1000,
        252,
        25,
        key="bt_initial_train",
    )
with bt_mid:
    bt_long_probability = st.slider(
        "LONG probability",
        0.50,
        0.90,
        0.55,
        0.01,
        key="bt_long_probability",
    )
    bt_short_probability = st.slider(
        "SHORT probability",
        0.10,
        0.50,
        0.45,
        0.01,
        key="bt_short_probability",
    )
with bt_right:
    bt_threshold = st.slider(
        "Training threshold (%)",
        0.0,
        5.0,
        1.0,
        0.5,
        key="bt_threshold",
    )
    bt_cost = st.slider(
        "Transaction cost (bps/side)",
        0.0,
        50.0,
        10.0,
        1.0,
        key="bt_cost",
    )

if st.button("Run Walk-Forward Backtest", type="primary"):
    ticker = (
        f"{str(ml_symbol).strip().upper()}.NS"
        if exchange == "NSE"
        else f"{str(ml_symbol).strip().upper()}.BO"
    )
    with st.spinner(f"Backtesting {ticker}..."):
        history = yf.download(
            ticker,
            period="5y",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        if isinstance(history.columns, pd.MultiIndex):
            history = history.droplevel(1, axis=1)

    try:
        trades, backtest = walk_forward_backtest(
            history,
            horizon=bt_horizon,
            threshold=bt_threshold / 100.0,
            long_probability=bt_long_probability,
            short_probability=bt_short_probability,
            initial_train=bt_initial_train,
            transaction_cost_bps=bt_cost,
        )
        st.dataframe(trades, use_container_width=True, hide_index=True)
        st.json(backtest)
    except (TypeError, ValueError, KeyError) as exc:
        st.error(f"Backtest could not be completed: {exc}")

st.divider()
st.subheader("🧾 Signal History & Outcome Tracking")
st.caption(
    "Persisted signals are scored against later market outcomes for research and calibration. "
    "No broker orders are submitted."
)

history_left, history_right = st.columns(2)
with history_left:
    if st.button("Record Current AI Signals"):
        current = scan_ml_universe(
            universe[:ml_count],
            exchange=exchange,
            period=period,
            horizon=scan_horizon,
            threshold=scan_threshold / 100.0,
        )
        if current.empty:
            st.warning("No current AI signals available to record.")
        else:
            recorded = record_signal(current)
            st.success(f"Recorded {recorded} signals.")
with history_right:
    if st.button("Update Signal Outcomes"):
        updated = attach_outcomes(exchange=exchange)
        st.success(f"Updated {updated} signal outcomes.")
