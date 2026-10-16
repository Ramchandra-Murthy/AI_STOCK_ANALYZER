"""Streamlit interface for the research-only Fibonacci-Gann backtest tools."""

from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st

from modules.fibonacci_gann.backtest import BacktestConfig, Candle, run_backtest
from modules.fibonacci_gann.parameter_sensitivity import evaluate_parameter_sensitivity
from modules.fibonacci_gann.regime_robustness import evaluate_regime_robustness

st.set_page_config(page_title="Fibonacci-Gann Research Lab", page_icon="📐", layout="wide")
st.title("📐 Fibonacci-Gann Research Lab")
st.caption(
    "Research-only historical analysis using your uploaded OHLC and signal data. "
    "No live market-data requests or broker orders are made by this page."
)
st.warning(
    "Backtest results are hypothetical and can be misleading. Check data quality, "
    "signal timing, transaction costs, slippage, and out-of-sample performance before "
    "drawing conclusions. This is not a trade recommendation."
)

with st.expander("CSV format and signal timing", expanded=True):
    st.markdown(
        "Upload a CSV containing **timestamp, open, high, low, close, signal** columns. "
        "The signal must be true/false or 1/0. A signal is assumed known only after that "
        "bar closes; the backtester enters no earlier than the next bar's open. "
        "Rows must be chronological and prices must be valid positive OHLC values."
    )
    st.caption(
        "Regime labels are supplied by you; this page does not automatically classify "
        "trending, sideways, or volatile markets."
    )

uploaded = st.file_uploader("Upload historical CSV", type=["csv"])
if uploaded is None:
    st.info("Upload a CSV to begin. No data is downloaded automatically.")
    st.stop()

try:
    frame = pd.read_csv(BytesIO(uploaded.getvalue()))
except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
    st.error(f"Could not read the CSV: {exc}")
    st.stop()

frame.columns = [str(column).strip().lower() for column in frame.columns]
required = {"timestamp", "open", "high", "low", "close", "signal"}
missing = sorted(required - set(frame.columns))
if missing:
    st.error("Missing required columns: " + ", ".join(missing))
    st.stop()
if len(frame) < 2:
    st.error("The CSV must contain at least two data rows.")
    st.stop()

numeric_columns = ["open", "high", "low", "close"]
for column in numeric_columns:
    frame[column] = pd.to_numeric(frame[column], errors="coerce")
signal_text = frame["signal"].astype(str).str.strip().str.lower()
signal_map = {"true": True, "false": False, "1": True, "0": False}
if not signal_text.isin(signal_map).all():
    st.error("The signal column must contain only true/false or 1/0 values.")
    st.stop()
frame["signal"] = signal_text.map(signal_map)
frame["timestamp"] = frame["timestamp"].astype(str).str.strip()

try:
    candles = tuple(
        Candle(
            timestamp=row.timestamp,
            open=float(row.open),
            high=float(row.high),
            low=float(row.low),
            close=float(row.close),
        )
        for row in frame[["timestamp", "open", "high", "low", "close"]].itertuples(index=False)
    )
except (TypeError, ValueError, AttributeError) as exc:
    st.error(f"Could not build OHLC candles: {exc}")
    st.stop()

signals = tuple(bool(value) for value in frame["signal"].tolist())
st.caption(f"Loaded {len(candles):,} candles. Verify timestamps, signal generation, and data source.")
st.dataframe(frame.head(10), use_container_width=True, hide_index=True)

st.subheader("Backtest assumptions")
left, middle, right = st.columns(3)
with left:
    capital = st.number_input("Starting capital (₹)", min_value=1000.0, value=10000.0, step=1000.0)
    max_loss = st.number_input("Maximum loss budget per trade (₹)", min_value=1.0, value=500.0, step=50.0)
with middle:
    stop_distance = st.number_input("Stop distance (price units)", min_value=0.01, value=5.0, step=0.5)
    reward_risk = st.number_input("Reward/risk ratio", min_value=0.1, value=2.0, step=0.1)
with right:
    round_trip_cost = st.number_input(
        "Round-trip cost per unit (₹)", min_value=0.0, value=0.0, step=0.1
    )
    slippage = st.number_input(
        "Slippage per unit per side (₹)", min_value=0.0, value=0.0, step=0.1
    )

