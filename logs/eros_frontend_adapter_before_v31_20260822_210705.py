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

    def decision_intelligence(self, symbol: str) -> dict[str, Any]:
        """
        EROS 3.0 V3.0 Decision Intelligence Foundation.

        Purpose:
            Convert the certified V2.9 decision_evidence() object
            into a normalized read-only intelligence object.

        Safety:
            - No database writes
            - No portfolio mutation
            - No valuation mutation
            - No risk mutation
            - No optimization
            - No broker submission
            - No live execution
        """

        evidence = self.decision_evidence(symbol)

        technical = evidence.get("technical_indicators", {})
        governance = evidence.get("governance", {})

        score = evidence.get("score")
        confidence = evidence.get("confidence")

        try:
            score_value = float(score)
        except (TypeError, ValueError):
            score_value = 0.0

        try:
            confidence_value = float(confidence)
        except (TypeError, ValueError):
            confidence_value = 0.0

        recommendation = evidence.get("recommendation", "UNKNOWN")

        risk = evidence.get("risk", "UNKNOWN")

        trend = evidence.get("trend", "UNKNOWN")

        momentum = evidence.get("momentum", "UNKNOWN")

        breakout_signal = evidence.get("breakout_signal", "NONE")

        reasons = evidence.get("reasons", [])

        if not isinstance(reasons, list):
            reasons = [str(reasons)]

        # ----------------------------------------------------
        # MARKET STANCE
        # ----------------------------------------------------

        if recommendation in ("STRONG BUY", "BUY"):
            stance = "BULLISH"
        elif recommendation in ("STRONG SELL", "SELL"):
            stance = "BEARISH"
        elif recommendation == "HOLD":
            stance = "NEUTRAL"
        else:
            stance = "UNDEFINED"

        # ----------------------------------------------------
        # CONFIDENCE BAND
        # ----------------------------------------------------

        if confidence_value >= 80:
            confidence_band = "HIGH"
        elif confidence_value >= 60:
            confidence_band = "MEDIUM"
        elif confidence_value >= 40:
            confidence_band = "LOW"
        else:
            confidence_band = "VERY LOW"

        # ----------------------------------------------------
        # SCORE BAND
        # ----------------------------------------------------

        if score_value >= 80:
            score_band = "STRONG"
        elif score_value >= 60:
            score_band = "POSITIVE"
        elif score_value >= 40:
            score_band = "NEUTRAL"
        else:
            score_band = "WEAK"

        # ----------------------------------------------------
        # RISK FLAGS
        # ----------------------------------------------------

        risk_flags = []

        if risk:
            risk_flags.append(str(risk))

        if breakout_signal and breakout_signal != "NONE":
            risk_flags.append("BREAKOUT_EVENT")

        support = technical.get("support")
        resistance = technical.get("resistance")
        price = evidence.get("price")

        if (
            isinstance(price, (int, float))
            and isinstance(support, (int, float))
            and isinstance(resistance, (int, float))
        ):
            if price <= support * 1.02:
                risk_flags.append("NEAR_SUPPORT")

            if price >= resistance * 0.98:
                risk_flags.append("NEAR_RESISTANCE")

        # ----------------------------------------------------
        # TECHNICAL DRIVERS
        # ----------------------------------------------------

        technical_drivers = []

        for reason in reasons:
            if isinstance(reason, str):
                technical_drivers.append(reason)

        # ----------------------------------------------------
        # DECISION SUMMARY
        # ----------------------------------------------------

        summary = (
            f"{evidence.get('symbol', symbol)} is "
            f"{stance.lower()} with "
            f"{recommendation} recommendation, "
            f"score {score_value:.0f}/100 and "
            f"{confidence_value:.0f}% confidence."
        )

        # ----------------------------------------------------
        # NORMALIZED V3.0 OBJECT
        # ----------------------------------------------------

        return {
            "symbol": evidence.get("symbol", symbol),
            "price": evidence.get("price"),
            "decision": {
                "stance": stance,
                "recommendation": recommendation,
                "score": score_value,
                "score_band": score_band,
                "confidence": confidence_value,
                "confidence_band": confidence_band,
                "risk": risk,
            },
            "market_context": {
                "trend": trend,
                "momentum": momentum,
                "breakout_signal": breakout_signal,
                "breakout_reason": evidence.get("breakout_reason", ""),
            },
            "technical_drivers": technical_drivers,
            "technical_indicators": technical,
            "risk_flags": risk_flags,
            "summary": summary,
            "governance": {
                "read_only": bool(governance.get("read_only", True)),
                "execution_blocked": bool(governance.get("execution_blocked", True)),
                "non_mutation_invariant": bool(governance.get("non_mutation_invariant", True)),
            },
        }
