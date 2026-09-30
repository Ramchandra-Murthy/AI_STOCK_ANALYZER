"""Streamlit page for the separate AI trading intelligence module."""

from __future__ import annotations

import pandas as pd
import streamlit as st
import yfinance as yf

from ai_trading.ai_scanner import scan_universe
from ai_trading.ml_model import predict_latest, train_model
from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES

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

    if result.empty:
        st.warning("No usable market data was returned.")
        st.stop()

    st.success(f"Analyzed {len(result)} symbols.")
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
st.subheader("🤖 ML Model Validation")
st.caption(
    "Train and validate a directional classifier on one symbol before using ML signals "
    "in a broader scanner."
)

ml_left, ml_mid, ml_right = st.columns(3)
with ml_left:
    ml_symbol = st.selectbox("Training symbol", universe[: min(30, len(universe))])
with ml_mid:
    horizon = st.slider("Forward horizon (days)", 1, 20, 5)
with ml_right:
    threshold_pct = st.slider("Positive-return threshold", 0.0, 5.0, 1.0, 0.5)

if st.button("Train & Validate ML Model", type="secondary"):
    ticker = (
        f"{str(ml_symbol).strip().upper()}.NS"
        if exchange == "NSE"
        else f"{str(ml_symbol).strip().upper()}.BO"
    )
    with st.spinner(f"Training on {ticker}..."):
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
        model, validation = train_model(
            history,
            horizon=horizon,
            threshold=threshold_pct / 100.0,
        )
        prediction = predict_latest(model, history)
    except (TypeError, ValueError, KeyError) as exc:
        st.error(f"ML validation could not run: {exc}")
    else:
        metric1, metric2, metric3, metric4 = st.columns(4)
        metric1.metric("Accuracy", f"{validation.accuracy:.1%}")
        metric2.metric(
            "ROC-AUC",
            f"{validation.roc_auc:.3f}" if validation.roc_auc is not None else "N/A",
        )
        metric3.metric("Train samples", validation.train_samples)
        metric4.metric("Test samples", validation.test_samples)

        st.write(
            f"Latest ML signal: **{prediction['signal']}** · "
            f"Probability up: **{float(prediction['probability_up']):.1%}** · "
            f"Model confidence: **{float(prediction['confidence']):.1%}**"
        )
        st.caption(
            "Validation uses earlier observations for training and later observations "
            "for testing. Metrics are historical validation measurements, not guarantees "
            "of future trading performance."
        )
