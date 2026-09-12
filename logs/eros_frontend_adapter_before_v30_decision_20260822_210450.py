from __future__ import annotations

from copy import deepcopy
from typing import Any

from scanner.market_scanner import market_scan
from services.analyzer import analyze_stock
from services.quantitative.block109_institutional_application_query_gateway import (
    EROSBlock109InstitutionalApplicationQueryGateway,
)


class EROSFrontendAdapter:
    """
    EROS 3.0 read-only frontend adapter.

    Purpose:
        Provide a stable interface between the Streamlit frontend
        and the existing EROS / AI Stock Analyzer services.

    Safety:
        - Read only
        - No order creation
        - No broker submission
        - No live execution
        - No portfolio mutation
        - No valuation mutation
        - No performance mutation
        - No risk mutation
        - No optimization
    """

    VERSION = "1.0"

    SAFETY_POLICY = {
        "read_only": True,
        "allow_order_creation": False,
        "allow_broker_submission": False,
        "allow_live_execution": False,
        "allow_portfolio_mutation": False,
        "allow_valuation_mutation": False,
        "allow_performance_mutation": False,
        "allow_risk_mutation": False,
        "allow_optimization": False,
        "execution_blocked": True,
        "non_mutation_invariant": True,
    }

    def __init__(self) -> None:

        self._query_gateway = EROSBlock109InstitutionalApplicationQueryGateway()

    # ==========================================================
    # GOVERNANCE
    # ==========================================================

    def governance(self) -> dict[str, Any]:
        """
        Return the frontend-visible EROS governance state.
        """

        return {
            "system": "EROS 3.0",
            "status": "CERTIFIED",
            "query_gateway": {
                "block_id": "109",
                "name": ("Institutional Application Query Gateway"),
                "status": "CERTIFIED",
            },
            "safety": deepcopy(self.SAFETY_POLICY),
        }

    # ==========================================================
    # STOCK ANALYSIS
    # ==========================================================

    def stock_analysis(
        self,
        symbol: str,
    ) -> dict[str, Any]:
        """
        Read-only stock analysis using the existing
        AI Stock Analyzer service.
        """

        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")

        symbol = symbol.strip().upper()

        if not symbol:
            raise ValueError("symbol cannot be empty")

        result = analyze_stock(symbol)

        return result

    # ==========================================================
    # MARKET SCANNER
    # ==========================================================

    def market_scan(self):
        """
        Read-only market scanner.

        Returns the existing scanner dataframe.
        """

        return market_scan()

    # ==========================================================
    # DASHBOARD SNAPSHOT
    # ==========================================================

    def dashboard_snapshot(
        self,
    ) -> dict[str, Any]:
        """
        Return a frontend-safe dashboard snapshot.
        """

        governance = self.governance()

        return {
            "system": {
                "name": "EROS 3.0",
                "description": ("Institutional Intelligence " "Command Center"),
                "status": "CERTIFIED",
            },
            "gateway": governance["query_gateway"],
            "safety": governance["safety"],
        }

    # ==========================================================
    # SNAPSHOT
    # ==========================================================

    def decision_evidence(self, symbol: str) -> dict:
        """
        EROS V2.9 normalized read-only decision evidence.

        This method consumes the existing stock_analysis()
        result and exposes a stable evidence contract.

        No database writes are performed.
        No portfolio mutation is performed.
        No broker or execution path is exposed.
        """

        result = self.stock_analysis(symbol)

        if not isinstance(result, dict):
            raise TypeError("STOCK_ANALYSIS_RESULT_MUST_BE_DICT")

        trend = result.get("trend") or {}
        signal = result.get("signal") or {}
        breakout = result.get("breakout") or {}
        last = result.get("last")

        def value_from_last(name):
            try:
                if last is not None and name in last:

                    value = last[name]

                    if hasattr(value, "item"):
                        value = value.item()

                    if value is None:
                        return None

                    try:
                        if value != value:
                            return None
                    except Exception:
                        pass

                    return value

            except Exception:
                return None

            return None

        evidence = {
            "symbol": symbol,
            "price": value_from_last("Close"),
            "trend": trend.get("Trend"),
            "momentum": trend.get("Momentum"),
            "score": signal.get("Score"),
            "confidence": signal.get("Confidence"),
            "recommendation": signal.get("Recommendation"),
            "risk": signal.get("Risk"),
            "reasons": list(signal.get("Reasons") or []),
            "breakout_signal": breakout.get("Signal"),
            "breakout_reason": breakout.get("Reason"),
            "technical_indicators": {
                "sma_20": value_from_last("SMA_20"),
                "sma_50": value_from_last("SMA_50"),
                "ema_20": value_from_last("EMA_20"),
                "rsi_14": value_from_last("RSI_14"),
                "macd": value_from_last("MACD"),
                "signal": value_from_last("Signal"),
                "histogram": value_from_last("Histogram"),
                "bb_middle": value_from_last("BB_Middle"),
                "bb_upper": value_from_last("BB_Upper"),
                "bb_lower": value_from_last("BB_Lower"),
                "atr": value_from_last("ATR"),
                "support": value_from_last("Support"),
                "resistance": value_from_last("Resistance"),
            },
            "governance": {
                "read_only": True,
                "execution_blocked": True,
                "non_mutation_invariant": True,
            },
        }

        return evidence

    def snapshot(self) -> dict[str, Any]:
        """
        Return immutable frontend adapter metadata.
        """

        return {
            "name": "EROSFrontendAdapter",
            "version": self.VERSION,
            "source": "Block 109",
            "mode": "READ_ONLY",
            "safety": deepcopy(self.SAFETY_POLICY),
        }
