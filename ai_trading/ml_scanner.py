"""Multi-stock ML scanner for AI trading intelligence."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from ai_trading.features import build_features
from ai_trading.ml_model import predict_latest, train_model
from ai_trading.regime_context import build_regime_context
from ai_trading.regime_decision import build_regime_aware_decision


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
            latest_features = build_features(frame).iloc[-1]
            return_score = max(-1.0, min(1.0, float(latest_features["return_5"]) * 4.0))
            ema_score = max(-1.0, min(1.0, float(latest_features["ema_gap"]) * 5.0))
            trend_score = (return_score + ema_score) / 2.0
            regime = build_regime_context(frame)
            decision = build_regime_aware_decision(
                probability_up=float(prediction["probability_up"]),
                accuracy=validation.accuracy,
                roc_auc=validation.roc_auc,
                trend_score=trend_score,
                regime=str(regime["regime"]),
                regime_strength=float(regime["regime_strength_pct"]) / 100.0,
            )
        except (TypeError, ValueError, KeyError):
            continue

        rows.append(
            {
                "symbol": str(symbol).upper(),
                "exchange": exchange,
                "latest_price": round(float(frame["Close"].dropna().iloc[-1]), 2),
                "probability_up_pct": round(float(prediction["probability_up"]) * 100, 1),
                "signal": decision.signal,
                "confidence_pct": decision.confidence_pct,
                "model_confidence_pct": decision.model_confidence_pct,
                "validation_pct": decision.validation_pct,
                "trend_pct": decision.trend_pct,
                "regime": regime["regime"],
                "regime_score": regime["regime_score"],
                "regime_strength_pct": regime["regime_strength_pct"],
                "decision_reason": decision.reason,
                "accuracy_pct": round(validation.accuracy * 100, 1),
                "roc_auc": round(validation.roc_auc, 3) if validation.roc_auc is not None else None,
                "train_samples": validation.train_samples,
                "test_samples": validation.test_samples,
            }
        )

    columns = [
        "symbol",
        "exchange",
        "latest_price",
        "probability_up_pct",
        "confidence_pct",
        "signal",
        "model_confidence_pct",
        "validation_pct",
        "trend_pct",
        "regime",
        "regime_score",
        "regime_strength_pct",
        "decision_reason",
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
        (
            str(symbol).strip().upper()
            if str(symbol).upper().endswith(suffix)
            else f"{str(symbol).strip().upper()}{suffix}"
        )
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
