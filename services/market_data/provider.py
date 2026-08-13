from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from services.market_data.adapter import MarketDataPacket

logger = logging.getLogger(__name__)

class YahooFinanceDataProvider:
    """
    EROS 3.0 Block 23C Actual Market Data Provider.
    Fetches real-world market data using yfinance with robust fallback/error handling for institutional reliability.
    """
    @staticmethod
    def fetch_live_market_data(symbol: str) -> MarketDataPacket:
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            
            if hist.empty:
                raise ValueError(f"No price history returned for symbol {symbol}")

            current_price = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else current_price
            volume = int(hist["Volume"].iloc[-1])

            ohlcv = []
            for date_idx, row in hist.iterrows():
                ohlcv.append({
                    "date": str(date_idx.date()),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"])
                })

            return MarketDataPacket(
                symbol=symbol,
                current_price=current_price,
                previous_close=prev_close,
                volume=volume,
                ohlcv_history=ohlcv,
                is_stale=False,
                details={"source": "yfinance-live-api", "currency": "INR"}
            )
        except Exception as e:
            logger.warning("Live data fetch failed for %s (%s). Falling back to institutional parity baseline.", symbol, str(e))
            # Resilient Fallback mechanism ensuring pipeline continuity
            fallback_prices = {
                "RELIANCE.NS": 2450.0,
                "INFY.NS": 1550.0,
                "TCS.NS": 3800.0,
                "HDFCBANK.NS": 1650.0,
                "ICICIBANK.NS": 1050.0,
            }
            price = fallback_prices.get(symbol, 1000.0)
            return MarketDataPacket(
                symbol=symbol,
                current_price=price,
                previous_close=price * 0.99,
                volume=1000000,
                ohlcv_history=[{"date": str(datetime.utcnow().date()), "close": price, "volume": 1000000}],
                is_stale=True,
                details={"source": "fallback-parity-adapter", "error": str(e)}
            )
