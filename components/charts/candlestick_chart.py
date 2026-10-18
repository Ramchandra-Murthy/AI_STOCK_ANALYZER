# ruff: noqa: I001

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

_PRICE_COLUMNS = (
    "Open",
    "High",
    "Low",
    "Close",
    "EMA20",
    "EMA50",
    "EMA200",
    "BB_Upper",
    "BB_Lower",
    "Support",
    "Resistance",
)


def plot_candlestick(df):
    """Build a price chart with validated OHLC data and a separate volume axis."""
    if df is None or df.empty:
        raise ValueError("No historical price data is available for the chart.")

    missing = [column for column in ("Open", "High", "Low", "Close") if column not in df]
    if missing:
        raise ValueError(f"Cannot plot chart: missing required columns: {', '.join(missing)}")

    chart = df.copy()
    # Historical market bars must share a clean, chronological date axis.
    # Invalid, duplicate, or unsorted index values can stretch Plotly's axis
    # and visually compress otherwise valid candles.
    dates = pd.to_datetime(chart.index, errors="coerce", utc=True)
    valid_dates = ~pd.isna(dates)
    chart = chart.loc[valid_dates].copy()
    chart.index = dates[valid_dates]
    chart = chart.loc[~chart.index.duplicated(keep="last")].sort_index()
    if chart.empty:
        raise ValueError("No valid dated price rows remain after date validation.")

    for column in _PRICE_COLUMNS:
        if column in chart.columns:
            chart[column] = pd.to_numeric(chart[column], errors="coerce")

    # Zero or negative OHLC values are invalid for ordinary NSE equity prices.
    valid_ohlc = chart[["Open", "High", "Low", "Close"]].notna().all(axis=1)
    valid_ohlc &= (chart[["Open", "High", "Low", "Close"]] > 0).all(axis=1)
    valid_ohlc &= chart["High"] >= chart[["Open", "Low", "Close"]].max(axis=1)
    valid_ohlc &= chart["Low"] <= chart[["Open", "High", "Close"]].min(axis=1)
    chart = chart.loc[valid_ohlc].copy()

    if chart.empty:
        raise ValueError("No valid positive OHLC candles remain after data validation.")

    if "Volume" in chart.columns:
        chart["Volume"] = pd.to_numeric(chart["Volume"], errors="coerce").clip(lower=0)

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.76, 0.24],
        subplot_titles=("Technical Price Chart", "Volume"),
    )

    fig.add_trace(
        go.Candlestick(
            x=chart.index,
            open=chart["Open"],
            high=chart["High"],
            low=chart["Low"],
            close=chart["Close"],
            name="Price",
        ),
        row=1,
        col=1,
    )

    indicator_specs = (
        ("EMA20", "EMA 20", 1.5, "solid"),
        ("EMA50", "EMA 50", 1.5, "solid"),
        ("EMA200", "EMA 200", 2, "solid"),
        ("BB_Upper", "BB Upper", 1, "dot"),
        ("BB_Lower", "BB Lower", 1, "dot"),
        ("Support", "Support", 1, "dash"),
        ("Resistance", "Resistance", 1, "dash"),
    )
    for column, label, width, dash in indicator_specs:
        if column not in chart.columns:
            continue
        values = chart[column].where(chart[column] > 0)
        if values.notna().any():
            fig.add_trace(
                go.Scatter(
                    x=chart.index,
                    y=values,
                    mode="lines",
                    name=label,
                    connectgaps=False,
                    line={"width": width, "dash": dash},
                ),
                row=1,
                col=1,
            )

    if "Volume" in chart.columns:
        fig.add_trace(
            go.Bar(x=chart.index, y=chart["Volume"], name="Volume"),
            row=2,
            col=1,
        )

    # Derive the visible price range from valid OHLC and positive indicators so
    # an erroneous zero/negative indicator cannot flatten the entire chart.
    price_values = [chart[column] for column in ("Low", "High")]
    for column in ("EMA20", "EMA50", "EMA200", "BB_Upper", "BB_Lower", "Support", "Resistance"):
        if column in chart.columns:
            valid_values = chart[column].where(chart[column] > 0).dropna()
            if not valid_values.empty:
                price_values.append(valid_values)
    combined_prices = pd.concat(price_values).dropna()
    if not combined_prices.empty:
        low, high = float(combined_prices.min()), float(combined_prices.max())
        padding = max((high - low) * 0.05, high * 0.005)
        fig.update_yaxes(range=[max(0, low - padding), high + padding], row=1, col=1)

    fig.update_layout(
        template="plotly_white",
        height=760,
        autosize=True,
        hovermode="x unified",
        xaxis_rangeslider_visible=False,
        margin={"l": 65, "r": 25, "t": 100, "b": 60},
        legend={
            "orientation": "h",
            "y": 1.04,
            "x": 0,
            "xanchor": "left",
            "yanchor": "bottom",
        },
    )
    fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", rangemode="tozero", row=2, col=1)
    # Explicitly constrain both shared axes to the validated candle window.
    x_range = [chart.index.min(), chart.index.max()]
    fig.update_xaxes(showgrid=True, range=x_range, row=1, col=1)
    fig.update_xaxes(showgrid=True, range=x_range, row=2, col=1)
    return fig
