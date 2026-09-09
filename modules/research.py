import math
import streamlit as st

# ==========================================================
# COMPONENTS
# ==========================================================
from components.charts.candlestick_chart import plot_candlestick
from components.technical_summary import show_technical_summary

# ==========================================================
# REPORTS
# ==========================================================
from reports.report_generator import ReportGenerator
from services.ai_service import get_ai_recommendation
from services.fundamental_score_service import calculate_fundamental_score
from services.investment_thesis_service import generate_investment_thesis
from services.news_service import get_company_news
from services.recommendation_service import generate_recommendation

# ==========================================================
# SERVICES
# ==========================================================
from services.research_service import get_stock_profile
from services.scenario_service import generate_scenario_analysis
from services.score_service import calculate_investment_score
from services.technical_score_service import calculate_technical_score
from services.technical_service import get_price_history
from services.trade_plan_service import generate_trade_plan
from services.valuation_service import generate_valuation_analysis
from services.valuation_v43_service import generate_valuation_v43

# ==========================================================
# HELPER FUNCTIONS & FORMATTERS
# ==========================================================


def _finite_number(value):
    """Return a finite float, or None for missing/invalid/non-finite input."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def format_market_cap(value):
    """Format market capitalization without displaying invalid evidence as valid."""
    number = _finite_number(value)
    if number is None or number < 0:
        return "N/A"

    if number >= 1e12:
        return f"₹{number / 1e12:.2f} Lakh Cr"
    if number >= 1e9:
        return f"₹{number / 1e7:.2f} Cr"
    if number >= 1e6:
        return f"₹{number / 1e5:.2f} Lakh"
    return f"₹{number:,.0f}"


def format_percent(value):
    """Convert finite decimal values to percentages."""
    if value in [None, "N/A"]:
        return "N/A"

    number = _finite_number(value)
    if number is None or abs(number) > 10:
        return "N/A"

    return f"{number * 100:.2f}%"


def format_dividend_yield(value):
    """
    Format Yahoo Finance dividendYield.

    Yahoo may return dividendYield as an already-percent
    value, e.g. 0.47 means 0.47%.
    """
    if value in [None, "N/A"]:
        return "N/A"

    number = _finite_number(value)
    if number is None:
        return "N/A"

    return f"{number:.2f}%"


def safe_progress(value):
    """Convert a finite 0-100 score into a Streamlit progress value."""
    score = _finite_number(value)
    if score is None or score < 0 or score > 100:
        return 0.0
    return score / 100.0


def format_price(value):
    """Safely format a finite positive price."""
    number = _finite_number(value)
    if number is None or number <= 0:
        return "N/A"
    return f"₹{number:,.2f}"


def format_ratio(value):
    """
    Format a financial ratio when it is finite and positive.

    Example:
        1.52 -> 1.52x
    """
    number = _finite_number(value)
    if number is None or number <= 0:
        return "N/A"
    return f"{number:.2f}x"


def format_debt_to_equity(value):
    """
    Format Yahoo Finance debtToEquity.

    Yahoo Finance commonly reports debtToEquity
    on a percentage-style scale.

    Example:
        36.653 -> 0.37x
    """
    number = _finite_number(value)
    if number is None or number < 0 or number > 10000:
        return "N/A"
    return f"{number / 100.0:.2f}x"


def format_large_rupees(value):
    """
    Format large rupee-denominated financial values.

    Examples:
        3.98e12 -> Rs. 3.98 Lakh Cr
        5.00e10 -> Rs. 5,000.00 Cr
    """
    number = _finite_number(value)
    if number is None:
        return "N/A"

    if number >= 1e12:
        return f"Rs. {number / 1e12:.2f} Lakh Cr"
    if number >= 1e7:
        return f"Rs. {number / 1e7:,.2f} Cr"
    if number >= 1e5:
        return f"Rs. {number / 1e5:,.2f} Lakh"
    return f"Rs. {number:,.2f}"


# ==========================================================
# MAIN SCREEN
# ==========================================================


def show():
    st.title("Stock Research Terminal")
    st.caption("Professional Equity Research Platform")

    st.divider()

    # ======================================================
    # SEARCH
    # ======================================================
    search_col, button_col = st.columns([3, 1])

    with search_col:
        entered_symbol = st.text_input(
            "Enter NSE Symbol",
            value="RELIANCE",
            key="research_symbol_input",
        )
        entered_symbol = entered_symbol.strip().upper()

    with button_col:
        st.write("")
        st.write("")
        analyze = st.button(
            "Analyze",
            use_container_width=True,
            key="research_analyze_button",
        )

    # ======================================================
    # SESSION STATE
    # ======================================================
    if "research_analyzed" not in st.session_state:
        st.session_state["research_analyzed"] = False

    if "research_active_symbol" not in st.session_state:
        st.session_state["research_active_symbol"] = None

    # ======================================================
    # ANALYZE BUTTON
    # ======================================================
    if analyze:
        if not entered_symbol:
            st.warning("Please enter an NSE symbol.")
            return

        st.session_state["research_analyzed"] = True
        st.session_state["research_active_symbol"] = entered_symbol

        # Remove previously generated PDF when a new analysis starts.
        st.session_state.pop("research_pdf", None)
        st.session_state.pop("research_pdf_symbol", None)
        st.session_state.pop("research_pdf_name", None)

    # ======================================================
    # WAIT FOR ANALYSIS
    # ======================================================
    if not st.session_state["research_analyzed"]:
        return

    symbol = st.session_state.get("research_active_symbol")

    if not symbol:
        return

    # ======================================================
    # SYMBOL CHANGE MESSAGE
    # ======================================================
    if entered_symbol and entered_symbol != symbol:
        st.info(
            f"Showing analysis for {symbol}. "
            f"Click Analyze to load {entered_symbol}."
        )

    # ======================================================
    # FETCH STOCK DATA
    # ======================================================
    try:
        with st.spinner("Fetching stock information..."):
            data = get_stock_profile(symbol)
            history = get_price_history(symbol)

    except Exception as error:
        st.error(f"Unable to fetch stock information: {error}")
        return

    if not data:
        st.error("Unable to fetch stock information.")
        return

    # ======================================================
    # AI ANALYSIS
    # ======================================================
    try:
        ai_result = get_ai_recommendation(data, history)
        if not isinstance(ai_result, dict):
            ai_result = {}
    except Exception as error:
        st.warning(f"AI recommendation unavailable: {error}")
        ai_result = {}

    # ======================================================
    # NEWS
    # ======================================================
    try:
        news = get_company_news(symbol)
        if not news:
            news = []
    except Exception as error:
        st.warning(f"Company news unavailable: {error}")
        news = []

    # ======================================================
    # TECHNICAL SCORE
    # ======================================================
    try:
        if history is not None and not history.empty:
            technical_score, technical_reasons = calculate_technical_score(history)
        else:
            technical_score = None
            technical_reasons = ["Historical price data unavailable."]
    except Exception as error:
        technical_score = None
        technical_reasons = [f"Technical scoring unavailable: {error}"]

    # ======================================================
    # FUNDAMENTAL SCORE V2
    # ======================================================
    try:
        fundamental_score, fundamental_reasons = calculate_fundamental_score(data)
    except Exception as error:
        fundamental_score = None
        fundamental_reasons = [f"Fundamental scoring unavailable: {error}"]

    # ======================================================
    # INVESTMENT SCORE V2
    # ======================================================
    try:
        investment_score, score_breakdown = calculate_investment_score(
            technical_score=technical_score,
            fundamental_score=fundamental_score,
            ai_result=ai_result,
            data=data,
        )
    except Exception as error:
        st.warning(f"Investment score unavailable: {error}")
        investment_score = None
        score_breakdown = {}

    # ======================================================
    # RECOMMENDATION ENGINE
    # ======================================================
    try:
        recommendation_result = generate_recommendation(
            investment_score=investment_score,
        )

        if not isinstance(recommendation_result, dict):
            recommendation_result = {}

    except Exception as error:
        st.warning(f"Recommendation engine unavailable: {error}")
        recommendation_result = {}

    # ======================================================
    # TRADE PLANNING ENGINE
    # ======================================================
    try:
        trade_plan = generate_trade_plan(
            history=history,
            technical_score=technical_score,
            symbol=symbol,
        )
        if not isinstance(trade_plan, dict):
            trade_plan = {
                "status": "ERROR",
                "message": "Invalid trade plan result.",
            }
        elif trade_plan.get("status") == "INSUFFICIENT DATA":
            # Preserve the explicit evidence state; never reinterpret it as
            # an executable trade signal.
            trade_plan.setdefault("signal", "INSUFFICIENT DATA")
    except Exception as error:
        st.warning(f"Trade planning engine unavailable: {error}")
        trade_plan = {
            "status": "ERROR",
            "message": str(error),
        }

    # ======================================================
    # INVESTMENT THESIS ENGINE V3
    # ======================================================

    try:
        investment_thesis = generate_investment_thesis(
            data=data,
            investment_score=investment_score,
            technical_score=technical_score,
            fundamental_score=fundamental_score,
            ai_result=ai_result,
            score_breakdown=score_breakdown,
            technical_reasons=technical_reasons,
            fundamental_reasons=fundamental_reasons,
            trade_plan=trade_plan,
        )

        if not isinstance(investment_thesis, dict):
            investment_thesis = {}

    except Exception as error:
        st.warning(f"Investment thesis unavailable: {error}")
        investment_thesis = {}

    # ======================================================
    # SCENARIO ANALYSIS ENGINE V3
    # ======================================================

    try:
        scenario_analysis = generate_scenario_analysis(
            data=data,
            investment_score=investment_score,
            technical_score=technical_score,
            fundamental_score=fundamental_score,
            ai_result=ai_result,
            score_breakdown=score_breakdown,
            trade_plan=trade_plan,
        )

        if not isinstance(scenario_analysis, dict):
            scenario_analysis = {}

    except Exception as error:
        st.warning(f"Scenario analysis unavailable: {error}")
        scenario_analysis = {}

    # ======================================================
    # FUNDAMENTAL VALUATION ENGINE V3
    # ======================================================

    try:
        valuation_analysis = generate_valuation_analysis(
            data=data,
            fundamental_score=fundamental_score,
            investment_score=investment_score,
        )

        if not isinstance(valuation_analysis, dict):
            valuation_analysis = {
                "status": "UNAVAILABLE",
                "message": "Invalid valuation result.",
            }

    except Exception as error:
        st.warning(f"Valuation analysis unavailable: {error}")

        valuation_analysis = {
            "status": "UNAVAILABLE",
            "message": str(error),
        }

    # ======================================================
    # MULTI-METHOD VALUATION ENGINE V4.3
    # ======================================================

    try:
        valuation_v43 = generate_valuation_v43(
            symbol=symbol,
            company_data=data,
        )

        if not isinstance(valuation_v43, dict):
            valuation_v43 = {
                "status": "UNAVAILABLE",
                "message": "Invalid V4.3 valuation result.",
            }

    except Exception as error:
        st.warning(f"Valuation V4.3 unavailable: {error}")

        valuation_v43 = {
            "status": "UNAVAILABLE",
            "message": str(error),
        }

    # ======================================================
    # TABS
    # ======================================================
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Overview",
            "Financials",
            "Technical",
            "AI Analysis",
            "News",
        ]
    )

    # ======================================================
    # TAB 1 : OVERVIEW
    # ======================================================
    with tab1:
        st.subheader("Company Profile")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Company", data.get("company", "N/A"))
            st.metric("Sector", data.get("sector", "N/A"))
            st.metric("Industry", data.get("industry", "N/A"))

        with col2:
            st.metric("Current Price", format_price(data.get("price")))
            st.metric("Market Cap", format_market_cap(data.get("market_cap")))
            st.metric("Currency", data.get("currency", "N/A"))

    # ======================================================
    # TAB 2 : FINANCIALS
    # ======================================================
    with tab2:
        st.subheader("Financial Ratios")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("P/E", data.get("pe", "N/A"))
        with c2:
            st.metric("P/B", data.get("pb", "N/A"))
        with c3:
            st.metric("EPS", data.get("eps", "N/A"))
        with c4:
            st.metric("Beta", data.get("beta", "N/A"))

        st.write("")

        c5, c6, c7, c8 = st.columns(4)
        with c5:
            st.metric("ROE", format_percent(data.get("roe")))
        with c6:
            st.metric("Profit Margin", format_percent(data.get("profit_margin")))
        with c7:
            st.metric(
                "Operating Margin",
                format_percent(data.get("operating_margin")),
            )
        with c8:
            st.metric(
                "Dividend Yield",
                format_dividend_yield(data.get("dividend_yield")),
            )

        st.divider()

        # ==================================================
        # ADVANCED FUNDAMENTALS
        # ==================================================

        st.subheader("Advanced Fundamentals")

        # --------------------------------------------------
        # Profitability & Financial Health
        # --------------------------------------------------

        st.write("### Profitability & Financial Health")

        a1, a2, a3 = st.columns(3)

        with a1:
            st.metric(
                "ROA",
                format_percent(data.get("roa")),
            )

        with a2:
            st.metric(
                "Debt / Equity",
                format_debt_to_equity(data.get("debt_to_equity")),
            )

        with a3:
            st.metric(
                "Current Ratio",
                format_ratio(data.get("current_ratio")),
            )

        st.write("")

        # --------------------------------------------------
        # Growth
        # --------------------------------------------------

        st.write("### Growth")

        g1, g2 = st.columns(2)

        with g1:
            st.metric(
                "Revenue Growth",
                format_percent(data.get("revenue_growth")),
            )

        with g2:
            st.metric(
                "Earnings Growth",
                format_percent(data.get("earnings_growth")),
            )

        st.write("")

        # --------------------------------------------------
        # Balance Sheet
        # --------------------------------------------------

        st.write("### Balance Sheet")

        b1, b2 = st.columns(2)

        with b1:
            st.metric(
                "Total Debt",
                format_large_rupees(data.get("total_debt")),
            )

        with b2:
            st.metric(
                "Total Cash",
                format_large_rupees(data.get("total_cash")),
            )

        st.write("")

        # --------------------------------------------------
        # Cash Flow
        # --------------------------------------------------

        st.write("### Cash Flow")

        cf1, cf2 = st.columns(2)

        with cf1:
            st.metric(
                "Operating Cash Flow",
                format_large_rupees(data.get("operating_cash_flow")),
            )

        with cf2:
            st.metric(
                "Free Cash Flow",
                format_large_rupees(data.get("free_cash_flow")),
            )

    # ======================================================
    # TAB 3 : TECHNICAL ANALYSIS
    # ======================================================
    with tab3:
        st.subheader("Technical Analysis")

        if history is not None and not history.empty:
            try:
                fig = plot_candlestick(history)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as error:
                st.error(f"Unable to display price chart: {error}")

            st.divider()

            try:
                show_technical_summary(history)
            except Exception as error:
                st.error(f"Unable to display technical summary: {error}")
        else:
            st.warning("No historical price data available.")

    # ======================================================
    # TAB 4 : AI ANALYSIS
    # ======================================================
    with tab4:
        st.subheader("AI Investment Analysis")

        recommendation = recommendation_result.get(
            "recommendation",
            "HOLD",
        )

        st.markdown("### Investment Score V2")

        score_col1, score_col2 = st.columns(2)

        with score_col1:
            st.metric(
                "Overall Investment Score",
                f"{investment_score}/100",
            )

        with score_col2:
            st.metric(
                "Recommendation",
                recommendation,
            )

        st.divider()

        st.markdown("### Component Scores")

        component_col1, component_col2 = st.columns(2)
        component_col3, component_col4 = st.columns(2)

        technical_component = score_breakdown.get(
            "Technical",
            technical_score,
        )

        fundamental_component = score_breakdown.get(
            "Fundamental",
            fundamental_score,
        )

        ai_component = score_breakdown.get(
            "AI",
            ai_result.get("score"),
        )

        stability_component = score_breakdown.get(
            "Stability",
            None,
        )

        with component_col1:
            st.metric(
                "Technical",
                (
                    f"{float(technical_component):.0f}/100"
                    if _finite_number(technical_component) is not None
                    else "N/A"
                ),
            )

        with component_col2:
            st.metric(
                "Fundamental",
                (
                    f"{float(fundamental_component):.0f}/100"
                    if _finite_number(fundamental_component) is not None
                    else "N/A"
                ),
            )

        with component_col3:
            st.metric(
                "AI Model",
                (
                    f"{float(ai_component):.0f}/100"
                    if _finite_number(ai_component) is not None
                    else "N/A"
                ),
            )

        with component_col4:
            st.metric(
                "Stability",
                (
                    f"{float(stability_component):.0f}/100"
                    if _finite_number(stability_component) is not None
                    else "N/A"
                ),
            )

        st.divider()

        st.markdown("### Weighted Contributions")

        technical_contribution = score_breakdown.get(
            "Technical Contribution",
            0,
        )

        fundamental_contribution = score_breakdown.get(
            "Fundamental Contribution",
            0,
        )

        ai_contribution = score_breakdown.get(
            "AI Contribution",
            0,
        )

        stability_contribution = score_breakdown.get(
            "Stability Contribution",
            0,
        )

        contribution_col1, contribution_col2 = st.columns(2)
        contribution_col3, contribution_col4 = st.columns(2)

        with contribution_col1:
            st.metric(
                "Technical Weight",
                f"{technical_contribution:.2f} / 35",
            )

        with contribution_col2:
            st.metric(
                "Fundamental Weight",
                f"{fundamental_contribution:.2f} / 40",
            )

        with contribution_col3:
            st.metric(
                "AI Weight",
                f"{ai_contribution:.2f} / 15",
            )

        with contribution_col4:
            st.metric(
                "Stability Weight",
                f"{stability_contribution:.2f} / 10",
            )

        contribution_values = [
            _finite_number(technical_contribution),
            _finite_number(fundamental_contribution),
            _finite_number(ai_contribution),
            _finite_number(stability_contribution),
        ]
        weighted_total = (
            sum(value for value in contribution_values if value is not None)
            if all(value is not None for value in contribution_values)
            else None
        )

        investment_score_display = (
            f"{float(investment_score):.0f}/100"
            if _finite_number(investment_score) is not None
            else "N/A"
        )
        weighted_total_display = (
            f"{weighted_total:.2f}/100"
            if weighted_total is not None
            else "N/A"
        )
        st.caption(
            f"Weighted total: {weighted_total_display} "
            f"-> Investment Score {investment_score_display}"
        )

        stability_reasons = score_breakdown.get(
            "Stability Reasons",
            [],
        )

        if stability_reasons:
            st.markdown("### Stability Assessment")

            for reason in stability_reasons:
                st.write(f"- {reason}")

        st.divider()

        st.subheader("AI Engine Summary")
        confidence = recommendation_result.get("confidence", 0)
        recommendation = recommendation_result.get("recommendation", "INSUFFICIENT DATA")

        # Never manufacture a HOLD when the authoritative recommendation
        # engine reports missing/invalid evidence.
        if investment_score is None or (
            recommendation in (None, "", "HOLD")
            and recommendation_result.get("overall_score") is None
        ):
            recommendation = "INSUFFICIENT DATA"
            confidence = 0

        try:
            technical_for_default = _finite_number(technical_score)
            fundamental_for_default = _finite_number(fundamental_score)
            if technical_for_default is not None and fundamental_for_default is not None:
                default_overall_score = round(
                    (technical_for_default + fundamental_for_default) / 2
                )
            else:
                default_overall_score = None
        except (TypeError, ValueError):
            default_overall_score = None

        overall_score = recommendation_result.get(
            "overall_score", default_overall_score
        )

        overall_score_display = (
            f"{float(overall_score):.0f}/100"
            if _finite_number(overall_score) is not None
            else "N/A"
        )
        confidence_display = (
            f"{float(confidence):.0f}%"
            if _finite_number(confidence) is not None and 0 <= float(confidence) <= 100
            else "N/A"
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            technical_display = format_price(technical_score) if False else (
                f"{float(technical_score):.0f}/100"
                if _finite_number(technical_score) is not None
                else "N/A"
            )
            st.metric("Technical Score", technical_display)
        with c2:
            fundamental_display = (
                f"{float(fundamental_score):.0f}/100"
                if _finite_number(fundamental_score) is not None
                else "N/A"
            )
            st.metric("Fundamental Score", fundamental_display)
        with c3:
            st.metric("Overall Score", overall_score_display)
        with c4:
            st.metric("Confidence", confidence_display)

        st.progress(safe_progress(confidence))

        recommendation_text = str(recommendation).strip().upper()
        if "STRONG BUY" in recommendation_text:
            st.success(f"{recommendation}")
        elif "BUY" in recommendation_text:
            st.success(f"{recommendation}")
        elif "HOLD" in recommendation_text:
            st.warning(recommendation)
        else:
            st.error(f"{recommendation}")

        st.divider()

        st.subheader("Target Price & Trade Plan")

        if trade_plan.get("status") == "OK":
            current_price = trade_plan.get("current_price")
            target_price = trade_plan.get("target_price")
            stop_loss = trade_plan.get("stop_loss")
            upside = trade_plan.get("upside_percent")
            risk_reward = trade_plan.get("risk_reward")
            atr = trade_plan.get("atr")
            support = trade_plan.get("support")
            quote_timestamp = trade_plan.get("quote_timestamp")
            quote_frequency = trade_plan.get("quote_frequency", "unavailable")
            price_source = trade_plan.get("price_source", "Unknown")
            is_tick_live = bool(trade_plan.get("is_tick_live", False))
            resistance = trade_plan.get("resistance")
            trade_signal = trade_plan.get("signal", "N/A")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Current Price", format_price(current_price))
                if quote_timestamp:
                    freshness = "Tick live" if is_tick_live else f"Latest {quote_frequency}"
                    st.caption(f"{freshness} • {price_source} • {quote_timestamp}")
            with c2:
                st.metric("Target Price", format_price(target_price))
            with c3:
                upside_number = _finite_number(upside)
                upside_text = f"{upside_number:.2f}%" if upside_number is not None else "N/A"
                st.metric("Potential Upside", upside_text)

            c4, c5, c6 = st.columns(3)
            with c4:
                st.metric("Stop Loss", format_price(stop_loss))
            with c5:
                rr_number = _finite_number(risk_reward)
                risk_reward_text = f"1 : {rr_number:.2f}" if rr_number is not None else "N/A"
                st.metric("Risk / Reward", risk_reward_text)
            with c6:
                st.metric("ATR", format_price(atr))

            c7, c8 = st.columns(2)
            with c7:
                st.metric("Support", format_price(support))
            with c8:
                st.metric("Resistance", format_price(resistance))

            st.write(f"### Trade Signal: **{trade_signal}**")

            setup_quality = trade_plan.get("setup_quality", "N/A")
            st.write(f"### Setup Quality: **{setup_quality}**")

            trade_note = trade_plan.get("trade_note", "")
            if trade_note:
                st.info(trade_note)

            st.caption(
                "Target, stop-loss, support and resistance levels are rule-based "
                "estimates derived from historical price data, volatility and the "
                "technical score."
            )
        else:
            st.warning(trade_plan.get("message", "Trade planning data unavailable."))

        st.divider()

        st.subheader("AI Model Analysis")
        ai_score = ai_result.get("score")
        ai_recommendation = ai_result.get("recommendation", "INSUFFICIENT DATA")
        risk = ai_result.get("risk", "Unknown")
        ai_reasons = ai_result.get("reasons", [])

        ai_col1, ai_col2, ai_col3 = st.columns(3)
        with ai_col1:
            ai_score_display = (
                f"{float(ai_score):.0f}/100"
                if _finite_number(ai_score) is not None
                else "N/A"
            )
            st.metric("AI Score", ai_score_display)
        with ai_col2:
            st.metric("Risk Level", risk)
        with ai_col3:
            st.metric("AI Verdict", ai_recommendation)

        ai_recommendation_text = str(ai_recommendation).strip().upper()
        if "BUY" in ai_recommendation_text:
            st.success(f"{ai_recommendation}")
        elif "HOLD" in ai_recommendation_text:
            st.warning(f"{ai_recommendation}")
        else:
            st.error(f"{ai_recommendation}")

        st.write("### AI Reasons")
        if ai_reasons:
            for reason in ai_reasons:
                st.write(f"- {reason}")
        else:
            st.info("No AI reasons available.")

        st.divider()

        st.subheader("Technical Reasons")
        if technical_reasons:
            for reason in technical_reasons:
                st.write(f"- {reason}")
        else:
            st.info("No technical reasons available.")

        st.divider()

        st.subheader("Fundamental Reasons")
        if fundamental_reasons:
            for reason in fundamental_reasons:
                st.write(f"- {reason}")
        else:
            st.info("No fundamental reasons available.")

        st.divider()

        st.subheader("Final Recommendation")

        final_col1, final_col2 = st.columns(2)
        with final_col1:
            st.metric("Overall Score", overall_score_display)
        with final_col2:
            st.metric("Investment Verdict", recommendation)

        st.progress(safe_progress(overall_score))

        st.divider()

        # ==================================================
        # INVESTMENT THESIS V3
        # ==================================================

        st.subheader("Investment Thesis V3")

        if investment_thesis:
            thesis_text = investment_thesis.get(
                "thesis",
                "Investment thesis is unavailable.",
            )
            conviction = investment_thesis.get(
                "conviction",
                "N/A",
            )
            strengths = investment_thesis.get("strengths", [])
            concerns = investment_thesis.get("concerns", [])
            catalysts = investment_thesis.get("catalysts", [])
            bull_case = investment_thesis.get("bull_case", "Bull case unavailable.")
            base_case = investment_thesis.get("base_case", "Base case unavailable.")
            bear_case = investment_thesis.get("bear_case", "Bear case unavailable.")

            thesis_col1, thesis_col2 = st.columns(2)
            with thesis_col1:
                st.metric(
                    "Investment Score",
                    investment_score_display,
                )
            with thesis_col2:
                st.metric("Conviction", conviction)

            st.write("### Investment Thesis")
            st.info(thesis_text)

            strength_col, concern_col = st.columns(2)
            with strength_col:
                st.write("### Key Strengths")
                if strengths:
                    for strength in strengths:
                        st.write(f"- {strength}")
                else:
                    st.write("No major strengths identified.")
            with concern_col:
                st.write("### Key Concerns")
                if concerns:
                    for concern in concerns:
                        st.write(f"- {concern}")
                else:
                    st.write("No major concerns identified.")

            st.write("### Potential Catalysts")
            if catalysts:
                for catalyst in catalysts:
                    st.write(f"- {catalyst}")
            else:
                st.write("No major catalysts identified.")

            st.divider()
            st.write("### Scenario Analysis")
            bull_col, base_col, bear_col = st.columns(3)
            with bull_col:
                st.write("#### Bull Case")
                st.success(bull_case)
            with base_col:
                st.write("#### Base Case")
                st.info(base_case)
            with bear_col:
                st.write("#### Bear Case")
                st.warning(bear_case)
        else:
            st.info("Investment Thesis V3 is unavailable.")

        st.divider()

        # ==================================================
        # QUANTITATIVE SCENARIO ANALYSIS V3
        # ==================================================

        st.subheader("Quantitative Scenario Analysis V3")

        if scenario_analysis:
            bull = scenario_analysis.get("bull", {})
            base = scenario_analysis.get("base", {})
            bear = scenario_analysis.get("bear", {})
            long_term_view = scenario_analysis.get("long_term_view", "N/A")
            entry_quality = scenario_analysis.get("entry_quality", "N/A")
            action = scenario_analysis.get("action", "N/A")
            reward_risk = _finite_number(scenario_analysis.get("reward_risk"))

            d1, d2, d3 = st.columns(3)
            with d1:
                st.metric("Long-Term View", long_term_view)
            with d2:
                st.metric("Entry Quality", entry_quality)
            with d3:
                st.metric("Model Action", action)

            st.metric(
                "Reward / Risk",
                f"{reward_risk:.2f} : 1" if reward_risk is not None else "N/A",
            )

            st.divider()

            bull_col, base_col, bear_col = st.columns(3)

            with bull_col:
                st.markdown("### Bull Case")
                bull_price = bull.get("price")
                bull_return = _finite_number(bull.get("return_percent"))
                st.metric("Scenario Price", format_price(bull_price))
                if bull_return is not None:
                    st.metric(
                        "Potential Return",
                        f"+{bull_return:.2f}%" if bull_return >= 0 else f"{bull_return:.2f}%",
                    )
                else:
                    st.metric("Potential Return", "N/A")
                bull_assumptions = bull.get("assumptions", [])
                if bull_assumptions:
                    st.write("**Assumptions**")
                    for assumption in bull_assumptions:
                        st.write(f"- {assumption}")

            with base_col:
                st.markdown("### Base Case")
                base_price = base.get("price")
                base_return = _finite_number(base.get("return_percent"))
                st.metric("Scenario Price", format_price(base_price))
                st.metric(
                    "Potential Return",
                    f"{base_return:.2f}%" if base_return is not None else "N/A",
                )
                base_assumptions = base.get("assumptions", [])
                if base_assumptions:
                    st.write("**Assumptions**")
                    for assumption in base_assumptions:
                        st.write(f"- {assumption}")

            with bear_col:
                st.markdown("### Bear Case")
                bear_price = bear.get("price")
                bear_return = _finite_number(bear.get("return_percent"))
                st.metric("Scenario Price", format_price(bear_price))
                st.metric(
                    "Potential Return",
                    f"{bear_return:.2f}%" if bear_return is not None else "N/A",
                )
                bear_assumptions = bear.get("assumptions", [])
                if bear_assumptions:
                    st.write("**Assumptions**")
                    for assumption in bear_assumptions:
                        st.write(f"- {assumption}")

            st.write("### Scenario Interpretation")
            if reward_risk is not None and reward_risk < 1:
                st.warning(
                    "The current modeled reward is smaller than "
                    "the modeled downside risk. The stock may have "
                    "supportive longer-term characteristics, but the "
                    "current entry setup is not attractive on a "
                    "reward-to-risk basis."
                )
            elif reward_risk is not None and reward_risk >= 1.5:
                st.success(
                    "The current modeled reward-to-risk profile is "
                    "favorable, subject to confirmation from the "
                    "technical and fundamental analysis."
                )
            else:
                st.info(
                    "The current reward-to-risk profile is moderate. "
                    "Additional confirmation may improve conviction."
                )

        else:
            st.info("Quantitative scenario analysis is unavailable.")

        st.divider()

        # ==================================================
        # FUNDAMENTAL VALUATION V3
        # ==================================================

        st.subheader("Fundamental Valuation V3")

        if valuation_analysis.get("status") == "OK":
            current_value = valuation_analysis.get("current_price")
            fair_value = valuation_analysis.get("fair_value")
            bear_value = valuation_analysis.get("bear_value")
            bull_value = valuation_analysis.get("bull_value")
            upside_percent = valuation_analysis.get("upside_percent")
            margin_of_safety = valuation_analysis.get("margin_of_safety")
            v3_quote_timestamp = valuation_analysis.get("quote_timestamp")
            v3_quote_frequency = valuation_analysis.get("quote_frequency", "unavailable")
            v3_price_source = valuation_analysis.get("price_source", "Unknown")
            v3_is_tick_live = bool(valuation_analysis.get("is_tick_live", False))
            trailing_pe = valuation_analysis.get("trailing_pe")
            forward_pe = valuation_analysis.get("forward_pe")
            base_pe = valuation_analysis.get("base_pe")
            fair_pe = valuation_analysis.get("fair_pe")
            valuation_status = valuation_analysis.get("valuation_status", "N/A")
            valuation_conviction = valuation_analysis.get("valuation_conviction", "N/A")
            valuation_reasons = valuation_analysis.get("reasons", [])

            v1, v2, v3 = st.columns(3)
            with v1:
                st.metric("Current Price", format_price(current_value))
            with v2:
                st.metric("Estimated Fair Value", format_price(fair_value))
            with v3:
                upside_number = _finite_number(upside_percent)
                st.metric(
                    "Valuation Upside / Downside",
                    f"{upside_number:+.2f}%" if upside_number is not None else "N/A",
                )

            if v3_quote_timestamp:
                freshness = "Tick live" if v3_is_tick_live else f"Latest {v3_quote_frequency}"
                st.caption(f"Valuation price: {freshness} • {v3_price_source} • {v3_quote_timestamp}")

            s1, s2, s3 = st.columns(3)
            with s1:
                st.metric("Valuation Status", valuation_status)
            with s2:
                st.metric("Valuation Conviction", valuation_conviction)
            with s3:
                mos_number = _finite_number(margin_of_safety)
                st.metric(
                    "Margin of Safety",
                    f"{mos_number:.2f}%" if mos_number is not None else "N/A",
                )

            st.divider()
            st.markdown("### Valuation Range")
            range1, range2, range3 = st.columns(3)
            with range1:
                st.metric("Bear Value", format_price(bear_value))
            with range2:
                st.metric("Base Fair Value", format_price(fair_value))
            with range3:
                st.metric("Bull Value", format_price(bull_value))

            st.markdown("### P/E Valuation")
            pe1, pe2, pe3, pe4 = st.columns(4)
            with pe1:
                st.metric("Trailing P/E", f"{float(trailing_pe):.2f}x" if _finite_number(trailing_pe) is not None and float(trailing_pe) > 0 else "N/A")
            with pe2:
                st.metric("Forward P/E", f"{float(forward_pe):.2f}x" if _finite_number(forward_pe) is not None and float(forward_pe) > 0 else "N/A")
            with pe3:
                st.metric("Base P/E", f"{float(base_pe):.2f}x" if _finite_number(base_pe) is not None and float(base_pe) > 0 else "N/A")
            with pe4:
                st.metric("Model Fair P/E", f"{float(fair_pe):.2f}x" if _finite_number(fair_pe) is not None and float(fair_pe) > 0 else "N/A")

            st.markdown("### Valuation Interpretation")
            if valuation_status == "UNDERVALUED":
                st.success("The earnings-based valuation model indicates meaningful upside relative to the current market price.")
            elif valuation_status == "SLIGHTLY UNDERVALUED":
                st.success("The earnings-based valuation model indicates modest upside relative to the current market price.")
            elif valuation_status == "FAIRLY VALUED":
                st.info("The current market price is close to the model's estimated earnings-based fair value.")
            elif valuation_status == "SLIGHTLY OVERVALUED":
                st.warning("The current market price is moderately above the model's estimated earnings-based fair value.")
            elif valuation_status == "OVERVALUED":
                st.warning("The current market price is materially above the model's estimated earnings-based fair value.")
            else:
                st.info("Valuation status is unavailable.")

            if valuation_reasons:
                st.markdown("### Valuation Factors")
                for reason in valuation_reasons:
                    st.write(f"- {reason}")

            st.caption(
                "Fundamental Valuation V3 is a rule-based earnings "
                "valuation model. It is independent of the technical "
                "target price and should not be interpreted as a "
                "guaranteed future market price."
            )
        else:
            st.info(
                valuation_analysis.get(
                    "message",
                    "Fundamental valuation is unavailable.",
                )
            )

        st.divider()

        # ==================================================
        # MULTI-METHOD VALUATION V4.3
        # ==================================================

        st.subheader("Multi-Method Valuation V4.3")

        if valuation_v43.get("status") == "OK":
            v43_result = valuation_v43.get("valuation", {})
            if not isinstance(v43_result, dict):
                v43_result = {}

            v43_current_price = v43_result.get("current_price")
            v43_fair_value = v43_result.get("composite_fair_value")
            v43_upside = v43_result.get("upside_percent")
            v43_quote_timestamp = v43_result.get("quote_timestamp")
            v43_quote_frequency = v43_result.get("quote_frequency", "unavailable")
            v43_price_source = v43_result.get("price_source", "Unknown")
            v43_is_tick_live = bool(v43_result.get("is_tick_live", False))
            v43_status = v43_result.get("valuation_status", "N/A")
            v43_confidence = v43_result.get("confidence", "N/A")
            v43_confidence_score = v43_result.get("confidence_score")
            v43_agreement = v43_result.get("method_agreement_score")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Price", format_price(v43_current_price))
            with col2:
                st.metric("Composite Fair Value", format_price(v43_fair_value))
            with col3:
                v43_upside_number = _finite_number(v43_upside)
                st.metric(
                    "Valuation Upside / Downside",
                    f"{v43_upside_number:+.2f}%" if v43_upside_number is not None else "N/A",
                )

            if v43_quote_timestamp:
                freshness = "Tick live" if v43_is_tick_live else f"Latest {v43_quote_frequency}"
                st.caption(f"Valuation price: {freshness} • {v43_price_source} • {v43_quote_timestamp}")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Valuation Status", v43_status)
            with col2:
                st.metric("Confidence", v43_confidence)
            with col3:
                confidence_score = _finite_number(v43_confidence_score)
                st.metric("Confidence Score", f"{confidence_score:.1f}/100" if confidence_score is not None else "N/A")

            agreement_number = _finite_number(v43_agreement)
            st.metric("Method Agreement", f"{agreement_number:.1f}%" if agreement_number is not None else "N/A")

            v43_low_value = v43_result.get("low_value")
            v43_high_value = v43_result.get("high_value")
            st.markdown("### Valuation Range")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Low Estimate", format_price(v43_low_value))
            with col2:
                st.metric("Composite Fair Value", format_price(v43_fair_value))
            with col3:
                st.metric("High Estimate", format_price(v43_high_value))

            st.markdown("### Valuation Methods")
            v43_methods = v43_result.get("methods", {})
            if not isinstance(v43_methods, dict):
                v43_methods = {}

            method_labels = {
                "trailing_pe": "Trailing P/E",
                "forward_pe": "Forward P/E",
                "pb": "Price / Book",
                "ev_ebitda": "EV / EBITDA",
                "fcf_yield": "FCF Yield",
            }
            method_rows = []
            for method_key, method_label in method_labels.items():
                method = v43_methods.get(method_key, {})
                if not isinstance(method, dict):
                    continue
                fair_value = _finite_number(method.get("fair_value"))
                upside = _finite_number(method.get("upside_percent"))
                reliability = _finite_number(method.get("reliability"))
                weight = _finite_number(method.get("weight"))
                method_rows.append(
                    {
                        "Method": method_label,
                        "Fair Value": f"₹{fair_value:,.2f}" if fair_value is not None and fair_value > 0 else "N/A",
                        "Upside / Downside": f"{upside:+.2f}%" if upside is not None else "N/A",
                        "Benchmark": method.get("benchmark_label") or "N/A",
                        "Reliability": f"{reliability * 100:.1f}%" if reliability is not None else "N/A",
                        "Weight": f"{weight * 100:.1f}%" if weight is not None else "N/A",
                        "Source": method.get("source") or "N/A",
                    }
                )
            if method_rows:
                st.dataframe(method_rows, use_container_width=True, hide_index=True)
            else:
                st.info("Detailed valuation methods are unavailable.")

            st.markdown("### Peer Relevance")
            peer_relevance = valuation_v43.get("peer_relevance", {})
            if not isinstance(peer_relevance, dict):
                peer_relevance = {}
            peer_score = _finite_number(peer_relevance.get("score_percent"))
            peer_view = peer_relevance.get("relevance_view", peer_relevance.get("view", "UNKNOWN"))
            components = peer_relevance.get("components", {})
            if not isinstance(components, dict):
                components = {}
            classification = components.get("classification", {})
            financial_profile = components.get("financial_profile", {})
            business_model = components.get("business_model", {})
            if not isinstance(classification, dict):
                classification = {}
            if not isinstance(financial_profile, dict):
                financial_profile = {}
            if not isinstance(business_model, dict):
                business_model = {}
            classification_score = _finite_number(classification.get("score_percent"))
            financial_score = _finite_number(financial_profile.get("score_percent"))
            business_score = _finite_number(business_model.get("score_percent"))

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Peer Relevance Score", f"{peer_score:.1f}%" if peer_score is not None else "N/A")
            with col2:
                st.metric("Peer Relevance View", peer_view)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Classification Match", f"{classification_score:.1f}%" if classification_score is not None else "N/A")
            with col2:
                st.metric("Financial Profile", f"{financial_score:.1f}%" if financial_score is not None else "N/A")
            with col3:
                st.metric("Business Model Fit", f"{business_score:.1f}%" if business_score is not None else "N/A")

            business_reason = business_model.get("reason")
            if business_reason:
                st.info(business_reason)

            st.markdown("### Quality Adjustment")
            quality_adjustment = valuation_v43.get("quality_adjustment", {})
            if not isinstance(quality_adjustment, dict):
                quality_adjustment = {}
            quality_percent = _finite_number(quality_adjustment.get("composite_adjustment_percent"))
            quality_view = quality_adjustment.get("quality_view", "UNKNOWN")
            active_weight = _finite_number(quality_adjustment.get("active_weight"))

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Multiple Adjustment", f"{quality_percent:+.2f}%" if quality_percent is not None else "N/A")
            with col2:
                st.metric("Quality View", quality_view)
            with col3:
                st.metric("Active Factor Weight", f"{active_weight * 100:.1f}%" if active_weight is not None else "N/A")

            quality_factors = quality_adjustment.get("factors", {})
            if not isinstance(quality_factors, dict):
                quality_factors = {}
            quality_factor_labels = {
                "roe": "Return on Equity",
                "revenue_growth": "Revenue Growth",
                "earnings_growth": "Earnings Growth",
                "operating_margin": "Operating Margin",
                "debt_to_equity": "Debt / Equity",
            }
            quality_rows = []
            for factor_key, factor_label in quality_factor_labels.items():
                factor = quality_factors.get(factor_key, {})
                if not isinstance(factor, dict):
                    continue
                company_value = _finite_number(factor.get("company_value"))
                peer_median = _finite_number(factor.get("peer_median"))
                adjustment = _finite_number(factor.get("adjustment"))
                observations = factor.get("observations")
                quality_rows.append(
                    {
                        "Factor": factor_label,
                        "Company": f"{company_value:.4f}" if company_value is not None else "N/A",
                        "Peer Median": f"{peer_median:.4f}" if peer_median is not None else "N/A",
                        "Adjustment": f"{adjustment * 100:+.2f}%" if adjustment is not None else "N/A",
                        "Observations": observations if isinstance(observations, int) else "N/A",
                    }
                )
            if quality_rows:
                st.dataframe(quality_rows, use_container_width=True, hide_index=True)

            st.markdown("### Benchmark Transformation")
            raw_benchmarks = valuation_v43.get("raw_peer_benchmarks", {})
            quality_benchmarks = valuation_v43.get("quality_adjusted_benchmarks", {})
            final_benchmarks = valuation_v43.get("final_benchmarks", {})
            if not isinstance(raw_benchmarks, dict):
                raw_benchmarks = {}
            if not isinstance(quality_benchmarks, dict):
                quality_benchmarks = {}
            if not isinstance(final_benchmarks, dict):
                final_benchmarks = {}

            benchmark_labels = {
                "pe": "Trailing P/E",
                "forward_pe": "Forward P/E",
                "pb": "Price / Book",
                "ev_ebitda": "EV / EBITDA",
            }
            benchmark_rows = []
            for benchmark_key, benchmark_label in benchmark_labels.items():
                raw_block = raw_benchmarks.get(benchmark_key, {})
                quality_block = quality_benchmarks.get(benchmark_key, {})
                final_block = final_benchmarks.get(benchmark_key, {})
                if not isinstance(raw_block, dict):
                    raw_block = {}
                if not isinstance(quality_block, dict):
                    quality_block = {}
                if not isinstance(final_block, dict):
                    final_block = {}

                raw_multiple = _finite_number(raw_block.get("multiple"))
                adjusted_multiple = _finite_number(quality_block.get("multiple"))
                quality_percent = _finite_number(quality_block.get("quality_adjustment_percent"))
                initial_reliability = _finite_number(final_block.get("pre_relevance_reliability"))
                relevance_multiplier = _finite_number(final_block.get("peer_relevance_multiplier"))
                final_reliability = _finite_number(final_block.get("reliability"))
                observations = final_block.get("observations")

                benchmark_rows.append(
                    {
                        "Method": benchmark_label,
                        "Raw Peer Median": f"{raw_multiple:.2f}x" if raw_multiple is not None else "N/A",
                        "Quality Adj.": f"{quality_percent:+.2f}%" if quality_percent is not None else "N/A",
                        "Adjusted Multiple": f"{adjusted_multiple:.2f}x" if adjusted_multiple is not None else "N/A",
                        "Initial Reliability": f"{initial_reliability * 100:.1f}%" if initial_reliability is not None else "N/A",
                        "Relevance Multiplier": f"{relevance_multiplier:.2f}x" if relevance_multiplier is not None else "N/A",
                        "Final Reliability": f"{final_reliability * 100:.1f}%" if final_reliability is not None else "N/A",
                        "Observations": observations if isinstance(observations, int) else "N/A",
                    }
                )

            if benchmark_rows:
                st.dataframe(benchmark_rows, use_container_width=True, hide_index=True)
            else:
                st.info("Benchmark transformation data is unavailable.")
        else:
            st.info(
                valuation_v43.get(
                    "message",
                    "Multi-method valuation is unavailable.",
                )
            )

    # ======================================================
    # TAB 5 : NEWS
    # ======================================================
    with tab5:
        st.subheader("Latest Company News")

        if news:
            for item in news:
                if not isinstance(item, dict):
                    continue

                title = item.get("title", "Untitled")
                summary = item.get("summary", "")
                link = item.get("link")

                st.markdown(f"### {title}")

                if summary:
                    st.write(summary)

                if link:
                    st.markdown(f"[Read Full Article]({link})")

                st.divider()
        else:
            st.info("No recent company news available.")

    # ======================================================
    # REPORT GENERATION
    # ======================================================

    st.divider()

    st.subheader("Research Report")

    report_data = {
        "company": data.get("company", symbol),
        "symbol": symbol,
        "price": data.get("price"),
        "market_cap": data.get("market_cap"),
        "technical_score": technical_score,
        "fundamental_score": fundamental_score,
        "investment_score": investment_score,
        "recommendation": recommendation,
        "ai_result": ai_result,
        "investment_thesis": investment_thesis,
        "scenario_analysis": scenario_analysis,
        "valuation_analysis": valuation_analysis,
        "valuation_v43": valuation_v43,
        "trade_plan": trade_plan,
        "news": news,
        "technical_reasons": technical_reasons,
        "fundamental_reasons": fundamental_reasons,
        "score_breakdown": score_breakdown,
    }

    try:
        report_generator = ReportGenerator()
        report_result = report_generator.generate_report(report_data)
    except Exception as error:
        report_result = {
            "status": "ERROR",
            "error": str(error),
        }

    if report_result.get("status") == "OK":
        st.download_button(
            "Download Research Report",
            data=report_result["content"],
            file_name=f"{symbol}_research_report.pdf",
            mime="application/pdf",
        )
    else:
        st.warning(
            report_result.get(
                "error",
                "Research report is currently unavailable.",
            )
        )
