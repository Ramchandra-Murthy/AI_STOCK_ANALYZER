"""Multi-symbol NSE/BSE algorithmic opportunity scanner."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from algorithmic_trading.pipeline import AlgorithmicAnalysis, analyze_symbol


def scan_universe(
    symbols: list[str],
    exchange: str,
    capital: float,
    risk_fraction: float = 0.01,
    period: str = "1y",
    relative_periods: int = 20,
) -> pd.DataFrame:
    """Run the transparent algorithmic pipeline across an exchange universe."""
    exchange = exchange.upper()
    if exchange not in {"NSE", "BSE"}:
        raise ValueError("exchange must be NSE or BSE")
    if not symbols:
        return pd.DataFrame()

    tickers = [_ticker(symbol, exchange) for symbol in symbols]
    benchmark_ticker = "^NSEI" if exchange == "NSE" else "^BSESN"
    market = yf.download(
        tickers=tickers,
        period=period,
        auto_adjust=False,
        progress=False,
        group_by="ticker",
        threads=True,
    )
    benchmark = yf.download(
        tickers=benchmark_ticker,
        period=period,
        auto_adjust=False,
        progress=False,
    )

    if market.empty or benchmark.empty:
        return pd.DataFrame()

    benchmark_close = _close_series(benchmark)
    rows: list[dict[str, object]] = []

    for symbol, ticker in zip(symbols, tickers):
        frame = _symbol_frame(market, ticker)
        if frame.empty or "Close" not in frame:
            continue
        try:
            result = analyze_symbol(
                symbol=symbol,
                frame=frame,
                benchmark=benchmark_close,
                capital=capital,
                risk_fraction=risk_fraction,
                relative_periods=relative_periods,
            )
        except (TypeError, ValueError, IndexError):
            continue
        rows.append(_row(result, exchange, ticker, frame))

    return _result_frame(rows)


def _ticker(symbol: str, exchange: str) -> str:
    clean = str(symbol).strip().upper()
    if not clean:
        raise ValueError("symbols must not contain empty values")
    suffix = ".NS" if exchange == "NSE" else ".BO"
    return clean if clean.endswith(suffix) else f"{clean}{suffix}"


def _symbol_frame(market: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if isinstance(market.columns, pd.MultiIndex):
        if ticker not in market.columns.get_level_values(0):
            return pd.DataFrame()
        frame = market[ticker].copy()
    else:
        frame = market.copy()
    return frame.dropna(how="all")


def _close_series(frame: pd.DataFrame) -> pd.Series:
    if isinstance(frame.columns, pd.MultiIndex):
        frame = frame.copy()
        frame.columns = frame.columns.get_level_values(0)
    if "Close" not in frame:
        return pd.Series(dtype=float)
    return pd.to_numeric(frame["Close"], errors="coerce").dropna()


def _row(
    result: AlgorithmicAnalysis,
    exchange: str,
    ticker: str,
    frame: pd.DataFrame,
) -> dict[str, object]:
    close = pd.to_numeric(frame["Close"], errors="coerce").dropna()
    return {
        "symbol": result.symbol,
        "exchange": exchange,
        "ticker": ticker,
        "price": float(close.iloc[-1]),
        "regime": result.regime,
        "regime_score": result.regime_score,
        "relative_return_pct": result.relative_return_pct,
        "signal": result.signal.direction,
        "signal_score": result.signal.score,
        "quantity": result.position_size.quantity,
        "risk_budget": result.position_size.risk_budget,
    }


def _result_frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    columns = [
        "symbol",
        "exchange",
        "ticker",
        "price",
        "regime",
        "regime_score",
        "relative_return_pct",
        "signal",
        "signal_score",
        "quantity",
        "risk_budget",
    ]
    if not rows:
        return pd.DataFrame(columns=columns)
    return (
        pd.DataFrame(rows, columns=columns)
        .sort_values(["signal_score", "relative_return_pct"], ascending=False)
        .reset_index(drop=True)
    )
