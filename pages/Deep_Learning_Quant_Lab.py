"""Research workbench inspired by Deep Learning in Quantitative Trading.

This first iteration focuses on data diagnostics and a leakage-aware momentum
baseline. It does not generate broker orders or claim a validated ML edge.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from algorithmic_trading.walk_forward_validation import walk_forward_evaluate
from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES
from services.resilient_market_data import download_symbol_frames

st.set_page_config(page_title="Deep Learning Quant Lab", page_icon="🧪", layout="wide")

st.title("🧪 Deep Learning Quant Lab")
st.caption(
    "A separate research module inspired by *Deep Learning in Quantitative Trading* "
    "(Zhang & Zohren, 2025). Research and paper analysis only; no broker orders are submitted."
)

st.info(
    "Phase 1 provides data-quality checks, financial time-series diagnostics, and a simple "
    "momentum baseline. Deep-learning models will be added only after the baseline and "
    "chronological validation are working reliably."
)

left, right = st.columns(2)
with left:
    exchange = st.selectbox("Exchange", ["NSE", "BSE"], key="dlq_exchange")
    universe = NSE_CANDIDATES if exchange == "NSE" else BSE_CANDIDATES
    symbol = st.selectbox(
        "Stock symbol",
        universe,
        index=0,
        format_func=lambda value: str(value).removesuffix(".NS").removesuffix(".BO"),
        key="dlq_symbol",
    )
with right:
    period = st.selectbox("History", ["6mo", "1y", "2y", "5y"], index=2, key="dlq_period")
    benchmark_choice = st.selectbox(
        "Risk-comparison benchmark",
        ["Stock buy-and-hold", "NIFTY 50 (^NSEI)", "S&P BSE SENSEX (^BSESN)"],
        key="dlq_benchmark",
        help="External index comparisons use overlapping trading dates only.",
    )
    benchmark_symbol = {
        "NIFTY 50 (^NSEI)": "^NSEI",
        "S&P BSE SENSEX (^BSESN)": "^BSESN",
    }.get(benchmark_choice)
    train_size = st.slider(
        "Initial training window (sessions)",
        min_value=60,
        max_value=504,
        value=252,
        step=21,
        key="dlq_train_size",
    )
    n_splits = st.slider(
        "Out-of-sample folds",
        min_value=2,
        max_value=8,
        value=4,
        step=1,
        key="dlq_n_splits",
    )
    transaction_cost_bps = st.slider(
        "Assumed transaction cost (bps per position change)",
        min_value=0,
        max_value=50,
        value=10,
        step=5,
        key="dlq_cost_bps",
    )

ticker = str(symbol).strip().upper()
if not ticker.endswith((".NS", ".BO")):
    ticker = f"{ticker}.NS" if exchange == "NSE" else f"{ticker}.BO"

if st.button("Load history and run diagnostics", type="primary", key="dlq_run"):
    with st.spinner(f"Loading historical candles for {ticker}..."):
        frames, diagnostics = download_symbol_frames(
            [ticker] + ([benchmark_symbol] if benchmark_symbol else []),
            period=period,
            interval="1d",
            auto_adjust=False,
            batch_size=1,
            timeout=15,
            recover_missing=True,
        )

    history = frames.get(ticker, pd.DataFrame())
    if history.empty or "Close" not in history.columns:
        st.error(
            "No usable historical price data was returned. No synthetic prices or fallback "
            "signals are generated. Retry later or select another symbol."
        )
        if diagnostics:
            st.caption(f"Provider diagnostics: {diagnostics}")
        st.stop()

    close = pd.to_numeric(history["Close"], errors="coerce").dropna()
    close = close[~close.index.duplicated(keep="last")].sort_index()
    if len(close) < 60:
        st.warning(f"Only {len(close)} usable closing-price observations are available.")
    if len(close) < 25:
        st.error("At least 25 usable observations are needed for the momentum baseline.")
        st.stop()

    returns = close.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    log_returns = np.log(close / close.shift(1)).replace([np.inf, -np.inf], np.nan).dropna()
    rolling_vol = returns.rolling(20).std() * np.sqrt(252)
    drawdown = close / close.cummax() - 1.0
    momentum = close.pct_change(20)
    # Signal at t uses only information available through close[t].
    # Return at t+1 is assigned to that signal, avoiding same-bar look-ahead.
    signal = momentum.gt(0).astype(float)
    next_return = returns.shift(-1)
    turnover = signal.diff().abs().fillna(signal.iloc[0])
    costs = turnover * (transaction_cost_bps / 10_000.0)
    strategy_returns = (signal * next_return - costs).dropna()
    benchmark_returns = next_return.loc[strategy_returns.index].dropna()
    strategy_returns = strategy_returns.loc[benchmark_returns.index]

    def max_drawdown(series: pd.Series) -> float:
        wealth = (1.0 + series).cumprod()
        return float((wealth / wealth.cummax() - 1.0).min()) if not wealth.empty else float("nan")

    def sharpe(series: pd.Series) -> float:
        std = float(series.std(ddof=1))
        if not np.isfinite(std) or std <= 0:
            return float("nan")
        return float(series.mean() / std * np.sqrt(252))

    external_benchmark_returns = pd.Series(dtype=float)
    external_benchmark_name = ""
    if benchmark_symbol:
        benchmark_history = frames.get(benchmark_symbol, pd.DataFrame())
        if not benchmark_history.empty and "Close" in benchmark_history.columns:
            benchmark_close = pd.to_numeric(
                benchmark_history["Close"], errors="coerce"
            ).dropna()
            benchmark_close = benchmark_close[
                ~benchmark_close.index.duplicated(keep="last")
            ].sort_index()
            benchmark_returns_raw = benchmark_close.pct_change()
            aligned = pd.concat(
                [
                    strategy_returns.rename("strategy"),
                    benchmark_returns_raw.rename("benchmark"),
                ],
                axis=1,
                join="inner",
            ).dropna()
            external_benchmark_returns = aligned["benchmark"]
            strategy_returns = aligned["strategy"]
            external_benchmark_name = benchmark_choice
        else:
            st.warning(
                f"{benchmark_choice} data was unavailable. External benchmark-relative "
                "metrics will be shown as unavailable; the stock buy-and-hold baseline remains."
            )

    st.session_state["dlq_results"] = {
        "ticker": ticker,
        "external_benchmark_returns": external_benchmark_returns,
        "external_benchmark_name": external_benchmark_name,
        "close": close,
        "returns": returns,
        "log_returns": log_returns,
        "rolling_vol": rolling_vol,
        "drawdown": drawdown,
        "momentum": momentum,
        "strategy_returns": strategy_returns,
        "benchmark_returns": benchmark_returns,
        "observations": len(close),
        "cost_bps": transaction_cost_bps,
        "train_size": train_size,
        "n_splits": n_splits,
    }

result = st.session_state.get("dlq_results")
if isinstance(result, dict):
    close = result["close"]
    returns = result["returns"]
    log_returns = result["log_returns"]
    rolling_vol = result["rolling_vol"]
    drawdown = result["drawdown"]
    momentum = result["momentum"]
    strategy_returns = result["strategy_returns"]
    benchmark_returns = result["benchmark_returns"]

    st.subheader(f"Historical diagnostics — {result['ticker']}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Observations", f"{result['observations']:,}")
    m2.metric("Latest close", f"₹{close.iloc[-1]:,.2f}")
    m3.metric(
        "20-day annualized volatility",
        f"{rolling_vol.iloc[-1]:.1%}" if pd.notna(rolling_vol.iloc[-1]) else "N/A",
    )
    m4.metric("Maximum historical drawdown", f"{drawdown.min():.1%}")

    diagnostics_tab, baseline_tab, notes_tab = st.tabs(
        ["Time-series diagnostics", "Momentum baseline", "Method & limitations"]
    )
    with diagnostics_tab:
        st.markdown("**Closing price**")
        st.line_chart(close.rename("Close"))
        st.markdown("**Daily simple returns**")
        st.line_chart(returns.rename("Daily return"))
        st.markdown("**20-day annualized rolling volatility**")
        st.line_chart(rolling_vol.rename("Annualized volatility"))
        st.markdown("**Drawdown from prior peak**")
        st.line_chart(drawdown.rename("Drawdown"))
        summary = pd.DataFrame(
            {
                "Metric": [
                    "Mean daily return",
                    "Daily volatility",
                    "Skewness",
                    "Excess kurtosis",
                    "Positive-return days",
                ],
                "Value": [
                    returns.mean(),
                    returns.std(ddof=1),
                    returns.skew(),
                    returns.kurt(),
                    (returns > 0).mean(),
                ],
            }
        )
        st.dataframe(summary, use_container_width=True, hide_index=True)
        st.caption(
            "Skewness and excess kurtosis describe the sample distribution; they do not establish "
            "that returns follow a particular probability distribution."
        )

    with baseline_tab:
        st.caption(
            "Baseline rule: hold the stock when its trailing 20-session return is positive; "
            "otherwise hold cash. The signal is shifted against the following session's return. "
            "This is a simple benchmark, not a trained neural network."
        )
        strategy_equity = (1.0 + strategy_returns).cumprod()
        benchmark_equity = (1.0 + benchmark_returns).cumprod()
        chart = pd.concat(
            [
                strategy_equity.rename("20-day momentum baseline"),
                benchmark_equity.rename("Buy-and-hold reference"),
            ],
            axis=1,
        )
        st.line_chart(chart)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Baseline cumulative return",
            f"{(strategy_equity.iloc[-1] - 1):.1%}" if not strategy_equity.empty else "N/A",
        )
        c2.metric(
            "Reference cumulative return",
            f"{(benchmark_equity.iloc[-1] - 1):.1%}" if not benchmark_equity.empty else "N/A",
        )
        c3.metric(
            "Baseline Sharpe (annualized)",
            f"{sharpe(strategy_returns):.2f}" if np.isfinite(sharpe(strategy_returns)) else "N/A",
        )
        c4.metric(
            "Baseline max drawdown",
            f"{max_drawdown(strategy_returns):.1%}" if not strategy_returns.empty else "N/A",
        )
        # Use the selected external index only when its aligned returns are available.
        risk_reference = result.get("external_benchmark_returns", pd.Series(dtype=float))
        risk_reference_name = result.get("external_benchmark_name", "")
        if not risk_reference.empty:
            risk_strategy, risk_reference = strategy_returns.align(
                risk_reference, join="inner"
            )
        else:
            risk_strategy = strategy_returns
            risk_reference = benchmark_returns
            risk_reference_name = "Stock buy-and-hold"

        # Compare returns only on identical dates; never fill missing benchmark observations.
        active_returns = risk_strategy - risk_reference
        tracking_error = (
            float(active_returns.std(ddof=1) * np.sqrt(252))
            if len(active_returns) > 1
            else float("nan")
        )
        active_std = float(active_returns.std(ddof=1))
        information_ratio = (
            float(active_returns.mean() / active_std * np.sqrt(252))
            if np.isfinite(active_std) and active_std > 0
            else float("nan")
        )

        def downside_deviation(series: pd.Series) -> float:
            downside = np.minimum(series.to_numpy(dtype=float), 0.0)
            return float(np.sqrt(np.mean(np.square(downside))) * np.sqrt(252))

        baseline_downside = downside_deviation(risk_strategy)
        reference_downside = downside_deviation(risk_reference)
        baseline_wealth = (1.0 + risk_strategy).cumprod()
        reference_wealth = (1.0 + risk_reference).cumprod()
        excess_cumulative = (
            float(baseline_wealth.iloc[-1] - reference_wealth.iloc[-1])
            if not baseline_wealth.empty and not reference_wealth.empty
            else float("nan")
        )
        baseline_risk_drawdown = max_drawdown(risk_strategy)
        reference_risk_drawdown = max_drawdown(risk_reference)
        risk_metrics = pd.DataFrame(
            {
                "Metric": [
                    "Cumulative excess return vs buy-and-hold (percentage points)",
                    "Annualized tracking error",
                    "Annualized information ratio",
                    "Annualized downside deviation — baseline",
                    "Annualized downside deviation — buy-and-hold",
                    "Maximum drawdown — baseline",
                    f"Maximum drawdown — {risk_reference_name}",
                ],
                "Value": [
                    f"{excess_cumulative * 100:.2f} pp" if np.isfinite(excess_cumulative) else "N/A",
                    f"{tracking_error:.2%}" if np.isfinite(tracking_error) else "N/A",
                    f"{information_ratio:.2f}" if np.isfinite(information_ratio) else "N/A",
                    f"{baseline_downside:.2%}" if np.isfinite(baseline_downside) else "N/A",
                    f"{reference_downside:.2%}" if np.isfinite(reference_downside) else "N/A",
                    f"{baseline_risk_drawdown:.1%}" if np.isfinite(baseline_risk_drawdown) else "N/A",
                    f"{reference_risk_drawdown:.1%}" if np.isfinite(reference_risk_drawdown) else "N/A",
                ],
            }
        )
        st.subheader("Benchmark-relative performance and risk")
        st.caption(
            f"Reference: {risk_reference_name}. Metrics use overlapping dates only and do not "
            "fill missing observations. The baseline includes the selected transaction-cost "
            "assumption; reference returns do not include simulated trading costs. "
            "Cumulative excess return is the difference between compounded wealth factors."
        )
        st.dataframe(risk_metrics, use_container_width=True, hide_index=True)
        st.download_button(
            "Download benchmark-relative risk metrics (CSV)",
            risk_metrics.to_csv(index=False).encode("utf-8"),
            file_name=f"{result['ticker'].replace('.', '_')}_relative_risk_metrics.csv",
            mime="text/csv",
        )

        st.subheader("Chronological walk-forward validation")
        try:
            fold_metrics = walk_forward_evaluate(
                close,
                momentum.gt(0).astype(float),
                min_train_size=int(result["train_size"]),
                n_splits=int(result["n_splits"]),
                cost_bps=float(result["cost_bps"]),
            )
            st.caption(
                "Signals are computed from trailing 20-session momentum and evaluated on "
                "sequential test folds. The existing backtester shifts signals by one bar. "
                "This is a fixed baseline, not a trained or tuned model."
            )
            st.dataframe(fold_metrics, use_container_width=True, hide_index=True)
            st.line_chart(fold_metrics.set_index("fold")[["total_return", "buy_hold_return"]])
            st.download_button(
                "Download walk-forward fold metrics (CSV)",
                fold_metrics.to_csv(index=False).encode("utf-8"),
                file_name=f"{result['ticker'].replace('.', '_')}_walk_forward_folds.csv",
                mime="text/csv",
            )
        except ValueError as exc:
            st.warning(f"Walk-forward validation unavailable: {exc}")
        st.warning(
            "Walk-forward evaluation improves chronological reporting but does not prove "
            "future profitability. Results remain sensitive to market regimes, data quality, "
            "corporate actions, and simplified transaction costs. Do not use this output alone "
            "for live trades."
        )
        export = pd.DataFrame(
            {
                "strategy_return": strategy_returns,
                "benchmark_return": benchmark_returns,
            }
        )
        st.download_button(
            "Download baseline return series (CSV)",
            export.to_csv(index=True).encode("utf-8"),
            file_name=f"{result['ticker'].replace('.', '_')}_quant_baseline.csv",
            mime="text/csv",
        )

    with notes_tab:
        st.markdown("""
            **Book-aligned roadmap**

            1. Establish return-distribution and volatility diagnostics.
            2. Keep a transparent classical baseline before introducing complex models.
            3. Add chronological train/validation/test splits and walk-forward evaluation.
            4. Compare neural networks against the baseline using identical data and costs.
            5. Add portfolio and risk constraints only after validation is reliable.

            **Not implemented in this first phase:** neural-network training, hyperparameter
            search, end-to-end portfolio optimization, order-book modelling, or live trading.
            """)
        st.caption(
            "Reference: Zihao Zhang and Stefan Zohren, *Deep Learning in Quantitative Trading* "
            "(Cambridge University Press, 2025). This module is an independent research implementation."
        )
else:
    st.caption("Choose an exchange, symbol, and history length, then run the diagnostics.")
