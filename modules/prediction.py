import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# ==========================================================
# Download Stock Data
# ==========================================================


def download_stock(symbol):

    try:

        df = yf.download(
            symbol.strip().upper(),
            period="1y",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
        )

        if df is None or df.empty:
            return None

        # Handle MultiIndex columns (new yfinance versions)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df

    except Exception as e:

        st.exception(e)
        return None


# ==========================================================
# Prediction Model
# ==========================================================


def predict_prices(df, days=30):

    close = df["Close"].astype(float)

    last_price = float(close.iloc[-1])

    ma20 = float(close.rolling(20).mean().iloc[-1])

    if pd.isna(ma20):
        ma20 = last_price

    trend = last_price - ma20

    forecast = []

    price = last_price

    for _ in range(days):

        price = price + trend * 0.10

        forecast.append(round(price, 2))

    return forecast


# ==========================================================
# Prediction Page
# ==========================================================


def show():

    st.title("🤖 AI Stock Price Prediction")

    st.write("Simple AI prediction using moving-average trend forecasting.")

    symbol = st.text_input("Stock Symbol", value="RELIANCE.NS")

    forecast_days = st.slider("Forecast Days", 5, 60, 30)

    if st.button("Predict"):

        with st.spinner("Downloading market data..."):

            df = download_stock(symbol)

        if df is None:

            st.error(f"Unable to download data for {symbol}")

            return

        st.success("Market data downloaded successfully.")

        st.subheader("Latest Market Data")

        st.dataframe(df.tail(), use_container_width=True)

        prediction = predict_prices(df, forecast_days)

        current_price = float(df["Close"].iloc[-1])

        predicted_price = prediction[-1]

        expected_return = ((predicted_price - current_price) / current_price) * 100

        st.divider()

        c1, c2, c3 = st.columns(3)

        c1.metric("Current Price", f"₹{current_price:,.2f}")

        c2.metric("Predicted Price", f"₹{predicted_price:,.2f}")

        c3.metric("Expected Return", f"{expected_return:.2f}%")

        st.divider()

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Historical Price")
        )

        future_dates = pd.date_range(
            start=df.index[-1], periods=forecast_days + 1, freq="B"
        )[1:]

        fig.add_trace(
            go.Scatter(
                x=future_dates, y=prediction, mode="lines+markers", name="AI Prediction"
            )
        )

        fig.update_layout(
            title=f"{symbol} Price Prediction",
            xaxis_title="Date",
            yaxis_title="Price",
            height=600,
            template="plotly_white",
        )

        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        if expected_return > 10:

            st.success("🟢 Strong Bullish Outlook")

        elif expected_return > 3:

            st.info("🟡 Bullish Outlook")

        elif expected_return > -3:

            st.warning("🟠 Sideways Outlook")

        else:

            st.error("🔴 Bearish Outlook")

        st.divider()

        st.subheader("Prediction Summary")

        summary = pd.DataFrame(
            {
                "Metric": [
                    "Stock",
                    "Forecast",
                    "Current Price",
                    "Predicted Price",
                    "Expected Return",
                ],
                "Value": [
                    symbol,
                    f"{forecast_days} Days",
                    f"₹{current_price:.2f}",
                    f"₹{predicted_price:.2f}",
                    f"{expected_return:.2f}%",
                ],
            }
        )

        st.table(summary)

        st.info(
            "This is an educational trend-based forecasting model and should not be treated as investment advice."
        )
