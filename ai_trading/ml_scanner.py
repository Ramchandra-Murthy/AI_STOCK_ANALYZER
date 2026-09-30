"""Multi-stock ML scanner for AI trading intelligence."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from ai_trading.ml_model import predict_latest, train_model


def scan_frames(
    frames: dict[str, pd.DataFrame],
    *,
    exchange: str = "NSE",
    horizon: int = 5,
    threshold: float = 0.01,
) -> pd.DataFrame:
    """Train and validate one ML model per symbol and return ranked results."""
    exchange = exchange.upper()
    if exchange not in {"NSE", "BSE"}:
        raise ValueError("exchange must be NSE or BSE")

    rows: list[dict[str, object]] = []
    for symbol, frame in frames.items():
        try:
            model, validation = train_model(
                frame,
                horizon=horizon,
                threshold=threshold,
            )
            prediction = predict_latest(model, frame)
        except (TypeError, ValueError, KeyError):
            continue

        rows.append(
            {
                "symbol": str(symbol).upper(),
                "exchange": exchange,
                "probability_up_pct": round(
                    float(prediction["probability_up"]) * 100, 1
                ),
                "confidence_pct": round(float(prediction["confidence"]) * 100, 1),
                "signal": str(prediction["signal"]),
                "accuracy_pct": round(validation.accuracy * 100, 1),
                "roc_auc": round(validation.roc_auc, 3)
                if validation.roc_auc is not None
                else None,
                "train_samples": validation.train_samples,
                "test_samples": validation.test_samples,
            }
        )

    columns = [
        "symbol",
        "exchange",
        "probability_up_pct",
        "confidence_pct",
        "signal",
        "accuracy_pct",
        "roc_auc",
        "train_samples",
        "test_samples",
    ]
    if not rows:
        return pd.DataFrame(columns=columns)

    return (
        pd.DataFrame(rows, columns=columns)
        .sort_values(
            ["confidence_pct", "roc_auc", "probability_up_pct"],
            ascending=False,
        )
        .reset_index(drop=True)
    )


def scan_universe(
    symbols: list[str],
    *,
    exchange: str = "NSE",
    period: str = "5y",
    horizon: int = 5,
    threshold: float = 0.01,
) -> pd.DataFrame:
    """Download market history and run the ML model across a stock universe."""
    exchange = exchange.upper()
    if exchange not in {"NSE", "BSE"}:
        raise ValueError("exchange must be NSE or BSE")
    if not symbols:
        return pd.DataFrame()

    suffix = ".NS" if exchange == "NSE" else ".BO"
    tickers = [
        str(symbol).strip().upper()
        if str(symbol).upper().endswith(suffix)
        else f"{str(symbol).strip().upper()}{suffix}"
        for symbol in symbols
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

    frames: dict[str, pd.DataFrame] = {}
    for symbol, ticker in zip(symbols, tickers, strict=True):
        try:
            if isinstance(data.columns, pd.MultiIndex):
                if ticker not in data.columns.get_level_values(0):
                    continue
                frame = data[ticker].copy()
            else:
                frame = data.copy()
            frame = frame.dropna(how="all")
            if not frame.empty and "Close" in frame.columns:
                frames[str(symbol).upper().removesuffix(suffix)] = frame
        except (KeyError, TypeError):
            continue

    return scan_frames(
        frames,
        exchange=exchange,
        horizon=horizon,
        threshold=threshold,
    )
