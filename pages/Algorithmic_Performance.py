""""Streamlit dashboard for algorithmic trading performance research."""

from __future__ import annotations

import pandas as pd
import streamlit as st
import yfinance as yf

from algorithmic_trading.signal_backtest import backtest_pipeline


def _download_market_data(ticker: str, benchmark_ticker: str, period: str):
    """Download and normalize one symbol and its benchmark."""
    with st.spinner(f"Loading {ticker} and {benchmark_ticker}..."):
        frame = yf.download(ticker, period=period, auto_adjust=False, progress=False)
        benchmark = yf.download(benchmark_ticker, period=period, auto_adjust=False, progress=False)

    for data in (frame, benchmark):
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

    return frame, benchmark


def _show_results(data: pd.DataFrame, metrics) -> None:
    """Render the historical backtest results."""
    st.subheader("Historical backtest")
    cols = st.columns(6)
    cols[0].metric("Total return", f"{metrics.total_return:.2%}")
    cols[1].metric("CAGR", f"{metrics.cagr:.2%}" if metrics.cagr is not None else "—")
    cols[2].metric("Max drawdown", f"{metrics.max_drawdown:.2%}")
    cols[3].metric("Buy & hold", f"{metrics.buy_hold_return:.2%}")
    cols[4].metric("Trades", metrics.trade_count)
    cols[5].metric("Win rate", f"{metrics.win_rate:.2%}")

    st.subheader("Equity curve")
    st.line_chart(data[["strategy_equity", "buy_hold_equity"]])

    st.subheader("Drawdown")
    st.line_chart(data["drawdown"])

    st.subheader("Backtest observations")
    st.dataframe(data.tail(250), use_container_width=True)


def _run_backtest(
    frame: pd.DataFrame,
    benchmark: pd.DataFrame,
    capital: float,
    cost_bps: float,
):
    """Validate data and run the existing point-in-time backtest."""
    if frame.empty or benchmark.empty:
        st.error("No usable historical market data was returned.")
        return None

    if "Close" not in frame.columns or "Close" not in benchmark.columns:
        st.error("Historical data did not contain a usable Close series.")
        return None

    try:
        return backtest_pipeline(
            frame=frame,
            benchmark=benchmark["Close"],
            initial_capital=capital,
            cost_bps=cost_bps,
        )
    except ValueError as exc:
        st.error(str(exc))
        return None


st.set_page_config(
    page_title="NSE/BSE Algorithmic Performance",
    page_icon="📊",
    layout="wide",
)

st.title("📊 NSE/BSE Algorithmic Performance")
st.caption(
    "Historical signal performance only. Open paper positions are not treated " "as realized P&L."
)

left, right = st.columns(2)
with left:
    exchange = st.selectbox("Exchange", ["NSE", "BSE"])
    symbol = st.text_input("Symbol", "RELIANCE").strip().upper()
    period = st.selectbox("History", ["2y", "5y", "10y"], index=0)
with right:
    capital = st.number_input(
        "Initial capital (₹)", min_value=1_000.0, value=100_000.0, step=10_000.0
    )
    cost_bps = st.number_input(
        "Transaction cost (bps)",
        min_value=0.0,
        max_value=500.0,
        value=10.0,
        step=1.0,
    )
    run = st.button("Run performance analysis", type="primary")

if run:
    ticker = f"{symbol}.NS" if exchange == "NSE" else f"{symbol}.BO"
    benchmark_ticker = "^NSEI" if exchange == "NSE" else "^BSESN"
    frame, benchmark = _download_market_data(ticker, benchmark_ticker, period)
    result = _run_backtest(frame, benchmark, capital, cost_bps)

    if result is not None:
        data, metrics = result
        _show_results(data, metrics)
        st.info(
            "Completed-trade feedback will populate after realized trade records "
            "are connected to the paper-trading ledger."
        )
