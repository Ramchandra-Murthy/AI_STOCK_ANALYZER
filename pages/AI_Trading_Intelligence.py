"""Streamlit page for the separate AI trading intelligence module."""

from __future__ import annotations

import pandas as pd
import streamlit as st
import yfinance as yf

from ai_trading.ai_scanner import scan_universe
from ai_trading.ml_model import predict_latest, train_model
from ai_trading.ml_scanner import scan_universe as scan_ml_universe
from ai_trading.walk_forward import walk_forward_backtest
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
st.subheader("🔎 Multi-Stock ML Scanner")
st.caption(
    "Trains a separate leakage-safe model for each selected symbol and ranks "
    "the resulting historical validation and latest probability metrics."
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

if st.button("Run Multi-Stock ML Scan", type="primary"):
    with st.spinner(f"Training {ml_count} {exchange} models..."):
        ml_result = scan_ml_universe(
            universe[:ml_count],
            exchange=exchange,
            period="5y",
            horizon=scan_horizon,
            threshold=scan_threshold / 100.0,
        )

    if ml_result.empty:
        st.warning("No symbols produced a valid ML result.")
    else:
        st.success(f"Validated {len(ml_result)} stock models.")
        st.dataframe(
            ml_result.head(10),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "Ranking is based on model confidence, historical ROC-AUC, and latest "
            "probability. These are historical model measurements, not forecasts "
            "of guaranteed returns."
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

st.divider()
st.subheader("📈 AI Walk-Forward Backtest")
st.caption(
    "Replays the ML strategy chronologically with an expanding training window. "
    "Each test trade uses only information available before entry and holds for the "
    "selected horizon."
)

bt_left, bt_mid, bt_right = st.columns(3)
with bt_left:
    bt_initial_train = st.slider(
        "Initial training bars",
        60,
        300,
        100,
        20,
        key="bt_initial_train",
    )
    bt_long_probability = st.slider(
        "LONG probability",
        0.50,
        0.90,
        0.55,
        0.01,
        key="bt_long_probability",
    )
with bt_mid:
    bt_horizon = st.slider(
        "Backtest horizon (days)",
        1,
        20,
        5,
        key="bt_horizon",
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
    except (TypeError, ValueError, KeyError) as exc:
        st.error(f"Walk-forward backtest could not run: {exc}")
    else:
        metric1, metric2, metric3, metric4, metric5 = st.columns(5)
        metric1.metric("Total return", f"{backtest.total_return:.1%}")
        metric2.metric("Max drawdown", f"{backtest.max_drawdown:.1%}")
        metric3.metric("Trades", backtest.trades)
        metric4.metric("Win rate", f"{backtest.win_rate:.1%}")
        metric5.metric(
            "Profit factor",
            f"{backtest.profit_factor:.2f}" if backtest.profit_factor is not None else "N/A",
        )

        chart = trades.set_index("exit_index")[["equity"]]
        st.line_chart(chart)
        st.dataframe(
            trades[
                [
                    "entry_index",
                    "exit_index",
                    "signal",
                    "probability_up",
                    "entry_price",
                    "exit_price",
                    "net_return",
                    "equity",
                    "drawdown",
                ]
            ].tail(25),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "This is a historical simulation, not a live strategy or a guarantee "
            "of future performance. Transaction costs are applied on entry and exit; "
            "slippage, taxes, and liquidity effects are not modeled."
        )
