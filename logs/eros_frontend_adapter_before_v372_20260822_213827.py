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

    def decision_convergence(self, symbol: str = "RELIANCE.NS"):
        """
        EROS V3.6
        Decision Convergence Engine.

        Read-only analytical convergence layer.
        No database writes.
        No execution.
        """

        scenario = self.decision_scenario_engine(symbol)

        explanation = self.decision_scenario_explanation(symbol)

        action = self.decision_action_framework(symbol)

        interpretation = self.decision_interpretation(symbol)

        evidence = self.decision_evidence(symbol)

        intelligence = self.decision_intelligence(symbol)

        decision = intelligence.get("decision", {})
        scenario_data = scenario.get("scenarios", {})
        explanation_data = explanation.get("scenario_explanation", {})
        action_data = action.get("action", {})
        interpretation_data = interpretation.get("interpretation", {})

        primary_scenario = scenario.get("primary_scenario", "BASE")

        confirmation_logic = action.get("confirmation_conditions", [])

        invalidation_logic = action.get("invalidation_conditions", [])

        primary_drivers = interpretation_data.get("primary_drivers", [])

        supporting_drivers = interpretation_data.get("supporting_drivers", [])

        conflicting_signals = interpretation_data.get("conflicting_signals", [])

        decision_quality = interpretation_data.get(
            "decision_quality", scenario.get("decision_quality", "UNKNOWN")
        )

        stance = decision.get("stance", action_data.get("stance", "UNKNOWN"))

        recommendation = decision.get(
            "recommendation", action_data.get("recommendation", "UNKNOWN")
        )

        confidence = decision.get("confidence", action_data.get("confidence", 0.0))

        risk = decision.get("risk", action_data.get("risk_context", "UNKNOWN"))

        classification = action_data.get("classification", "UNKNOWN")

        bull = scenario_data.get("bull", {})
        bear = scenario_data.get("bear", {})
        base = scenario_data.get("base", {})

        convergence = {
            "symbol": symbol,
            "price": scenario.get("price", evidence.get("price")),
            "decision": {
                "stance": stance,
                "recommendation": recommendation,
                "classification": classification,
                "confidence": confidence,
                "risk": risk,
                "decision_quality": decision_quality,
            },
            "convergence": {
                "primary_scenario": primary_scenario,
                "base": {
                    "classification": base.get("classification"),
                    "stance": base.get("stance"),
                    "conditions": base.get("conditions", []),
                },
                "bull_confirmation": {
                    "classification": bull.get("classification"),
                    "stance": bull.get("stance"),
                    "conditions": bull.get("conditions", []),
                    "decision_effect": bull.get("decision_effect"),
                },
                "bear_invalidation": {
                    "classification": bear.get("classification"),
                    "stance": bear.get("stance"),
                    "conditions": bear.get("conditions", []),
                    "decision_effect": bear.get("decision_effect"),
                },
                "confirmation_logic": confirmation_logic,
                "invalidation_logic": invalidation_logic,
                "primary_drivers": primary_drivers,
                "supporting_drivers": supporting_drivers,
                "conflicting_signals": conflicting_signals,
            },
            "interpretation": {
                "market_condition": interpretation_data.get("market_condition"),
                "price_context": interpretation_data.get("price_context"),
                "breakout_context": interpretation_data.get("breakout_context"),
                "decision_quality": decision_quality,
            },
            "conclusion": (
                f"{symbol} currently has a "
                f"{stance} stance with "
                f"{recommendation} recommendation. "
                f"The current analytical classification is "
                f"{classification}. "
                f"The primary scenario is "
                f"{primary_scenario}. "
                f"Bull confirmation depends on the defined "
                f"confirmation conditions, while bear "
                f"invalidation depends on the defined "
                f"invalidation conditions."
            ),
            "governance": {
                "read_only": True,
                "execution_blocked": True,
                "non_mutation_invariant": True,
                "allow_order_creation": False,
                "allow_broker_submission": False,
                "allow_live_execution": False,
                "allow_portfolio_mutation": False,
                "allow_valuation_mutation": False,
                "allow_performance_mutation": False,
                "allow_risk_mutation": False,
                "allow_optimization": False,
            },
        }

        return convergence

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

    def decision_interpretation(self, symbol: str) -> dict[str, Any]:
        """
        EROS 3.0 V3.1 Decision Interpretation Engine.

        Converts the certified V3.0 decision_intelligence()
        object into an interpretive, read-only decision view.

        No execution.
        No broker interaction.
        No database mutation.
        """

        intelligence = self.decision_intelligence(symbol)

        decision = intelligence.get("decision", {})

        context = intelligence.get("market_context", {})

        technical = intelligence.get("technical_indicators", {})

        drivers = intelligence.get("technical_drivers", [])

        risk_flags = intelligence.get("risk_flags", [])

        governance = intelligence.get("governance", {})

        price = intelligence.get("price")

        try:
            price_value = float(price)
        except (TypeError, ValueError):
            price_value = None

        try:
            score = float(decision.get("score", 0))
        except (TypeError, ValueError):
            score = 0.0

        try:
            confidence = float(decision.get("confidence", 0))
        except (TypeError, ValueError):
            confidence = 0.0

        recommendation = decision.get("recommendation", "UNKNOWN")

        trend = context.get("trend", "UNKNOWN")

        momentum = context.get("momentum", "UNKNOWN")

        breakout = context.get("breakout_signal", "NONE")

        # ----------------------------------------------------
        # PRIMARY DRIVERS
        # ----------------------------------------------------

        primary_drivers = []

        for driver in drivers:

            if not isinstance(driver, str):
                continue

            driver_lower = driver.lower()

            if "sma" in driver_lower or "ema" in driver_lower or "macd" in driver_lower:
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
                    conflicting_signals.append("Oversold momentum condition")

                if score >= 60 and rsi_value > 70:
                    conflicting_signals.append("Overbought momentum condition")

        except (TypeError, ValueError):
            pass

        try:

            if macd is not None and signal is not None:

                if score >= 60 and float(macd) < float(signal):
                    conflicting_signals.append("MACD below signal line")

                if score < 40 and float(macd) > float(signal):
                    conflicting_signals.append("MACD above signal line")

        except (TypeError, ValueError):
            pass

        try:

            if sma20 is not None and sma50 is not None:

                if score >= 60 and float(sma20) < float(sma50):
                    conflicting_signals.append("Short-term moving average below long-term average")

                if score < 40 and float(sma20) > float(sma50):
                    conflicting_signals.append("Short-term moving average above long-term average")

        except (TypeError, ValueError):
            pass

        # ----------------------------------------------------
        # MARKET CONDITION
        # ----------------------------------------------------

        if trend == "Bullish" and momentum == "Strong":
            market_condition = "BULLISH_MOMENTUM"

        elif trend == "Bullish":
            market_condition = "BULLISH"

        elif trend == "Bearish" and momentum == "Strong":
            market_condition = "BEARISH_MOMENTUM"

        elif trend == "Bearish":
            market_condition = "BEARISH"

        else:
            market_condition = "NEUTRAL"

        # ----------------------------------------------------
        # PRICE LOCATION
        # ----------------------------------------------------

        price_context = "UNKNOWN"

        if price_value is not None and support is not None and resistance is not None:

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
            breakout_context = str(breakout)

        else:
            breakout_context = "UNKNOWN"

        # ----------------------------------------------------
        # DECISION QUALITY
        # ----------------------------------------------------

        if score >= 80 and confidence >= 80 and len(conflicting_signals) == 0:
            decision_quality = "HIGH"

        elif score >= 60 and confidence >= 60:
            decision_quality = "MEDIUM"

        else:
            decision_quality = "LOW"

        # ----------------------------------------------------
        # INVALIDATION CONTEXT
        # ----------------------------------------------------

        invalidation = []

        if support is not None:

            invalidation.append(f"Monitor price behavior around support " f"{float(support):.2f}")

        if resistance is not None:

            invalidation.append(
                f"Monitor price behavior around resistance " f"{float(resistance):.2f}"
            )

        if conflicting_signals:

            invalidation.extend(conflicting_signals)

        if not invalidation:

            invalidation.append("No explicit technical invalidation detected.")

        # ----------------------------------------------------
        # INTERPRETATION
        # ----------------------------------------------------

        if recommendation in ("STRONG BUY", "BUY"):

            interpretation = (
                f"The technical evidence currently supports "
                f"a {recommendation} stance. "
                f"The market condition is {market_condition}. "
                f"Decision quality is {decision_quality}."
            )

        elif recommendation in ("STRONG SELL", "SELL"):

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
            "symbol": intelligence.get("symbol", symbol),
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
                "invalidation_context": invalidation,
            },
            "technical_indicators": technical,
            "governance": {
                "read_only": bool(governance.get("read_only", True)),
                "execution_blocked": bool(governance.get("execution_blocked", True)),
                "non_mutation_invariant": bool(governance.get("non_mutation_invariant", True)),
            },
        }

    def decision_action_explanation(self, symbol: str) -> dict:
        """
        EROS V3.3
        Decision Action Explanation Engine.

        Converts the V3.2 action framework into a human-readable,
        structured explanation.

        READ-ONLY ONLY.
        NO DATABASE WRITE.
        NO ORDER CREATION.
        NO BROKER SUBMISSION.
        """

        action = self.decision_action_framework(symbol)

        interpretation = self.decision_interpretation(symbol)

        decision = interpretation.get("decision", {})
        technical = interpretation.get("technical_indicators", {})
        governance = interpretation.get("governance", {})

        action_block = action.get("action", {})
        market_context = action.get("market_context", {})

        classification = action_block.get("classification", "UNKNOWN")

        stance = action_block.get("stance", decision.get("stance", "UNKNOWN"))

        recommendation = action_block.get(
            "recommendation", decision.get("recommendation", "UNKNOWN")
        )

        confidence = action_block.get("confidence", decision.get("confidence", 0.0))

        confidence_band = action_block.get(
            "confidence_band", decision.get("confidence_band", "UNKNOWN")
        )

        risk_context = action_block.get("risk_context", decision.get("risk", "UNKNOWN"))

        price = interpretation.get("price", action.get("price"))

        support = market_context.get("support", technical.get("support"))

        resistance = market_context.get("resistance", technical.get("resistance"))

        price_context = market_context.get("price_context", "UNKNOWN")

        breakout_context = market_context.get("breakout_context", "UNKNOWN")

        confirmation_conditions = action.get("confirmation_conditions", [])

        invalidation_conditions = action.get("invalidation_conditions", [])

        interpretation_block = interpretation.get("interpretation", {})

        primary_drivers = interpretation_block.get("primary_drivers", [])

        supporting_drivers = interpretation_block.get("supporting_drivers", [])

        conflicting_signals = interpretation_block.get("conflicting_signals", [])

        decision_quality = interpretation_block.get("decision_quality", "UNKNOWN")

        if classification == "WAIT_FOR_CONFIRMATION":
            primary_reason = (
                "The underlying evidence is favorable, "
                "but the current price context requires confirmation "
                "before the action classification can strengthen."
            )

        elif classification == "ACTIONABLE":
            primary_reason = (
                "The evidence, market context and confirmation state "
                "support the current action classification."
            )

        elif classification == "AVOID":
            primary_reason = (
                "The current evidence does not provide sufficient "
                "support for a favorable action."
            )

        else:
            primary_reason = (
                "The action classification is derived from the "
                "current decision intelligence and interpretation."
            )

        supporting_reasons = []

        if stance != "UNKNOWN":
            supporting_reasons.append(f"Overall stance is {stance}.")

        if recommendation != "UNKNOWN":
            supporting_reasons.append(f"Recommendation is {recommendation}.")

        if confidence_band != "UNKNOWN":
            supporting_reasons.append(f"Confidence is {confidence_band} " f"({confidence:.1f}%).")

        if price_context != "UNKNOWN":
            supporting_reasons.append(f"Price context is {price_context}.")

        if breakout_context != "UNKNOWN":
            supporting_reasons.append(f"Breakout context is {breakout_context}.")

        confirmation_logic = list(confirmation_conditions)

        invalidation_logic = list(invalidation_conditions)

        if not confirmation_logic:
            confirmation_logic.append("No additional confirmation condition was generated.")

        if not invalidation_logic:
            invalidation_logic.append("No explicit invalidation condition was generated.")

        risk_explanation = (
            f"Risk context is {risk_context}. "
            "Risk is informational only and does not authorize execution."
        )

        explanation_summary = (
            f"{symbol} is classified as {classification} with "
            f"{stance} stance and {recommendation} recommendation. "
            f"Decision confidence is {confidence:.1f}% "
            f"({confidence_band}). "
            f"Price context is {price_context}."
        )

        return {
            "symbol": symbol,
            "price": price,
            "action": {
                "classification": classification,
                "stance": stance,
                "recommendation": recommendation,
                "confidence": confidence,
                "confidence_band": confidence_band,
                "risk_context": risk_context,
            },
            "explanation": {
                "primary_reason": primary_reason,
                "supporting_reasons": supporting_reasons,
                "primary_drivers": primary_drivers,
                "supporting_drivers": supporting_drivers,
                "conflicting_signals": conflicting_signals,
                "confirmation_logic": confirmation_logic,
                "invalidation_logic": invalidation_logic,
                "decision_quality": decision_quality,
                "risk_explanation": risk_explanation,
                "price_context": price_context,
                "support": support,
                "resistance": resistance,
                "breakout_context": breakout_context,
                "summary": explanation_summary,
                "execution_status": "BLOCKED",
            },
            "governance": {
                "read_only": True,
                "execution_blocked": True,
                "non_mutation_invariant": True,
                "allow_order_creation": False,
                "allow_broker_submission": False,
                "allow_live_execution": False,
                "allow_portfolio_mutation": False,
                "allow_valuation_mutation": False,
                "allow_performance_mutation": False,
                "allow_risk_mutation": False,
                "allow_optimization": False,
            },
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
        technical_indicators = interpretation.get("technical_indicators", {})
        interpretation_block = interpretation.get("interpretation", {})

        recommendation = decision.get("recommendation", "NO ACTION")

        stance = decision.get("stance", "NEUTRAL")

        risk = decision.get("risk", "UNKNOWN")

        score = float(decision.get("score", 0.0))

        confidence = float(decision.get("confidence", 0.0))

        price_context = interpretation_block.get("price_context", "UNKNOWN")

        breakout_context = interpretation_block.get("breakout_context", "UNKNOWN")

        support = technical_indicators.get("support")

        resistance = technical_indicators.get("resistance")

        # ----------------------------------------------------
        # ACTION CLASSIFICATION
        # ----------------------------------------------------

        if stance == "BULLISH" and recommendation in ("BUY", "STRONG BUY") and confidence >= 70:
            if price_context == "NEAR_SUPPORT":
                action = "WAIT_FOR_CONFIRMATION"
            elif breakout_context == "ACTIVE_BREAKOUT":
                action = "BREAKOUT_CONFIRMATION"
            else:
                action = "BULLISH_SETUP"

        elif stance == "BEARISH" and recommendation in ("SELL", "STRONG SELL") and confidence >= 70:
            action = "BEARISH_SETUP"

        else:
            action = "WAIT"

        # ----------------------------------------------------
        # CONFIRMATION CONDITIONS
        # ----------------------------------------------------

        confirmation = []

        if support is not None:
            confirmation.append(f"Hold above support {float(support):.2f}")

        if resistance is not None:
            confirmation.append(f"Monitor resistance {float(resistance):.2f}")

        if breakout_context == "ACTIVE_BREAKOUT":
            confirmation.append("Confirm breakout persistence")

        if not confirmation:
            confirmation.append("Await additional technical confirmation")

        # ----------------------------------------------------
        # INVALIDATION CONDITIONS
        # ----------------------------------------------------

        invalidation = []

        if support is not None:
            invalidation.append(f"Sustained breakdown below support " f"{float(support):.2f}")

        if resistance is not None and stance == "BULLISH":
            invalidation.append(f"Failure near resistance " f"{float(resistance):.2f}")

        if not invalidation:
            invalidation.append("Material deterioration in decision evidence")

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
            "allow_optimization": False,
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
                "risk_context": risk_context,
            },
            "market_context": {
                "price_context": price_context,
                "breakout_context": breakout_context,
                "support": support,
                "resistance": resistance,
            },
            "confirmation_conditions": confirmation,
            "invalidation_conditions": invalidation,
            "interpretation_summary": (interpretation_block.get("interpretation", "")),
            "governance": governance,
        }

    def decision_scenario_engine(self, symbol: str = "RELIANCE.NS") -> dict:
        """
        V3.4 Decision Scenario Engine.

        Read-only analytical layer.
        No orders.
        No broker submission.
        No execution.
        No portfolio mutation.
        No database writes.
        """

        interpretation = self.decision_interpretation(symbol)

        decision = interpretation.get("decision", {})
        interp = interpretation.get("interpretation", {})
        technical = interpretation.get("technical_indicators", {})
        governance = interpretation.get("governance", {})

        price = float(interpretation.get("price", 0.0))

        support = technical.get("support", interp.get("support"))

        resistance = technical.get("resistance", interp.get("resistance"))

        stance = str(decision.get("stance", "NEUTRAL"))
        recommendation = str(decision.get("recommendation", "HOLD"))

        confidence = float(decision.get("confidence", 0.0))

        risk = str(decision.get("risk", "UNKNOWN"))

        # ----------------------------------------------------
        # BASE SCENARIO
        # ----------------------------------------------------

        base_conditions = []

        if support is not None:
            base_conditions.append(f"Price remains above support {float(support):.2f}")

        if resistance is not None:
            base_conditions.append(f"Price continues to monitor resistance {float(resistance):.2f}")

        base = {
            "scenario": "BASE",
            "stance": stance,
            "classification": "WAIT_FOR_CONFIRMATION",
            "conditions": base_conditions,
            "decision_effect": (
                "Maintain the current analytical stance while "
                "confirmation conditions remain unresolved."
            ),
        }

        # ----------------------------------------------------
        # BULL SCENARIO
        # ----------------------------------------------------

        bull_conditions = []

        if resistance is not None:
            bull_conditions.append(f"Confirmed move above resistance {float(resistance):.2f}")

        bull_conditions.append("Bullish trend and momentum remain intact")

        bull = {
            "scenario": "BULL",
            "stance": "BULLISH",
            "classification": "CONFIRMATION",
            "conditions": bull_conditions,
            "decision_effect": (
                "A confirmed upside move would strengthen the " "existing bullish decision context."
            ),
        }

        # ----------------------------------------------------
        # BEAR SCENARIO
        # ----------------------------------------------------

        bear_conditions = []

        if support is not None:
            bear_conditions.append(f"Sustained breakdown below support {float(support):.2f}")

        bear_conditions.append("Bullish technical structure deteriorates")

        bear = {
            "scenario": "BEAR",
            "stance": "BEARISH",
            "classification": "INVALIDATION",
            "conditions": bear_conditions,
            "decision_effect": (
                "A sustained breakdown would invalidate the "
                "current bullish confirmation structure."
            ),
        }

        # ----------------------------------------------------
        # SCENARIO PRIORITY
        # ----------------------------------------------------

        if stance == "BULLISH":
            primary = "BULL"
        elif stance == "BEARISH":
            primary = "BEAR"
        else:
            primary = "BASE"

        # ----------------------------------------------------
        # SAFETY
        # ----------------------------------------------------

        safe_governance = {
            "read_only": True,
            "execution_blocked": True,
            "non_mutation_invariant": True,
            "allow_order_creation": False,
            "allow_broker_submission": False,
            "allow_live_execution": False,
            "allow_portfolio_mutation": False,
            "allow_valuation_mutation": False,
            "allow_performance_mutation": False,
            "allow_risk_mutation": False,
            "allow_optimization": False,
        }

        return {
            "symbol": symbol,
            "price": price,
            "current_decision": {
                "stance": stance,
                "recommendation": recommendation,
                "confidence": confidence,
                "risk": risk,
            },
            "primary_scenario": primary,
            "scenarios": {"base": base, "bull": bull, "bear": bear},
            "decision_quality": interp.get("decision_quality", "UNKNOWN"),
            "scenario_summary": (
                f"{symbol} currently has a {stance} stance with "
                f"{recommendation} recommendation. The primary "
                f"scenario is {primary}."
            ),
            "governance": safe_governance,
        }

    def decision_scenario_explanation(self, symbol: str) -> dict[str, Any]:
        """
        EROS V3.5
        Scenario Explanation Engine.

        Pure read-only interpretation layer over V3.4.
        No database writes.
        No portfolio mutation.
        No execution capability.
        """

        scenario_data = self.decision_scenario_engine(symbol)

        current = scenario_data.get("current_decision", {})
        scenarios = scenario_data.get("scenarios", {})

        base = scenarios.get("base", {})
        bull = scenarios.get("bull", {})
        bear = scenarios.get("bear", {})

        base_conditions = base.get("conditions", [])
        bull_conditions = bull.get("conditions", [])
        bear_conditions = bear.get("conditions", [])

        explanation = {
            "symbol": scenario_data.get("symbol"),
            "price": scenario_data.get("price"),
            "current_decision": current,
            "primary_scenario": scenario_data.get("primary_scenario"),
            "scenario_explanation": {
                "base": {
                    "meaning": (
                        "The BASE scenario represents the current "
                        "analytical state while confirmation remains "
                        "unresolved."
                    ),
                    "stance": base.get("stance"),
                    "classification": base.get("classification"),
                    "conditions": base_conditions,
                    "decision_effect": base.get("decision_effect"),
                },
                "bull": {
                    "meaning": (
                        "The BULL scenario represents confirmation "
                        "of the existing bullish structure."
                    ),
                    "stance": bull.get("stance"),
                    "classification": bull.get("classification"),
                    "conditions": bull_conditions,
                    "decision_effect": bull.get("decision_effect"),
                },
                "bear": {
                    "meaning": (
                        "The BEAR scenario represents invalidation "
                        "of the current bullish structure."
                    ),
                    "stance": bear.get("stance"),
                    "classification": bear.get("classification"),
                    "conditions": bear_conditions,
                    "decision_effect": bear.get("decision_effect"),
                },
            },
            "decision_quality": scenario_data.get("decision_quality"),
            "interpretation": (scenario_data.get("scenario_summary")),
            "confirmation_logic": bull_conditions,
            "invalidation_logic": bear_conditions,
            "summary": (
                f"{scenario_data.get('symbol')} currently has a "
                f"{current.get('stance')} stance with "
                f"{current.get('recommendation')} recommendation. "
                f"The primary scenario is "
                f"{scenario_data.get('primary_scenario')}. "
                f"The BULL scenario represents confirmation, while "
                f"the BEAR scenario represents invalidation."
            ),
            "governance": {
                "read_only": True,
                "execution_blocked": True,
                "non_mutation_invariant": True,
                "allow_order_creation": False,
                "allow_broker_submission": False,
                "allow_live_execution": False,
                "allow_portfolio_mutation": False,
                "allow_valuation_mutation": False,
                "allow_performance_mutation": False,
                "allow_risk_mutation": False,
                "allow_optimization": False,
            },
        }

        return explanation

    def decision_traceability(self, symbol: str = "RELIANCE.NS") -> dict[str, Any]:
        """
        EROS 3.0 - V3.7 Decision Traceability Engine.

        Purpose
        -------
        Converts the existing V3.6 decision-convergence output into
        a structured read-only traceability object.

        The method does not:
            - create orders
            - submit orders
            - execute trades
            - mutate portfolios
            - mutate valuation
            - mutate performance
            - mutate risk
            - perform optimization
            - write to the database

        Traceability connects:

            technical evidence
                    |
                    v
            decision intelligence
                    |
                    v
            interpretation
                    |
                    v
            action framework
                    |
                    v
            scenario analysis
                    |
                    v
            convergence
                    |
                    v
            final analytical conclusion

        This is an analytical provenance layer only.
        """

        convergence = self.decision_convergence(symbol)

        if not isinstance(convergence, dict):
            raise RuntimeError("TRACEABILITY_CONVERGENCE_NOT_DICT")

        decision = convergence.get("decision", {})
        convergence_data = convergence.get("convergence", {})
        interpretation = convergence.get("interpretation", {})
        governance = convergence.get("governance", {})

        traceability = {
            "symbol": convergence.get("symbol"),
            "price": convergence.get("price"),
            "decision": {
                "stance": decision.get("stance"),
                "recommendation": decision.get("recommendation"),
                "classification": decision.get("classification"),
                "confidence": decision.get("confidence"),
                "risk": decision.get("risk"),
                "decision_quality": decision.get("decision_quality"),
            },
            "trace": {
                "stage_1_evidence": {
                    "source": "decision_evidence",
                    "status": "AVAILABLE",
                },
                "stage_2_intelligence": {
                    "source": "decision_intelligence",
                    "status": "AVAILABLE",
                },
                "stage_3_interpretation": {
                    "source": "decision_interpretation",
                    "status": "AVAILABLE",
                    "market_condition": interpretation.get("market_condition"),
                    "price_context": interpretation.get("price_context"),
                    "breakout_context": interpretation.get("breakout_context"),
                },
                "stage_4_action_framework": {
                    "source": "decision_action_framework",
                    "status": "AVAILABLE",
                },
                "stage_5_action_explanation": {
                    "source": "decision_action_explanation",
                    "status": "AVAILABLE",
                },
                "stage_6_scenario_engine": {
                    "source": "decision_scenario_engine",
                    "status": "AVAILABLE",
                },
                "stage_7_scenario_explanation": {
                    "source": "decision_scenario_explanation",
                    "status": "AVAILABLE",
                },
                "stage_8_convergence": {
                    "source": "decision_convergence",
                    "status": "AVAILABLE",
                    "primary_scenario": convergence_data.get("primary_scenario"),
                },
            },
            "evidence_chain": {
                "primary_drivers": convergence_data.get("primary_drivers", []),
                "supporting_drivers": convergence_data.get("supporting_drivers", []),
                "conflicting_signals": convergence_data.get("conflicting_signals", []),
                "confirmation_logic": convergence_data.get("confirmation_logic", []),
                "invalidation_logic": convergence_data.get("invalidation_logic", []),
            },
            "scenario_trace": {
                "primary_scenario": convergence_data.get("primary_scenario"),
                "base": convergence_data.get("base", {}),
                "bull_confirmation": convergence_data.get("bull_confirmation", {}),
                "bear_invalidation": convergence_data.get("bear_invalidation", {}),
            },
            "interpretation": {
                "market_condition": interpretation.get("market_condition"),
                "price_context": interpretation.get("price_context"),
                "breakout_context": interpretation.get("breakout_context"),
                "decision_quality": interpretation.get("decision_quality"),
            },
            "conclusion": convergence.get("conclusion", ""),
            "traceability_status": "COMPLETE",
            "governance": {
                "read_only": True,
                "execution_blocked": True,
                "non_mutation_invariant": True,
                "allow_order_creation": False,
                "allow_broker_submission": False,
                "allow_live_execution": False,
                "allow_portfolio_mutation": False,
                "allow_valuation_mutation": False,
                "allow_performance_mutation": False,
                "allow_risk_mutation": False,
                "allow_optimization": False,
            },
        }

        return traceability
