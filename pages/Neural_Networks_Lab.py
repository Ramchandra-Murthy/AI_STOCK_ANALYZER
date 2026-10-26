"""Research-only Neural Networks Lab page."""

from __future__ import annotations

from io import BytesIO, StringIO

import pandas as pd
import streamlit as st
import yfinance as yf

from ai_trading.transaction_cost_sensitivity import transaction_cost_sensitivity
from ai_trading.benchmark_diagnostics import benchmark_relative_diagnostics
from neural_networks.baseline import train_baseline
from neural_networks.evaluation import (
    compare_feature_ablation,
    compare_holdout_baselines,
    compare_mlp_configurations,
    evaluate_mlp_seed_stability,
    factor_information_coefficient,
    permutation_feature_sensitivity,
    summarize_mlp_configuration_results,
    summarize_mlp_seed_stability,
    summarize_probability_reliability,
    summarize_walk_forward_stability,
    walk_forward_evaluation,
)
from neural_networks.features import build_direction_dataset
from neural_networks.strategy_backtest import (
    backtest_holdout_signals,
    summarize_backtest_trade_distribution,
)

st.title("Neural Networks Lab")
st.caption(
    "Experimental research module inspired by Neural Networks for Algorithmic Trading with MQL5."
)
st.warning(
    "Research only. No broker orders are submitted. Model results are not trading advice or proof of profitability."
)

st.markdown(
    "Get historical daily OHLCV data from Yahoo Finance or upload your own CSV, then build "
    "causal features and evaluate an MLP classifier on a later, chronological holdout period."
)

st.subheader("Get historical data")
st.caption(
    "Yahoo Finance data is retrieved when you click the button. Availability, history length, "
    "and symbols may vary. Verify the downloaded data before using it for research."
)
download_col, period_col = st.columns([2, 1])
with download_col:
    ticker_symbol = st.text_input(
        "Yahoo Finance symbol",
        value="RELIANCE.NS",
        help="Examples: RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS.",
    )
with period_col:
    history_period = st.selectbox(
        "History",
        options=["1y", "2y", "5y", "10y", "max"],
        index=2,
        help="Yahoo Finance may not provide every period for every symbol.",
    )

if st.button("Fetch historical OHLCV", type="secondary"):
    normalized_symbol = ticker_symbol.strip().upper()
    if not normalized_symbol:
        st.error("Enter a Yahoo Finance symbol, such as RELIANCE.NS.")
    else:
        try:
            downloaded = yf.Ticker(normalized_symbol).history(
                period=history_period,
                interval="1d",
                auto_adjust=False,
                actions=False,
            )
            if downloaded.empty:
                st.session_state.pop("nn_lab_yahoo_csv", None)
                st.error(
                    "Yahoo Finance returned no historical rows for this symbol and period. "
                    "Check the symbol and try another period, or upload a CSV instead."
                )
            else:
                downloaded.columns = [str(column).strip().title() for column in downloaded.columns]
                required_columns = ["Open", "High", "Low", "Close", "Volume"]
                missing_columns = [
                    column for column in required_columns if column not in downloaded.columns
                ]
                if missing_columns:
                    st.error(
                        "Yahoo Finance data did not include required columns: "
                        + ", ".join(missing_columns)
                    )
                else:
                    downloaded = downloaded.loc[:, required_columns]
                    downloaded.index.name = "Date"
                    csv_content = downloaded.to_csv(index=True)
                    st.session_state["nn_lab_yahoo_csv"] = csv_content
                    st.session_state["nn_lab_yahoo_symbol"] = normalized_symbol
                    st.session_state["nn_lab_yahoo_period"] = history_period
                    st.success(f"Fetched {len(downloaded):,} daily rows for {normalized_symbol}.")
        except Exception as exc:
            st.error(
                "Could not fetch Yahoo Finance data. Check the symbol and connection, "
                f"or upload a CSV instead. Details: {exc}"
            )

