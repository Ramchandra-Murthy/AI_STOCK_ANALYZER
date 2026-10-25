"""Research-only Neural Networks Lab page."""

from __future__ import annotations

from io import BytesIO, StringIO

import pandas as pd
import streamlit as st
import yfinance as yf

from neural_networks.baseline import train_baseline
from neural_networks.features import build_direction_dataset

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
                    st.success(
                        f"Fetched {len(downloaded):,} daily rows for {normalized_symbol}."
                    )
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
                _, metrics = train_baseline(features, target, train_fraction=float(train_fraction))
                split_at = int(len(features) * float(train_fraction))
                test_dates = features.index[split_at:]
                left, middle, right = st.columns(3)
                left.metric("Holdout accuracy", f"{metrics['accuracy']:.1%}")
                middle.metric("Test observations", f"{metrics['test_samples']:,}")
                if "roc_auc" in metrics:
                    right.metric("ROC-AUC", f"{metrics['roc_auc']:.3f}")
                else:
                    right.metric("ROC-AUC", "Unavailable")
                st.caption(
                    f"Train: {features.index[0].date()} to "
                    f"{features.index[split_at - 1].date()} · "
                    f"Test: {test_dates[0].date()} to {test_dates[-1].date()} · "
                    f"Label: positive close-to-close return after {int(horizon)} trading days."
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
                st.info(
                    "Interpretation caution: accuracy and ROC-AUC exclude transaction costs and slippage. "
                    "Compare against a majority-class baseline and use walk-forward testing before considering any strategy."
                )
            except (ValueError, KeyError) as exc:
                st.error(f"Could not train the model: {exc}")
            except Exception as exc:  # Keep upload errors visible instead of crashing the page.
                st.error(f"Unexpected model error: {exc}")
