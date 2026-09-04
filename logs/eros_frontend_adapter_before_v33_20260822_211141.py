from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from services.analyzer import analyze_stock
from scanner.market_scanner import market_scan
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

        self._query_gateway = (
            EROSBlock109InstitutionalApplicationQueryGateway()
        )

    # ==========================================================
    # GOVERNANCE
    # ==========================================================

    def governance(self) -> Dict[str, Any]:
        """
        Return the frontend-visible EROS governance state.
        """

        return {
            "system": "EROS 3.0",
            "status": "CERTIFIED",
            "query_gateway": {
                "block_id": "109",
                "name": (
                    "Institutional Application Query Gateway"
                ),
                "status": "CERTIFIED",
            },
            "safety": deepcopy(
                self.SAFETY_POLICY
            ),
        }

    # ==========================================================
    # STOCK ANALYSIS
    # ==========================================================

    def stock_analysis(
        self,
        symbol: str,
    ) -> Dict[str, Any]:
        """
        Read-only stock analysis using the existing
        AI Stock Analyzer service.
        """

        if not isinstance(symbol, str):
            raise TypeError(
                "symbol must be a string"
            )

        symbol = symbol.strip().upper()

        if not symbol:
            raise ValueError(
                "symbol cannot be empty"
            )

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
    ) -> Dict[str, Any]:
        """
        Return a frontend-safe dashboard snapshot.
        """

        governance = self.governance()

        return {
            "system": {
                "name": "EROS 3.0",
                "description": (
                    "Institutional Intelligence "
                    "Command Center"
                ),
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
            raise TypeError(
                "STOCK_ANALYSIS_RESULT_MUST_BE_DICT"
            )

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
            "recommendation": signal.get(
                "Recommendation"
            ),
            "risk": signal.get("Risk"),

            "reasons": list(
                signal.get("Reasons") or []
            ),

            "breakout_signal": breakout.get(
                "Signal"
            ),

            "breakout_reason": breakout.get(
                "Reason"
            ),

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

    def snapshot(self) -> Dict[str, Any]:
        """
        Return immutable frontend adapter metadata.
        """

        return {
            "name": "EROSFrontendAdapter",
            "version": self.VERSION,
            "source": "Block 109",
            "mode": "READ_ONLY",
            "safety": deepcopy(
                self.SAFETY_POLICY
            ),
        }

    def decision_intelligence(self, symbol: str) -> Dict[str, Any]:
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

        recommendation = evidence.get(
            "recommendation",
            "UNKNOWN"
        )

        risk = evidence.get(
            "risk",
            "UNKNOWN"
        )

        trend = evidence.get(
            "trend",
            "UNKNOWN"
        )

        momentum = evidence.get(
            "momentum",
            "UNKNOWN"
        )

        breakout_signal = evidence.get(
            "breakout_signal",
            "NONE"
        )

        reasons = evidence.get(
            "reasons",
            []
        )

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
                "risk": risk
            },

            "market_context": {
                "trend": trend,
                "momentum": momentum,
                "breakout_signal": breakout_signal,
                "breakout_reason": evidence.get(
                    "breakout_reason",
                    ""
                )
            },

            "technical_drivers": technical_drivers,

            "technical_indicators": technical,

            "risk_flags": risk_flags,

            "summary": summary,

            "governance": {
                "read_only": bool(
                    governance.get("read_only", True)
                ),
                "execution_blocked": bool(
                    governance.get("execution_blocked", True)
                ),
                "non_mutation_invariant": bool(
                    governance.get(
                        "non_mutation_invariant",
                        True
                    )
                )
            }
        }

    def decision_interpretation(self, symbol: str) -> Dict[str, Any]:
        """
        EROS 3.0 V3.1 Decision Interpretation Engine.

        Converts the certified V3.0 decision_intelligence()
        object into an interpretive, read-only decision view.

        No execution.
        No broker interaction.
        No database mutation.
        """

        intelligence = self.decision_intelligence(symbol)

        decision = intelligence.get(
            "decision",
            {}
        )

        context = intelligence.get(
            "market_context",
            {}
        )

        technical = intelligence.get(
            "technical_indicators",
            {}
        )

        drivers = intelligence.get(
            "technical_drivers",
            []
        )

        risk_flags = intelligence.get(
            "risk_flags",
            []
        )

        governance = intelligence.get(
            "governance",
            {}
        )

        price = intelligence.get("price")

        try:
            price_value = float(price)
        except (TypeError, ValueError):
            price_value = None

        try:
            score = float(
                decision.get("score", 0)
            )
        except (TypeError, ValueError):
            score = 0.0

        try:
            confidence = float(
                decision.get("confidence", 0)
            )
        except (TypeError, ValueError):
            confidence = 0.0

        recommendation = decision.get(
            "recommendation",
            "UNKNOWN"
        )

        trend = context.get(
            "trend",
            "UNKNOWN"
        )

        momentum = context.get(
            "momentum",
            "UNKNOWN"
        )

        breakout = context.get(
            "breakout_signal",
            "NONE"
        )

        # ----------------------------------------------------
        # PRIMARY DRIVERS
        # ----------------------------------------------------

        primary_drivers = []

        for driver in drivers:

            if not isinstance(driver, str):
                continue

            driver_lower = driver.lower()

            if (
                "sma" in driver_lower
                or "ema" in driver_lower
                or "macd" in driver_lower
            ):
                primary_drivers.append(driver)

        # ----------------------------------------------------
        # SUPPORTING DRIVERS
        # ----------------------------------------------------

        supporting_drivers = []

        for driver in drivers:

            if not isinstance(driver, str):
                continue

            if driver not in primary_drivers:
                supporting_drivers.append(driver)

        # ----------------------------------------------------
        # CONFLICT DETECTION
        # ----------------------------------------------------

        conflicting_signals = []

        rsi = technical.get("rsi_14")
        macd = technical.get("macd")
        signal = technical.get("signal")
        sma20 = technical.get("sma_20")
        sma50 = technical.get("sma_50")
        ema20 = technical.get("ema_20")
        support = technical.get("support")
        resistance = technical.get("resistance")

        try:

            if rsi is not None:

                rsi_value = float(rsi)

                if score >= 60 and rsi_value < 30:
                    conflicting_signals.append(
                        "Oversold momentum condition"
                    )

                if score >= 60 and rsi_value > 70:
                    conflicting_signals.append(
                        "Overbought momentum condition"
                    )

        except (TypeError, ValueError):
            pass

        try:

            if (
                macd is not None
                and signal is not None
            ):

                if score >= 60 and float(macd) < float(signal):
                    conflicting_signals.append(
                        "MACD below signal line"
                    )

                if score < 40 and float(macd) > float(signal):
                    conflicting_signals.append(
                        "MACD above signal line"
                    )

        except (TypeError, ValueError):
            pass

        try:

            if (
                sma20 is not None
                and sma50 is not None
            ):

                if score >= 60 and float(sma20) < float(sma50):
                    conflicting_signals.append(
                        "Short-term moving average below long-term average"
                    )

                if score < 40 and float(sma20) > float(sma50):
                    conflicting_signals.append(
                        "Short-term moving average above long-term average"
                    )

        except (TypeError, ValueError):
            pass

        # ----------------------------------------------------
        # MARKET CONDITION
        # ----------------------------------------------------

        if (
            trend == "Bullish"
            and momentum == "Strong"
        ):
            market_condition = "BULLISH_MOMENTUM"

        elif trend == "Bullish":
            market_condition = "BULLISH"

        elif (
            trend == "Bearish"
            and momentum == "Strong"
        ):
            market_condition = "BEARISH_MOMENTUM"

        elif trend == "Bearish":
            market_condition = "BEARISH"

        else:
            market_condition = "NEUTRAL"

        # ----------------------------------------------------
        # PRICE LOCATION
        # ----------------------------------------------------

        price_context = "UNKNOWN"

        if (
            price_value is not None
            and support is not None
            and resistance is not None
        ):

            try:

                support_value = float(support)
                resistance_value = float(resistance)

                if price_value <= support_value * 1.02:
                    price_context = "NEAR_SUPPORT"

                elif price_value >= resistance_value * 0.98:
                    price_context = "NEAR_RESISTANCE"

                else:
                    price_context = "MID_RANGE"

            except (TypeError, ValueError):
                pass

        # ----------------------------------------------------
        # BREAKOUT CONTEXT
        # ----------------------------------------------------

        if breakout == "NONE":
            breakout_context = "NO_ACTIVE_BREAKOUT"

        elif breakout:
            breakout_context = str(
                breakout
            )

        else:
            breakout_context = "UNKNOWN"

        # ----------------------------------------------------
        # DECISION QUALITY
        # ----------------------------------------------------

        if (
            score >= 80
            and confidence >= 80
            and len(conflicting_signals) == 0
        ):
            decision_quality = "HIGH"

        elif (
            score >= 60
            and confidence >= 60
        ):
            decision_quality = "MEDIUM"

        else:
            decision_quality = "LOW"

        # ----------------------------------------------------
        # INVALIDATION CONTEXT
        # ----------------------------------------------------

        invalidation = []

        if support is not None:

            invalidation.append(
                f"Monitor price behavior around support "
                f"{float(support):.2f}"
            )

        if resistance is not None:

            invalidation.append(
                f"Monitor price behavior around resistance "
                f"{float(resistance):.2f}"
            )

        if conflicting_signals:

            invalidation.extend(
                conflicting_signals
            )

        if not invalidation:

            invalidation.append(
                "No explicit technical invalidation detected."
            )

        # ----------------------------------------------------
        # INTERPRETATION
        # ----------------------------------------------------

        if recommendation in (
            "STRONG BUY",
            "BUY"
        ):

            interpretation = (
                f"The technical evidence currently supports "
                f"a {recommendation} stance. "
                f"The market condition is {market_condition}. "
                f"Decision quality is {decision_quality}."
            )

        elif recommendation in (
            "STRONG SELL",
            "SELL"
        ):

            interpretation = (
                f"The technical evidence currently supports "
                f"a {recommendation} stance. "
                f"The market condition is {market_condition}. "
                f"Decision quality is {decision_quality}."
            )

        else:

            interpretation = (
                f"The technical evidence currently supports "
                f"a {recommendation} stance. "
                f"The market condition is {market_condition}. "
                f"Decision quality is {decision_quality}."
            )

        # ----------------------------------------------------
        # NORMALIZED V3.1 OBJECT
        # ----------------------------------------------------

        return {

            "symbol": intelligence.get(
                "symbol",
                symbol
            ),

            "price": price_value,

            "decision": decision,

            "interpretation": {

                "market_condition": market_condition,

                "price_context": price_context,

                "breakout_context": breakout_context,

                "decision_quality": decision_quality,

                "primary_drivers": primary_drivers,

                "supporting_drivers": supporting_drivers,

                "conflicting_signals": conflicting_signals,

                "interpretation": interpretation,

                "invalidation_context": invalidation
            },

            "technical_indicators": technical,

            "governance": {

                "read_only": bool(
                    governance.get(
                        "read_only",
                        True
                    )
                ),

                "execution_blocked": bool(
                    governance.get(
                        "execution_blocked",
                        True
                    )
                ),

                "non_mutation_invariant": bool(
                    governance.get(
                        "non_mutation_invariant",
                        True
                    )
                )
            }
        }


    def decision_action_framework(self, symbol: str) -> dict:
        """
        EROS V3.2 - Decision Action Framework

        Converts V3.1 decision interpretation into a structured,
        read-only action framework.

        SAFETY:
        - No database writes
        - No portfolio mutation
        - No order creation
        - No broker submission
        - No live execution
        - No optimization
        """

        interpretation = self.decision_interpretation(symbol)

        decision = interpretation.get("decision", {})
        market_context = interpretation.get("market_context", {})
        technical_indicators = interpretation.get(
            "technical_indicators",
            {}
        )
        interpretation_block = interpretation.get(
            "interpretation",
            {}
        )

        recommendation = decision.get(
            "recommendation",
            "NO ACTION"
        )

        stance = decision.get(
            "stance",
            "NEUTRAL"
        )

        risk = decision.get(
            "risk",
            "UNKNOWN"
        )

        score = float(
            decision.get("score", 0.0)
        )

        confidence = float(
            decision.get("confidence", 0.0)
        )

        price_context = interpretation_block.get(
            "price_context",
            "UNKNOWN"
        )

        breakout_context = interpretation_block.get(
            "breakout_context",
            "UNKNOWN"
        )

        support = technical_indicators.get(
            "support"
        )

        resistance = technical_indicators.get(
            "resistance"
        )

        # ----------------------------------------------------
        # ACTION CLASSIFICATION
        # ----------------------------------------------------

        if (
            stance == "BULLISH"
            and recommendation in (
                "BUY",
                "STRONG BUY"
            )
            and confidence >= 70
        ):
            if price_context == "NEAR_SUPPORT":
                action = "WAIT_FOR_CONFIRMATION"
            elif breakout_context == "ACTIVE_BREAKOUT":
                action = "BREAKOUT_CONFIRMATION"
            else:
                action = "BULLISH_SETUP"

        elif (
            stance == "BEARISH"
            and recommendation in (
                "SELL",
                "STRONG SELL"
            )
            and confidence >= 70
        ):
            action = "BEARISH_SETUP"

        else:
            action = "WAIT"

        # ----------------------------------------------------
        # CONFIRMATION CONDITIONS
        # ----------------------------------------------------

        confirmation = []

        if support is not None:
            confirmation.append(
                f"Hold above support {float(support):.2f}"
            )

        if resistance is not None:
            confirmation.append(
                f"Monitor resistance {float(resistance):.2f}"
            )

        if breakout_context == "ACTIVE_BREAKOUT":
            confirmation.append(
                "Confirm breakout persistence"
            )

        if not confirmation:
            confirmation.append(
                "Await additional technical confirmation"
            )

        # ----------------------------------------------------
        # INVALIDATION CONDITIONS
        # ----------------------------------------------------

        invalidation = []

        if support is not None:
            invalidation.append(
                f"Sustained breakdown below support "
                f"{float(support):.2f}"
            )

        if resistance is not None and stance == "BULLISH":
            invalidation.append(
                f"Failure near resistance "
                f"{float(resistance):.2f}"
            )

        if not invalidation:
            invalidation.append(
                "Material deterioration in decision evidence"
            )

        # ----------------------------------------------------
        # RISK CONTEXT
        # ----------------------------------------------------

        if risk == "Low":
            risk_context = "LOW"
        elif risk == "Medium":
            risk_context = "MODERATE"
        elif risk == "High":
            risk_context = "HIGH"
        else:
            risk_context = "UNKNOWN"

        # ----------------------------------------------------
        # ACTION CONFIDENCE
        # ----------------------------------------------------

        if confidence >= 80:
            action_confidence = "HIGH"
        elif confidence >= 60:
            action_confidence = "MEDIUM"
        else:
            action_confidence = "LOW"

        # ----------------------------------------------------
        # READ-ONLY GOVERNANCE
        # ----------------------------------------------------

        governance = {
            "read_only": True,
            "execution_blocked": True,
            "non_mutation_invariant": True,
            "allow_order_creation": False,
            "allow_broker_submission": False,
            "allow_live_execution": False,
            "allow_portfolio_mutation": False,
            "allow_optimization": False
        }

        return {
            "symbol": symbol,
            "price": interpretation.get("price"),

            "action": {
                "classification": action,
                "stance": stance,
                "recommendation": recommendation,
                "score": score,
                "confidence": confidence,
                "confidence_band": action_confidence,
                "risk_context": risk_context
            },

            "market_context": {
                "price_context": price_context,
                "breakout_context": breakout_context,
                "support": support,
                "resistance": resistance
            },

            "confirmation_conditions": confirmation,

            "invalidation_conditions": invalidation,

            "interpretation_summary": (
                interpretation_block.get(
                    "interpretation",
                    ""
                )
            ),

            "governance": governance
        }