if st.session_state.get("nn_lab_yahoo_csv"):
    fetched_symbol = st.session_state.get("nn_lab_yahoo_symbol", "Yahoo Finance")
    fetched_period = st.session_state.get("nn_lab_yahoo_period", history_period)
    st.download_button(
        f"Download {fetched_symbol} CSV",
        data=st.session_state["nn_lab_yahoo_csv"].encode("utf-8"),
        file_name=f"{fetched_symbol.replace('.', '_')}_OHLCV.csv",
        mime="text/csv",
        key="nn_lab_download_csv",
    )
    st.caption(
        f"Fetched source: {fetched_symbol} · Period: {fetched_period} · Frequency: daily. "
        "Yahoo Finance is an external data source; prices and availability may change."
    )

st.divider()
st.subheader("Use data for model evaluation")
upload = st.file_uploader(
    "Upload OHLCV CSV (optional if you fetched data above)",
    type=["csv"],
    help="Required columns: Date, Open, High, Low, Close, Volume. Uploaded files take priority over fetched data.",
)

raw = None
data_source = None
if upload is not None:
    try:
        raw = pd.read_csv(BytesIO(upload.getvalue()))
        data_source = f"Uploaded file: {upload.name}"
    except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as exc:
        st.error(f"Could not read this CSV: {exc}")
        st.stop()
elif st.session_state.get("nn_lab_yahoo_csv"):
    try:
        raw = pd.read_csv(StringIO(st.session_state["nn_lab_yahoo_csv"]))
        data_source = (
            f"Yahoo Finance: {st.session_state.get('nn_lab_yahoo_symbol', 'unknown symbol')}"
        )
    except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as exc:
        st.error(f"Could not read the fetched Yahoo Finance CSV: {exc}")
        st.stop()

horizon = st.number_input(
    "Prediction horizon (trading days)", min_value=1, max_value=30, value=5, step=1
)
train_fraction = st.slider(
    "Training fraction (earlier observations)",
    min_value=0.50,
    max_value=0.90,
    value=0.70,
    step=0.05,
)
backtest_col, cost_col = st.columns(2)
with backtest_col:
    probability_threshold = st.slider(
        "Long-entry probability threshold",
        min_value=0.40,
        max_value=0.80,
        value=0.50,
        step=0.05,
        help="Fixed threshold for this holdout report; do not tune it against the holdout results.",
    )
with cost_col:
    run_mlp_configuration_comparison = st.checkbox(
        "Run optional chronological MLP configuration comparison (slower)",
        value=False,
        help="Compares a small fixed set of architectures across future validation folds. It does not select or deploy a model.",
    )
    cost_bps_per_side = st.number_input(
        "Estimated transaction cost (basis points per side)",
        min_value=0.0,
        max_value=200.0,
        value=10.0,
        step=1.0,
        help="Illustrative estimate per entry or exit. Replace with realistic brokerage, taxes, spread, and slippage assumptions.",
    )

