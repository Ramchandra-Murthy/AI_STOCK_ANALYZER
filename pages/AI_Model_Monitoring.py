"""Streamlit page for AI model monitoring and calibration."""

from __future__ import annotations

import pandas as pd
import streamlit as st
import yfinance as yf

from ai_trading.calibration import evaluate_calibration
from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES

st.set_page_config(
    page_title="AI Model Monitoring",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 AI Model Monitoring & Calibration")
st.caption(
    "Measure whether ML probabilities are reliable on unseen historical data. "
    "No broker or live orders are submitted."
)

left, right = st.columns(2)
with left:
    exchange = st.selectbox("Exchange", ["NSE", "BSE"])
    universe = NSE_CANDIDATES if exchange == "NSE" else BSE_CANDIDATES
    symbol = st.selectbox("Monitoring symbol", universe[: min(30, len(universe))])
with right:
    horizon = st.slider("Forward horizon (days)", 1, 20, 5)
    threshold = st.slider("Positive-return threshold (%)", 0.0, 5.0, 1.0, 0.5)

bins = st.slider("Calibration bins", 2, 10, 5)

if st.button("Run Model Monitoring", type="primary"):
    ticker = (
        f"{str(symbol).strip().upper()}.NS"
        if exchange == "NSE"
        else f"{str(symbol).strip().upper()}.BO"
    )
    with st.spinner(f"Evaluating {ticker}..."):
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
        metrics, calibration = evaluate_calibration(
            history,
            horizon=horizon,
            threshold=threshold / 100.0,
            bins=bins,
        )
    except (TypeError, ValueError, KeyError) as exc:
        st.error(f"Model monitoring could not run: {exc}")
        st.stop()

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Accuracy", f"{metrics.accuracy:.1%}")
    metric2.metric("Brier score", f"{metrics.brier_score:.3f}")
    metric3.metric("Calibration gap", f"{metrics.calibration_gap:.1%}")
    metric4.metric("Test samples", metrics.test_samples)

    st.subheader("Probability calibration")
    st.dataframe(calibration, use_container_width=True, hide_index=True)

    if not calibration.empty:
        chart = calibration.set_index("predicted_probability")[
            ["actual_rate"]
        ]
        st.line_chart(chart)

    st.subheader("Prediction distribution")
    st.write(
        f"Average predicted probability: **{metrics.average_probability:.1%}** · "
        f"Actual positive rate: **{metrics.actual_positive_rate:.1%}**"
    )

    st.caption(
        "Brier score measures probability error; lower is better. Calibration gap "
        "compares average predicted probability with the observed positive rate on "
        "the chronological holdout. These are historical measurements, not "
        "guarantees of future performance."
    )
