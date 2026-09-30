"""Multi-symbol AI trading intelligence scanner."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from ai_trading.features import build_features
from ai_trading.signal_engine import score_features


def scan_universe(
    symbols: list[str], exchange: str = "NSE", period: str = "1y"
) -> pd.DataFrame:
    """Scan a universe and return the latest AI trading intelligence signals."""
    exchange = exchange.upper()
    if exchange not in {"NSE", "BSE"}:
        raise ValueError("exchange must be NSE or BSE")
    if not symbols:
        return pd.DataFrame()

    suffix = ".NS" if exchange == "NSE" else ".BO"
    tickers = [
        s if str(s).upper().endswith(suffix) else f"{str(s).strip().upper()}{suffix}"
        for s in symbols
    ]
    data = yf.download(
        tickers=tickers,
        period=period,
        auto_adjust=False,
        progress=False,
        group_by="ticker",
        threads=True,
    )
    if data.empty:
        return pd.DataFrame()

    rows: list[dict[str, object]] = []
    for symbol, ticker in zip(symbols, tickers, strict=True):
        if isinstance(data.columns, pd.MultiIndex):
            if ticker not in data.columns.get_level_values(0):
                continue
            frame = data[ticker].copy()
        else:
            frame = data.copy()
        frame = frame.dropna(how="all")
        if frame.empty or "Close" not in frame.columns:
            continue
        try:
            features = build_features(frame)
            signals = score_features(features)
        except (TypeError, ValueError, KeyError):
            continue
        if signals.empty:
            continue
        latest = signals.iloc[-1]
        close = pd.to_numeric(frame["Close"], errors="coerce").dropna()
        if close.empty:
            continue
        rows.append(
            {
                "symbol": str(symbol).upper().removesuffix(suffix),
                "exchange": exchange,
                "price": float(close.iloc[-1]),
                "ai_score": round(float(latest["score"]), 4),
                "confidence_pct": round(float(latest["confidence"]) * 100, 1),
                "signal": str(latest["signal"]),
                "return_5_pct": round(float(features["return_5"].iloc[-1]) * 100, 2),
                "return_20_pct": round(float(features["return_20"].iloc[-1]) * 100, 2),
                "volatility_pct": round(
                    float(features["volatility_20"].iloc[-1]) * 100, 2
                ),
                "volume_ratio": round(float(features["volume_ratio"].iloc[-1]), 2),
            }
        )

    columns = [
        "symbol",
        "exchange",
        "price",
        "ai_score",
        "confidence_pct",
        "signal",
        "return_5_pct",
        "return_20_pct",
        "volatility_pct",
        "volume_ratio",
    ]
    if not rows:
        return pd.DataFrame(columns=columns)
    return (
        pd.DataFrame(rows, columns=columns)
        .sort_values(["confidence_pct", "ai_score"], ascending=False)
        .reset_index(drop=True)
    )