if raw is not None:
    try:
        raw.columns = [str(column).strip() for column in raw.columns]
        date_column = next(
            (
                column
                for column in raw.columns
                if column.lower() in {"date", "datetime", "timestamp"}
            ),
            None,
        )
        if date_column is None:
            st.error("CSV must include a Date, Datetime, or Timestamp column.")
            st.stop()
        raw[date_column] = pd.to_datetime(raw[date_column], errors="coerce")
        raw = raw.dropna(subset=[date_column]).set_index(date_column).sort_index()
        raw.index.name = "Date"
        raw = raw.loc[~raw.index.duplicated(keep="last")]
        column_lookup = {str(column).strip().lower(): column for column in raw.columns}
        required = ["open", "high", "low", "close", "volume"]
        missing = [column for column in required if column not in column_lookup]
        if missing:
            st.error("Missing required CSV columns: " + ", ".join(missing).upper())
            st.stop()
        data = raw.rename(columns={column_lookup[name]: name.title() for name in required})
        data = data.loc[:, ["Open", "High", "Low", "Close", "Volume"]]
        for column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")
        data = data.replace([float("inf"), float("-inf")], float("nan"))
        data = data.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
        data = data.loc[(data["Close"] > 0) & (data["Volume"] >= 0)]
        if len(data) < 150:
            st.error(
                f"Only {len(data)} valid daily rows remain. Upload or fetch at least 150 rows; "
                "more history is preferable."
            )
            st.stop()

        st.success(
            f"Validated {len(data):,} daily rows from {data.index.min().date()} "
            f"to {data.index.max().date()}."
        )
        st.caption(f"Data source: {data_source}")
        with st.expander("Preview cleaned OHLCV data"):
            st.dataframe(data.tail(10), use_container_width=True)

        if st.button("Build dataset and train MLP", type="primary"):
            try:
                features, target = build_direction_dataset(data, horizon=int(horizon))
                if len(features) < 130:
                    st.error(
                        "Not enough usable observations after feature preparation. Upload or fetch "
                        "more history."
                    )
                    st.stop()
                model, metrics = train_baseline(
                    features, target, train_fraction=float(train_fraction), horizon=int(horizon)
                )
                split_at = int(len(features) * float(train_fraction))
                test_dates = features.index[split_at:]
                train_end = metrics["train_end"]
                left, middle, right = st.columns(3)
                left.metric("Holdout accuracy", f"{metrics['accuracy']:.1%}")
                middle.metric("Test observations", f"{metrics['test_samples']:,}")
                if "roc_auc" in metrics:
                    right.metric("ROC-AUC", f"{metrics['roc_auc']:.3f}")
                else:
                    right.metric("ROC-AUC", "Unavailable")
                st.subheader("Overfitting and class-balance diagnostics")
                fit_left, fit_middle, fit_right = st.columns(3)
                fit_left.metric("Training accuracy", f"{metrics['train_accuracy']:.1%}")
                fit_middle.metric("Holdout accuracy", f"{metrics['accuracy']:.1%}")
                fit_right.metric("Train − holdout gap", f"{metrics['accuracy_gap']:+.1%}")
                st.caption(
                    f"Holdout balanced accuracy: {metrics['holdout_balanced_accuracy']:.1%}. "
                    "Balanced accuracy averages recall across classes and helps reveal "
                    "performance hidden by unequal class counts."
                )
                if metrics["accuracy_gap"] >= 0.15:
                    st.warning(
                        "Training accuracy exceeds holdout accuracy by at least 15 percentage "
                        "points. This can indicate overfitting; compare chronological folds and "
                        "class balance before drawing conclusions."
                    )
                elif metrics["accuracy_gap"] < 0:
                    st.info(
                        "Holdout accuracy exceeds training accuracy. This is not automatically "
                        "a problem; check fold-to-fold stability and data characteristics."
                    )
                st.subheader("MLP random-seed stability")
                seed_stability = evaluate_mlp_seed_stability(
                    features,
                    target,
                    train_fraction=float(train_fraction),
                    horizon=int(horizon),
                )
                st.caption(
                    "Each run uses the same chronological training and holdout dates but a different "
                    "MLP initialization seed. Metric variation reveals sensitivity to initialization; "
                    "it is not independent validation, and the shared holdout should not be used to "
                    "select a preferred seed."
                )
                seed_summary = summarize_mlp_seed_stability(seed_stability)
                st.subheader("Across-seed metric summary")
                st.caption(
                    "Mean, sample standard deviation, minimum, and maximum summarize variation across "
                    "initialization seeds on the same holdout. These are not confidence intervals or "
                    "independent estimates of future performance."
                )
                st.dataframe(
                    seed_summary.style.format(
                        {
                            "Mean": "{:.4f}",
                            "Std": "{:.4f}",
                            "Min": "{:.4f}",
                            "Max": "{:.4f}",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                st.download_button(
                    "Download MLP seed-stability summary CSV",
                    data=seed_summary.to_csv(index=False).encode("utf-8"),
                    file_name="neural_networks_seed_stability_summary.csv",
                    mime="text/csv",
                )
                st.dataframe(
                    seed_stability.style.format(
                        {
                            "Accuracy": "{:.1%}",
                            "Balanced accuracy": "{:.1%}",
                            "ROC-AUC": "{:.3f}",
                            "Brier score": "{:.4f}",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                st.download_button(
                    "Download MLP seed-stability CSV",
                    data=seed_stability.to_csv(index=False).encode("utf-8"),
                    file_name="neural_networks_seed_stability.csv",
                    mime="text/csv",
                )
                st.subheader("Probability calibration diagnostics")
                calibration_left, calibration_right = st.columns(2)
                calibration_left.metric("Brier score", f"{metrics['brier_score']:.4f}")
                calibration_right.metric("Log loss", f"{metrics['log_loss']:.4f}")
                st.caption(
                    "Brier score and log loss evaluate the quality of predicted probabilities, "
                    "not just the up/down classification. Lower values are better; compare them "
                    "against other models on the same holdout period. They do not establish "
                    "profitable trading signals."
                )
                reliability = summarize_probability_reliability(
                    metrics["actual"], metrics["probability_up"], n_bins=5
                )
                st.subheader("Holdout probability reliability by band")
                st.caption(
                    "Within each probability band, compare the model's mean predicted up-probability "
                    "with the observed up frequency. Positive calibration gap means the observed "
                    "rate was higher than predicted; negative means it was lower. Small sample "
                    "counts make each band's estimate noisy. This is descriptive, not a guarantee "
                    "of future calibration or profitability."
                )
                st.dataframe(
                    reliability.style.format(
                        {
                            "Mean predicted probability": "{:.1%}",
                            "Observed up rate": "{:.1%}",
                            "Calibration gap": "{:+.1%}",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                st.download_button(
                    "Download probability reliability CSV",
                    data=reliability.to_csv(index=False).encode("utf-8"),
                    file_name="neural_networks_probability_reliability.csv",
                    mime="text/csv",
                )
                st.subheader("MLP training diagnostics")
                diagnostic_left, diagnostic_middle, diagnostic_right = st.columns(3)
                diagnostic_left.metric(
                    "Training iterations",
                    f"{metrics['training_iterations']:,} / {metrics['max_iterations']:,}",
                )
                diagnostic_middle.metric(
                    "Final training loss", f"{metrics['final_training_loss']:.5f}"
                )
                diagnostic_right.metric(
                    "Iteration limit reached",
                    "Yes" if metrics["reached_iteration_limit"] else "No",
                )
                loss_curve = metrics["training_loss_curve"]
                if loss_curve:
                    st.line_chart(
                        pd.DataFrame(
                            {
                                "Training loss": loss_curve,
                                "Iteration": range(1, len(loss_curve) + 1),
                            }
                        ).set_index("Iteration")
                    )
                if metrics["convergence_warnings"]:
                    for warning_message in metrics["convergence_warnings"]:
                        st.warning(f"MLP convergence warning: {warning_message}")
                elif metrics["reached_iteration_limit"]:
                    st.warning(
                        "The MLP reached max_iter. Review the loss curve and compare results "
                        "across chronological folds before interpreting the model."
                    )
                else:
                    st.caption(
                        "No scikit-learn convergence warning was captured for this fit. "
                        "This does not establish predictive value or profitability."
                    )
                st.caption(
                    "Training loss describes optimization on the training data only; it is not "
                    "a measure of holdout performance or trading profitability."
                )
                st.caption(
                    f"Train: {features.index[0].date()} to {train_end} "
                    f"({metrics['train_samples']:,} rows; "
                    f"{metrics['train_positive']:,} positive / {metrics['train_negative']:,} negative) · "
                    f"Test: {test_dates[0].date()} to {test_dates[-1].date()} "
                    f"({metrics['test_samples']:,} rows; "
                    f"{metrics['test_positive']:,} positive / {metrics['test_negative']:,} negative) · "
                    f"Label: positive return from next close to close after {int(horizon)} holding days. "
                    f"Purged {int(horizon) + 1} rows at the split boundary."
                )
                result = pd.DataFrame(
                    {
                        "Date": test_dates,
                        "Actual_up": metrics["actual"],
                        "Predicted_probability_up": metrics["probability_up"],
                    }
                )
                result["Predicted_up"] = (result["Predicted_probability_up"] >= 0.5).astype(int)
                st.subheader("Chronological holdout predictions")
                st.dataframe(result.tail(100), use_container_width=True)
                st.download_button(
                    "Download holdout predictions CSV",
                    data=result.to_csv(index=False).encode("utf-8"),
                    file_name="neural_networks_holdout_predictions.csv",
                    mime="text/csv",
                )
                st.subheader("Holdout baseline comparison")
                st.caption(
                    "All models use the same chronological split. The majority-class model is a "
                    "simple reference; logistic regression tests whether a simpler linear model is competitive."
                )
                comparison = compare_holdout_baselines(
                    features, target, train_fraction=float(train_fraction), horizon=int(horizon)
                )
                st.caption(
                    "Brier score and log loss assess predicted-probability quality; lower is better. "
                    "Compare them across models on the same holdout. Undefined values are shown as dashes."
                )
                st.dataframe(
                    comparison.style.format(
                        {
                            "Accuracy": "{:.1%}",
                            "Balanced accuracy": "{:.1%}",
                            "ROC-AUC": "{:.3f}",
                            "Brier score": "{:.4f}",
                            "Log loss": "{:.4f}",
                        },
                        na_rep="—",
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

                st.subheader("Holdout feature sensitivity")
                st.caption(
                    "Features are shuffled one at a time on the chronological holdout. "
                    "The mean drop in balanced accuracy estimates how much the fitted model "
                    "relies on each feature under this test. Correlated features can mask one "
                    "another; negative values can occur from sampling noise. This is descriptive "
                    "research, not causal evidence, and repeated holdout inspection can bias conclusions."
                )
                sensitivity = permutation_feature_sensitivity(
                    model,
                    features.iloc[split_at:],
                    target.iloc[split_at:],
                    n_repeats=5,
                )
                st.dataframe(
                    sensitivity.style.format(
                        {
                            "Balanced accuracy drop mean": "{:+.4f}",
                            "Balanced accuracy drop std": "{:.4f}",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                st.download_button(
                    "Download feature sensitivity CSV",
                    data=sensitivity.to_csv(index=False).encode("utf-8"),
                    file_name="neural_networks_feature_sensitivity.csv",
                    mime="text/csv",
                )

                st.subheader("Feature ablation: original vs expanded factors")
                st.caption(
                    "A controlled comparison using identical labelled rows, chronological holdout "
                    "dates, and model settings. This checks whether the additional factors add "
                    "predictive value; it does not tune on the holdout."
                )
                ablation = compare_feature_ablation(
                    data, horizon=int(horizon), train_fraction=float(train_fraction)
                )
                st.dataframe(
                    ablation.style.format(
                        {
                            "Accuracy": "{:.1%}",
                            "Balanced accuracy": "{:.1%}",
                            "ROC-AUC": "{:.3f}",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                st.download_button(
                    "Download feature ablation results CSV",
                    data=ablation.to_csv(index=False).encode("utf-8"),
                    file_name="neural_networks_feature_ablation.csv",
                    mime="text/csv",
                )

                st.subheader("Factor Information Coefficient (IC)")
                st.caption(
                    "Spearman rank correlation between each factor and the subsequent "
                    f"{int(horizon)}-day forward return, reported across five chronological windows. "
                    "Moving-block bootstrap intervals provide a rough uncertainty range while preserving short-range dependence. "
                    "They are not formal significance tests; IC is a research diagnostic, not evidence of a profitable strategy."
                )
                factor_ic = factor_information_coefficient(data, horizon=int(horizon), n_windows=5)
                # Arrow requires a consistent scalar type for each displayed column.
                # Keep the calculation/export frame unchanged; normalize only the UI copy.
                factor_ic_display = factor_ic.copy()
                factor_ic_display["Window"] = factor_ic_display["Window"].astype(str)
                st.dataframe(
                    factor_ic_display.style.format(
                        {
                            "Spearman IC": "{:.3f}",
                            "IC standard deviation": "{:.3f}",
                            "IC CI lower": "{:.3f}",
                            "IC CI upper": "{:.3f}",
                        },
                        na_rep="—",
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                st.download_button(
                    "Download factor IC diagnostics CSV",
                    data=factor_ic.to_csv(index=False).encode("utf-8"),
                    file_name="neural_networks_factor_ic.csv",
                    mime="text/csv",
                )

                st.subheader("Walk-forward validation")
                st.caption(
                    "Three expanding-window folds. Each fold trains only on earlier observations "
                    "and evaluates on a later, non-overlapping period."
                )
                walk_forward = walk_forward_evaluation(
                    features, target, n_splits=3, horizon=int(horizon)
                )
                st.dataframe(
                    walk_forward.style.format(
                        {"Accuracy": "{:.1%}", "Balanced accuracy": "{:.1%}", "ROC-AUC": "{:.3f}"}
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                st.download_button(
                    "Download walk-forward results CSV",
                    data=walk_forward.to_csv(index=False).encode("utf-8"),
                    file_name="neural_networks_walk_forward_results.csv",
                    mime="text/csv",
                )

                st.subheader("Walk-forward fold stability")
                st.caption(
                    "Mean, standard deviation, and range summarize variation across the three future test folds. "
                    "ROC-AUC excludes folds where it is undefined. These are descriptive diagnostics, not "
                    "evidence of profitability or a significance test."
                )
                fold_stability = summarize_walk_forward_stability(walk_forward)
                st.dataframe(
                    fold_stability.style.format(
                        {
                            column: "{:.3f}"
                            for column in fold_stability.columns
                            if column not in {"Model", "Folds"}
                        },
                        na_rep="—",
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                st.download_button(
                    "Download fold stability CSV",
                    data=fold_stability.to_csv(index=False).encode("utf-8"),
                    file_name="neural_networks_walk_forward_stability.csv",
                    mime="text/csv",
                )

                if run_mlp_configuration_comparison:
                    st.subheader("Chronological MLP configuration comparison")
                    st.caption(
                        "A fixed set of architectures and regularization strengths is compared across "
                        "expanding chronological validation folds. Means and ranges describe validation "
                        "folds only; do not use this table to tune repeatedly against the final holdout."
                    )
                    configuration_folds = compare_mlp_configurations(
                        features, target, n_splits=3, horizon=int(horizon)
                    )
                    configuration_summary = summarize_mlp_configuration_results(configuration_folds)
                    st.dataframe(
                        configuration_summary.style.format(
                            {
                                column: "{:.4f}"
                                for column in configuration_summary.columns
                                if column
                                not in {
                                    "Configuration",
                                    "Hidden layers",
                                    "Folds",
                                    "Iteration-limit folds",
                                }
                            },
                            na_rep="—",
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
                    st.download_button(
                        "Download MLP configuration summary CSV",
                        data=configuration_summary.to_csv(index=False).encode("utf-8"),
                        file_name="neural_networks_mlp_configuration_summary.csv",
                        mime="text/csv",
                    )
                    st.download_button(
                        "Download MLP configuration fold results CSV",
                        data=configuration_folds.to_csv(index=False).encode("utf-8"),
                        file_name="neural_networks_mlp_configuration_folds.csv",
                        mime="text/csv",
                    )

                st.subheader("Cost-aware holdout strategy backtest")
                st.caption(
                    "Long-only, non-overlapping trades. Signals are generated after the signal-date close; "
                    "entry is the next close and exit is the close after the selected holding horizon. "
                    "The threshold and cost assumptions are explicit and should not be tuned on the holdout."
                )
                class_labels = list(model.classes_)
                probability_up = model.predict_proba(features.iloc[split_at:])[
                    :, class_labels.index(1)
                ]
                backtest_summary, backtest_trades = backtest_holdout_signals(
                    data["Close"],
                    test_dates,
                    probability_up,
                    horizon=int(horizon),
                    threshold=float(probability_threshold),
                    cost_bps_per_side=float(cost_bps_per_side),
                )
                st.dataframe(
                    backtest_summary.style.format(
                        {
                            "Total return": "{:.2%}",
                            "Maximum drawdown": "{:.2%}",
                            "Annualized Sharpe": "{:.2f}",
                            "Win rate": "{:.1%}",
                            "Cost per side (bps)": "{:.1f}",
                            "Threshold": "{:.2f}",
                        },
                        na_rep="—",
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                st.caption(
                    "Simplified research simulation: excludes taxes and market impact and assumes close-price fills. "
                    "The buy-and-hold benchmark uses the same evaluation window and estimated round-trip costs."
                )
                if not backtest_trades.empty:
                    benchmark_trade_returns = []
                    for _, trade in backtest_trades.iterrows():
                        entry_price = float(data.loc[trade["Entry date"], "Close"])
                        exit_price = float(data.loc[trade["Exit date"], "Close"])
                        benchmark_trade_returns.append(exit_price / entry_price - 1.0)
                    relative = benchmark_relative_diagnostics(
                        backtest_trades["Net return after costs"].reset_index(drop=True),
                        pd.Series(benchmark_trade_returns),
                        periods_per_year=max(1, 252 // int(horizon)),
                    )
                    st.subheader("Benchmark-relative trade diagnostics")
                    st.caption(
                        "Compares completed strategy trades after estimated costs with buy-and-hold "
                        "returns over the same entry-to-exit intervals. Tracking error and information "
                        "ratio are annualized approximations across trade observations, not daily returns. "
                        "These descriptive metrics do not establish future performance."
                    )
                    relative_frame = pd.DataFrame([relative])
                    st.dataframe(
                        relative_frame.style.format(
                            {
                                "active_return": "{:+.2%}",
                                "tracking_error": "{:.2%}",
                                "information_ratio": "{:.3f}",
                            },
                            na_rep="—",
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
                    st.download_button(
                        "Download benchmark-relative diagnostics CSV",
                        data=relative_frame.to_csv(index=False).encode("utf-8"),
                        file_name="neural_networks_benchmark_relative_diagnostics.csv",
                        mime="text/csv",
                    )
                with st.expander("View backtest trades"):
                    st.dataframe(
                        backtest_trades.style.format(
                            {
                                "Probability up": "{:.3f}",
                                "Entry close": "{:.2f}",
                                "Exit close": "{:.2f}",
                                "Gross return": "{:.2%}",
                                "Net return after costs": "{:.2%}",
                            }
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
                st.subheader("Trade-return distribution")
                trade_distribution = summarize_backtest_trade_distribution(backtest_trades)
                st.caption(
                    "These statistics describe completed simulated trades after the configured costs. "
                    "Profit factor is undefined when there are no losing trades. Trade statistics are "
                    "sample-dependent and do not establish future profitability."
                )
                st.dataframe(
                    trade_distribution.style.format(
                        {
                            "Win rate": "{:.1%}",
                            "Mean net return": "{:.2%}",
                            "Median net return": "{:.2%}",
                            "Net return standard deviation": "{:.2%}",
                            "Best net trade": "{:.2%}",
                            "Worst net trade": "{:.2%}",
                            "Profit factor": "{:.3f}",
                            "Gross profit from winning trades": "{:.2%}",
                            "Gross loss from losing trades": "{:.2%}",
                        },
                        na_rep="—",
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                st.subheader("Transaction-cost sensitivity")
                st.caption(
                    "Re-estimates trade outcomes using gross trade returns at alternative per-side cost "
                    "assumptions. A round trip is represented as two units of turnover. This uses a "
                    "linear cost approximation, not a fill simulator; taxes, spread, market impact, and "
                    "slippage must be considered separately."
                )
                gross_trade_returns = pd.to_numeric(
                    backtest_trades["Gross return"], errors="coerce"
                )

                cost_sensitivity = transaction_cost_sensitivity(
                    gross_trade_returns.reset_index(drop=True),
                    turnover=pd.Series(2.0, index=range(len(gross_trade_returns))),
                    cost_bps=(0.0, 5.0, 10.0, 20.0, 30.0),
                )
                st.dataframe(
                    cost_sensitivity.style.format(
                        {
                            "cost_bps": "{:.1f}",
                            "gross_return": "{:.2%}",
                            "net_return": "{:.2%}",
                            "cost_drag": "{:.2%}",
                            "total_turnover": "{:.1f}",
                        },
                        na_rep="—",
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                st.download_button(
                    "Download transaction-cost sensitivity CSV",
                    data=cost_sensitivity.to_csv(index=False).encode("utf-8"),
                    file_name="neural_networks_transaction_cost_sensitivity.csv",
                    mime="text/csv",
                )
                st.download_button(
                    "Download trade-return distribution CSV",
                    data=trade_distribution.to_csv(index=False).encode("utf-8"),
                    file_name="neural_networks_trade_return_distribution.csv",
                    mime="text/csv",
                )
                st.download_button(
                    "Download backtest trades CSV",
                    data=backtest_trades.to_csv(index=False).encode("utf-8"),
                    file_name="neural_networks_cost_aware_trades.csv",
                    mime="text/csv",
                )
                st.info(
                    "Interpretation caution: these are directional classification metrics, not trading returns. "
                    "They exclude transaction costs, slippage, and execution constraints. Do not treat them as "
                    "live signals; compare results across folds and test a cost-aware strategy separately."
                )
            except (ValueError, KeyError) as exc:
                st.error(f"Could not train the model: {exc}")
            except Exception as exc:  # Keep upload errors visible instead of crashing the page.
                st.error(f"Unexpected model error: {exc}")
    except Exception as exc:
        st.error(f"Unexpected data preparation error: {exc}")