base_config = BacktestConfig(
    capital=capital,
    max_loss_per_trade=max_loss,
    stop_distance=stop_distance,
    reward_risk_ratio=reward_risk,
    round_trip_cost_per_unit=round_trip_cost,
    slippage_per_unit_per_side=slippage,
)
if st.button("Run research analysis", type="primary"):
    try:
        baseline = run_backtest(candles, signals, base_config)
        variants = {
            "Baseline": base_config,
            "Wider stop (1.5×)": BacktestConfig(
                capital=capital,
                max_loss_per_trade=max_loss,
                stop_distance=stop_distance * 1.5,
                reward_risk_ratio=reward_risk,
                round_trip_cost_per_unit=round_trip_cost,
                slippage_per_unit_per_side=slippage,
            ),
            "Lower reward/risk (0.75×)": BacktestConfig(
                capital=capital,
                max_loss_per_trade=max_loss,
                stop_distance=stop_distance,
                reward_risk_ratio=max(0.1, reward_risk * 0.75),
                round_trip_cost_per_unit=round_trip_cost,
                slippage_per_unit_per_side=slippage,
            ),
        }
        sensitivity = evaluate_parameter_sensitivity(candles, signals, variants)
    except (ValueError, TypeError, OverflowError) as exc:
        st.error(f"Analysis could not be completed: {exc}")
        st.stop()

    st.subheader("Baseline result")
    metrics = st.columns(5)
    metrics[0].metric("Ending capital", f"₹{baseline.ending_capital:,.2f}")
    metrics[1].metric("Total return", f"{baseline.total_return_pct:.2f}%")
    metrics[2].metric("Max drawdown", f"{baseline.max_drawdown_pct:.2f}%")
    metrics[3].metric("Win rate", f"{baseline.win_rate_pct:.2f}%")
    metrics[4].metric("Trades", len(baseline.trades))

    st.subheader("Parameter sensitivity")
    sensitivity_rows = [
        {
            "Variant": item.variant,
            "Stop distance": item.config.stop_distance,
            "Reward/risk": item.config.reward_risk_ratio,
            "Trades": len(item.result.trades),
            "Ending capital (₹)": round(item.result.ending_capital, 2),
            "Return (%)": round(item.result.total_return_pct, 2),
            "Max drawdown (%)": round(item.result.max_drawdown_pct, 2),
            "Win rate (%)": round(item.result.win_rate_pct, 2),
            "Expectancy/trade (₹)": round(item.result.expectancy_per_trade, 2),
        }
        for item in sensitivity
    ]
    st.dataframe(pd.DataFrame(sensitivity_rows), use_container_width=True, hide_index=True)

    st.subheader("Optional caller-labelled regime windows")
    st.markdown(
        "Enter one non-overlapping window per line as **label,start_index,end_index**. "
        "Indices are zero-based and the end index is exclusive. Labels are your own "
        "classification, not inferred by the app."
    )
    regime_text = st.text_area(
        "Regime windows",
        placeholder="trending,0,100\nsideways,100,200",
        help="Each window must include at least two candles and fit within the uploaded data.",
    )
    if regime_text.strip():
        try:
            regimes: dict[str, tuple[int, int]] = {}
            for line_number, line in enumerate(regime_text.splitlines(), start=1):
                parts = [part.strip() for part in line.split(",")]
                if len(parts) != 3:
                    raise ValueError(f"Line {line_number}: use label,start_index,end_index")
                label, start_text, end_text = parts
                if label in regimes:
                    raise ValueError(f"Line {line_number}: duplicate label {label!r}")
                regimes[label] = (int(start_text), int(end_text))
            regime_results = evaluate_regime_robustness(
                candles, signals, base_config, regimes=regimes
            )
            regime_rows = [
                {
                    "Label": item.regime,
                    "Start index": item.start_index,
                    "End index (exclusive)": item.end_index,
                    "Candles": item.candle_count,
                    "Trades": len(item.result.trades),
                    "Return (%)": round(item.result.total_return_pct, 2),
                    "Max drawdown (%)": round(item.result.max_drawdown_pct, 2),
                    "Win rate (%)": round(item.result.win_rate_pct, 2),
                }
                for item in regime_results
            ]
            st.dataframe(pd.DataFrame(regime_rows), use_container_width=True, hide_index=True)
        except (ValueError, TypeError) as exc:
            st.error(f"Regime analysis could not be completed: {exc}")

    trades = pd.DataFrame([trade.__dict__ for trade in baseline.trades])
    st.subheader("Baseline trade ledger")
    if trades.empty:
        st.info("No trades were generated for these signals and assumptions.")
    else:
        st.dataframe(trades, use_container_width=True, hide_index=True)
        st.download_button(
            "Download trade ledger CSV",
            data=trades.to_csv(index=False).encode("utf-8"),
            file_name="fibonacci_gann_research_trades.csv",
            mime="text/csv",
        )
