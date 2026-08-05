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

# ==========================================================
# HELPER FUNCTIONS & FORMATTERS
# ==========================================================


def format_market_cap(value):
    """Format market capitalization."""
    if value in [None, "N/A"]:
        return "N/A"

    try:
        value = float(value)

        if value >= 1e12:
            return f"\u20b9{value / 1e12:.2f} Lakh Cr"

        if value >= 1e9:
            return f"\u20b9{value / 1e7:.2f} Cr"

        if value >= 1e6:
            return f"\u20b9{value / 1e5:.2f} Lakh"

        return f"\u20b9{value:,.0f}"

    except (TypeError, ValueError):
        return str(value)


def format_percent(value):
    """Convert decimal values to percentages."""
    if value in [None, "N/A"]:
        return "N/A"

    try:
        return f"{float(value) * 100:.2f}%"

    except (TypeError, ValueError):
        return str(value)


def format_dividend_yield(value):
    """
    Format Yahoo Finance dividendYield.

    Yahoo may return dividendYield as an already-percent
    value, e.g. 0.47 means 0.47%.
    """
    if value in [None, "N/A"]:
        return "N/A"

    try:
        return f"{float(value):.2f}%"

    except (TypeError, ValueError):
        return str(value)


def safe_progress(value):
    """Convert a 0-100 score into a Streamlit progress value."""
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = 0.0

    return max(0.0, min(score / 100.0, 1.0))


def format_price(value):
    """Safely format a price."""
    if value is None:
        return "N/A"

    try:
        return f"\u20b9{float(value):,.2f}"

    except (TypeError, ValueError):
        return "N/A"


def format_ratio(value):
    """
    Format a financial ratio.

    Example:
        1.52 -> 1.52x
    """
    if value in [None, "N/A"]:
        return "N/A"

    try:
        return f"{float(value):.2f}x"

    except (TypeError, ValueError):
        return "N/A"


def format_debt_to_equity(value):
    """
    Format Yahoo Finance debtToEquity.

    Yahoo Finance commonly reports debtToEquity
    on a percentage-style scale.

    Example:
        36.653 -> 0.37x
    """
    if value in [None, "N/A"]:
        return "N/A"

    try:
        ratio = float(value) / 100.0
        return f"{ratio:.2f}x"

    except (TypeError, ValueError):
        return "N/A"


def format_large_rupees(value):
    """
    Format large rupee-denominated financial values.

    Examples:
        3.98e12 -> Rs. 3.98 Lakh Cr
        5.00e10 -> Rs. 5,000.00 Cr
    """
    if value in [None, "N/A"]:
        return "N/A"

    try:
        value = float(value)

        if value >= 1e12:
            return f"Rs. {value / 1e12:.2f} Lakh Cr"

        if value >= 1e7:
            return f"Rs. {value / 1e7:,.2f} Cr"

        if value >= 1e5:
            return f"Rs. {value / 1e5:,.2f} Lakh"

        return f"Rs. {value:,.2f}"

    except (TypeError, ValueError):
        return "N/A"


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
            technical_score = 0
            technical_reasons = ["Historical price data unavailable."]
    except Exception as error:
        technical_score = 0
        technical_reasons = [f"Technical scoring unavailable: {error}"]

    # ======================================================
    # FUNDAMENTAL SCORE V2
    # ======================================================
    try:
        fundamental_score, fundamental_reasons = calculate_fundamental_score(data)
    except Exception as error:
        fundamental_score = 0
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
        investment_score = 0
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
            history=history, technical_score=technical_score
        )
        if not isinstance(trade_plan, dict):
            trade_plan = {
                "status": "ERROR",
                "message": "Invalid trade plan result.",
            }
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

        # ==================================================
        # INVESTMENT SCORE V2
        # ==================================================

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

        # ==================================================
        # COMPONENT SCORES
        # ==================================================

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
            ai_result.get("score", 0),
        )

        stability_component = score_breakdown.get(
            "Stability",
            0,
        )

        with component_col1:
            st.metric(
                "Technical",
                f"{technical_component:.0f}/100",
            )

        with component_col2:
            st.metric(
                "Fundamental",
                f"{fundamental_component:.0f}/100",
            )

        with component_col3:
            st.metric(
                "AI Model",
                f"{ai_component:.0f}/100",
            )

        with component_col4:
            st.metric(
                "Stability",
                f"{stability_component:.0f}/100",
            )

        st.divider()

        # ==================================================
        # WEIGHTED CONTRIBUTIONS
        # ==================================================

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

        weighted_total = (
            technical_contribution
            + fundamental_contribution
            + ai_contribution
            + stability_contribution
        )

        st.caption(
            f"Weighted total: {weighted_total:.2f}/100 "
            f"-> Investment Score {investment_score}/100"
        )

        # ==================================================
        # STABILITY ASSESSMENT
        # ==================================================

        stability_reasons = score_breakdown.get(
            "Stability Reasons",
            [],
        )

        if stability_reasons:
            st.markdown("### Stability Assessment")

            for reason in stability_reasons:
                st.write(f"- {reason}")

        st.divider()

        # AI Engine Summary
        st.subheader("AI Engine Summary")
        confidence = recommendation_result.get("confidence", 0)
        recommendation = recommendation_result.get("recommendation", "HOLD")

        try:
            default_overall_score = round(
                (float(technical_score) + float(fundamental_score)) / 2
            )
        except (TypeError, ValueError):
            default_overall_score = 0

        overall_score = recommendation_result.get(
            "overall_score", default_overall_score
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Technical Score", f"{technical_score}/100")
        with c2:
            st.metric("Fundamental Score", f"{fundamental_score}/100")
        with c3:
            st.metric("Overall Score", f"{overall_score}/100")
        with c4:
            st.metric("Confidence", f"{confidence}%")

        st.progress(safe_progress(confidence))

        # Recommendation Badge
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

        # Target Price & Trade Plan
        st.subheader("Target Price & Trade Plan")

        if trade_plan.get("status") == "OK":
            current_price = trade_plan.get("current_price")
            target_price = trade_plan.get("target_price")
            stop_loss = trade_plan.get("stop_loss")
            upside = trade_plan.get("upside_percent")
            risk_reward = trade_plan.get("risk_reward")
            atr = trade_plan.get("atr")
            support = trade_plan.get("support")
            resistance = trade_plan.get("resistance")
            trade_signal = trade_plan.get("signal", "N/A")

            # Row 1
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Current Price", format_price(current_price))
            with c2:
                st.metric("Target Price", format_price(target_price))
            with c3:
                if upside is not None:
                    try:
                        upside_text = f"{float(upside):.2f}%"
                    except (TypeError, ValueError):
                        upside_text = "N/A"
                else:
                    upside_text = "N/A"
                st.metric("Potential Upside", upside_text)

            # Row 2
            c4, c5, c6 = st.columns(3)
            with c4:
                st.metric("Stop Loss", format_price(stop_loss))
            with c5:
                if risk_reward is not None:
                    try:
                        risk_reward_text = f"1 : {float(risk_reward):.2f}"
                    except (TypeError, ValueError):
                        risk_reward_text = "N/A"
                else:
                    risk_reward_text = "N/A"
                st.metric("Risk / Reward", risk_reward_text)
            with c6:
                st.metric("ATR", format_price(atr))

            # Row 3
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

        # Existing AI Model
        st.subheader("AI Model Analysis")
        ai_score = ai_result.get("score", 0)
        ai_recommendation = ai_result.get("recommendation", "HOLD")
        risk = ai_result.get("risk", "Unknown")
        ai_reasons = ai_result.get("reasons", [])

        ai_col1, ai_col2, ai_col3 = st.columns(3)
        with ai_col1:
            st.metric("AI Score", f"{ai_score}/100")
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

        # Technical Reasons
        st.subheader("Technical Reasons")
        if technical_reasons:
            for reason in technical_reasons:
                st.write(f"- {reason}")
        else:
            st.info("No technical reasons available.")

        st.divider()

        # Fundamental Reasons
        st.subheader("Fundamental Reasons")
        if fundamental_reasons:
            for reason in fundamental_reasons:
                st.write(f"- {reason}")
        else:
            st.info("No fundamental reasons available.")

        st.divider()

        # Final Recommendation
        st.subheader("Final Recommendation")
        final_col1, final_col2 = st.columns(2)
        with final_col1:
            st.metric("Overall Score", f"{overall_score}/100")
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

            strengths = investment_thesis.get(
                "strengths",
                [],
            )

            concerns = investment_thesis.get(
                "concerns",
                [],
            )

            catalysts = investment_thesis.get(
                "catalysts",
                [],
            )

            bull_case = investment_thesis.get(
                "bull_case",
                "Bull case unavailable.",
            )

            base_case = investment_thesis.get(
                "base_case",
                "Base case unavailable.",
            )

            bear_case = investment_thesis.get(
                "bear_case",
                "Bear case unavailable.",
            )

            # ----------------------------------------------
            # CONVICTION
            # ----------------------------------------------

            thesis_col1, thesis_col2 = st.columns(2)

            with thesis_col1:
                st.metric(
                    "Investment Score",
                    f"{investment_score}/100",
                )

            with thesis_col2:
                st.metric(
                    "Conviction",
                    conviction,
                )

            st.write("### Investment Thesis")

            st.info(thesis_text)

            # ----------------------------------------------
            # STRENGTHS & CONCERNS
            # ----------------------------------------------

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

            # ----------------------------------------------
            # CATALYSTS
            # ----------------------------------------------

            st.write("### Potential Catalysts")

            if catalysts:
                for catalyst in catalysts:
                    st.write(f"- {catalyst}")
            else:
                st.write("No major catalysts identified.")

            st.divider()

            # ----------------------------------------------
            # BULL / BASE / BEAR CASE
            # ----------------------------------------------

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

            long_term_view = scenario_analysis.get(
                "long_term_view",
                "N/A",
            )

            entry_quality = scenario_analysis.get(
                "entry_quality",
                "N/A",
            )

            action = scenario_analysis.get(
                "action",
                "N/A",
            )

            reward_risk = scenario_analysis.get("reward_risk")

            # ----------------------------------------------
            # DECISION SUMMARY
            # ----------------------------------------------

            d1, d2, d3 = st.columns(3)

            with d1:
                st.metric(
                    "Long-Term View",
                    long_term_view,
                )

            with d2:
                st.metric(
                    "Entry Quality",
                    entry_quality,
                )

            with d3:
                st.metric(
                    "Model Action",
                    action,
                )

            if reward_risk is not None:
                st.metric(
                    "Reward / Risk",
                    f"{reward_risk:.2f} : 1",
                )
            else:
                st.metric(
                    "Reward / Risk",
                    "N/A",
                )

            st.divider()

            # ----------------------------------------------
            # SCENARIO CARDS
            # ----------------------------------------------

            bull_col, base_col, bear_col = st.columns(3)

            # BULL CASE
            with bull_col:
                st.markdown("### Bull Case")

                bull_price = bull.get("price")
                bull_return = bull.get("return_percent")

                st.metric(
                    "Scenario Price",
                    format_price(bull_price),
                )

                if bull_return is not None:
                    st.metric(
                        "Potential Return",
                        (
                            f"+{bull_return:.2f}%"
                            if bull_return >= 0
                            else f"{bull_return:.2f}%"
                        ),
                    )
                else:
                    st.metric(
                        "Potential Return",
                        "N/A",
                    )

                bull_assumptions = bull.get(
                    "assumptions",
                    [],
                )

                if bull_assumptions:
                    st.write("**Assumptions**")

                    for assumption in bull_assumptions:
                        st.write(f"- {assumption}")

            # BASE CASE
            with base_col:
                st.markdown("### Base Case")

                base_price = base.get("price")
                base_return = base.get("return_percent")

                st.metric(
                    "Scenario Price",
                    format_price(base_price),
                )

                if base_return is not None:
                    st.metric(
                        "Potential Return",
                        f"{base_return:.2f}%",
                    )
                else:
                    st.metric(
                        "Potential Return",
                        "N/A",
                    )

                base_assumptions = base.get(
                    "assumptions",
                    [],
                )

                if base_assumptions:
                    st.write("**Assumptions**")

                    for assumption in base_assumptions:
                        st.write(f"- {assumption}")

            # BEAR CASE
            with bear_col:
                st.markdown("### Bear Case")

                bear_price = bear.get("price")
                bear_return = bear.get("return_percent")

                st.metric(
                    "Scenario Price",
                    format_price(bear_price),
                )

                if bear_return is not None:
                    st.metric(
                        "Potential Return",
                        f"{bear_return:.2f}%",
                    )
                else:
                    st.metric(
                        "Potential Return",
                        "N/A",
                    )

                bear_assumptions = bear.get(
                    "assumptions",
                    [],
                )

                if bear_assumptions:
                    st.write("**Assumptions**")

                    for assumption in bear_assumptions:
                        st.write(f"- {assumption}")

            # ----------------------------------------------
            # INTERPRETATION
            # ----------------------------------------------

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
        # QUANTITATIVE SCENARIO ANALYSIS V3
        # ==================================================

        st.subheader("Quantitative Scenario Analysis V3")

        if scenario_analysis:

            bull = scenario_analysis.get("bull", {})
            base = scenario_analysis.get("base", {})
            bear = scenario_analysis.get("bear", {})

            long_term_view = scenario_analysis.get(
                "long_term_view",
                "N/A",
            )

            entry_quality = scenario_analysis.get(
                "entry_quality",
                "N/A",
            )

            action = scenario_analysis.get(
                "action",
                "N/A",
            )

            reward_risk = scenario_analysis.get("reward_risk")

            # ----------------------------------------------
            # DECISION SUMMARY
            # ----------------------------------------------

            d1, d2, d3, d4 = st.columns(4)

            with d1:
                st.metric(
                    "Long-Term View",
                    long_term_view,
                )

            with d2:
                st.metric(
                    "Entry Quality",
                    entry_quality,
                )

            with d3:
                st.metric(
                    "Model Action",
                    action,
                )

            with d4:
                if reward_risk is not None:
                    st.metric(
                        "Reward / Risk",
                        f"{reward_risk:.2f} : 1",
                    )
                else:
                    st.metric(
                        "Reward / Risk",
                        "N/A",
                    )

            st.divider()

            # ----------------------------------------------
            # BULL / BASE / BEAR SCENARIOS
            # ----------------------------------------------

            bull_col, base_col, bear_col = st.columns(3)

            # BULL CASE
            with bull_col:
                st.markdown("### Bull Case")

                bull_price = bull.get("price")
                bull_return = bull.get("return_percent")

                st.metric(
                    "Scenario Price",
                    format_price(bull_price),
                )

                if bull_return is not None:
                    if bull_return >= 0:
                        bull_return_text = f"+{bull_return:.2f}%"
                    else:
                        bull_return_text = f"{bull_return:.2f}%"
                else:
                    bull_return_text = "N/A"

                st.metric(
                    "Potential Return",
                    bull_return_text,
                )

                bull_assumptions = bull.get(
                    "assumptions",
                    [],
                )

                if bull_assumptions:
                    st.write("**Assumptions**")

                    for assumption in bull_assumptions:
                        st.write(f"- {assumption}")

            # BASE CASE
            with base_col:
                st.markdown("### Base Case")

                base_price = base.get("price")
                base_return = base.get("return_percent")

                st.metric(
                    "Scenario Price",
                    format_price(base_price),
                )

                if base_return is not None:
                    base_return_text = f"{base_return:.2f}%"
                else:
                    base_return_text = "N/A"

                st.metric(
                    "Potential Return",
                    base_return_text,
                )

                base_assumptions = base.get(
                    "assumptions",
                    [],
                )

                if base_assumptions:
                    st.write("**Assumptions**")

                    for assumption in base_assumptions:
                        st.write(f"- {assumption}")

            # BEAR CASE
            with bear_col:
                st.markdown("### Bear Case")

                bear_price = bear.get("price")
                bear_return = bear.get("return_percent")

                st.metric(
                    "Scenario Price",
                    format_price(bear_price),
                )

                if bear_return is not None:
                    bear_return_text = f"{bear_return:.2f}%"
                else:
                    bear_return_text = "N/A"

                st.metric(
                    "Potential Return",
                    bear_return_text,
                )

                bear_assumptions = bear.get(
                    "assumptions",
                    [],
                )

                if bear_assumptions:
                    st.write("**Assumptions**")

                    for assumption in bear_assumptions:
                        st.write(f"- {assumption}")

            st.divider()

            # ----------------------------------------------
            # SCENARIO INTERPRETATION
            # ----------------------------------------------

            st.markdown("### Scenario Interpretation")

            if reward_risk is not None and reward_risk < 1:

                st.warning(
                    "The current modeled reward is smaller than "
                    "the modeled downside risk. The company may "
                    "have supportive longer-term characteristics, "
                    "but the current entry setup is unattractive "
                    "on a reward-to-risk basis."
                )

            elif reward_risk is not None and reward_risk >= 1.5:

                st.success(
                    "The current modeled reward-to-risk profile "
                    "is favorable, subject to confirmation from "
                    "the technical and fundamental analysis."
                )

            else:

                st.info(
                    "The current reward-to-risk profile is moderate. "
                    "Additional technical or fundamental confirmation "
                    "may improve conviction."
                )

        else:

            st.info("Quantitative scenario analysis is unavailable.")

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
            reward_risk = scenario_analysis.get("reward_risk")

            # ==============================================
            # DECISION SUMMARY
            # ==============================================

            d1, d2, d3, d4 = st.columns(4)

            with d1:
                st.metric(
                    "Long-Term View",
                    long_term_view,
                )

            with d2:
                st.metric(
                    "Entry Quality",
                    entry_quality,
                )

            with d3:
                st.metric(
                    "Model Action",
                    action,
                )

            with d4:
                if reward_risk is not None:
                    st.metric(
                        "Reward / Risk",
                        f"{reward_risk:.2f} : 1",
                    )
                else:
                    st.metric(
                        "Reward / Risk",
                        "N/A",
                    )

            st.divider()

            # ==============================================
            # BULL / BASE / BEAR
            # ==============================================

            bull_col, base_col, bear_col = st.columns(3)

            # ----------------------------------------------
            # BULL CASE
            # ----------------------------------------------

            with bull_col:
                st.markdown("### Bull Case")

                bull_price = bull.get("price")
                bull_return = bull.get("return_percent")

                st.metric(
                    "Scenario Price",
                    format_price(bull_price),
                )

                if bull_return is not None:
                    bull_return_text = (
                        f"+{bull_return:.2f}%"
                        if bull_return >= 0
                        else f"{bull_return:.2f}%"
                    )
                else:
                    bull_return_text = "N/A"

                st.metric(
                    "Potential Return",
                    bull_return_text,
                )

                bull_assumptions = bull.get("assumptions", [])

                if bull_assumptions:
                    st.write("**Assumptions**")

                    for assumption in bull_assumptions:
                        st.write(f"- {assumption}")

            # ----------------------------------------------
            # BASE CASE
            # ----------------------------------------------

            with base_col:
                st.markdown("### Base Case")

                base_price = base.get("price")
                base_return = base.get("return_percent")

                st.metric(
                    "Scenario Price",
                    format_price(base_price),
                )

                if base_return is not None:
                    base_return_text = f"{base_return:.2f}%"
                else:
                    base_return_text = "N/A"

                st.metric(
                    "Potential Return",
                    base_return_text,
                )

                base_assumptions = base.get("assumptions", [])

                if base_assumptions:
                    st.write("**Assumptions**")

                    for assumption in base_assumptions:
                        st.write(f"- {assumption}")

            # ----------------------------------------------
            # BEAR CASE
            # ----------------------------------------------

            with bear_col:
                st.markdown("### Bear Case")

                bear_price = bear.get("price")
                bear_return = bear.get("return_percent")

                st.metric(
                    "Scenario Price",
                    format_price(bear_price),
                )

                if bear_return is not None:
                    bear_return_text = f"{bear_return:.2f}%"
                else:
                    bear_return_text = "N/A"

                st.metric(
                    "Potential Return",
                    bear_return_text,
                )

                bear_assumptions = bear.get("assumptions", [])

                if bear_assumptions:
                    st.write("**Assumptions**")

                    for assumption in bear_assumptions:
                        st.write(f"- {assumption}")

            st.divider()

            # ==============================================
            # INTERPRETATION
            # ==============================================

            st.markdown("### Scenario Interpretation")

            if reward_risk is not None and reward_risk < 1:
                st.warning(
                    "The current modeled reward is smaller than "
                    "the modeled downside risk. The company may "
                    "have supportive longer-term characteristics, "
                    "but the current entry setup is unattractive "
                    "on a reward-to-risk basis."
                )

            elif reward_risk is not None and reward_risk >= 1.5:
                st.success(
                    "The current modeled reward-to-risk profile "
                    "is favorable, subject to confirmation from "
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

        # PDF Research Report
        st.subheader("Professional Research Report")
        st.caption(
            "Generate a PDF containing company information, financial analysis, "
            "investment scores, target price and trade planning, technical analysis, "
            "fundamental analysis and recent news."
        )

        if st.button(
            "Generate PDF Research Report",
            key=f"generate_research_pdf_{symbol}",
            use_container_width=True,
        ):
            try:
                generator = ReportGenerator()

                pdf_path = generator.generate(
                    symbol=symbol,
                    data=data,
                    investment_score=investment_score,
                    technical_score=technical_score,
                    fundamental_score=fundamental_score,
                    recommendation=recommendation,
                    technical_reasons=technical_reasons,
                    fundamental_reasons=fundamental_reasons,
                    news=news,
                    trade_plan=trade_plan,
                    score_breakdown=score_breakdown,
                    ai_result=ai_result,
                )

                with open(pdf_path, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()

                st.session_state["research_pdf"] = pdf_bytes
                st.session_state["research_pdf_symbol"] = symbol
                st.session_state["research_pdf_name"] = f"{symbol}_Research_Report.pdf"

                st.success("Research report generated successfully.")

            except Exception as error:
                st.error(f"Unable to generate research report: {error}")
            except Exception as error:
                st.error(f"Unable to generate research report: {error}")

        pdf_available = (
            "research_pdf" in st.session_state
            and st.session_state.get("research_pdf_symbol") == symbol
        )

        if pdf_available:
            st.download_button(
                label="Download PDF Research Report",
                data=st.session_state["research_pdf"],
                file_name=st.session_state.get(
                    "research_pdf_name", f"{symbol}_Research_Report.pdf"
                ),
                mime="application/pdf",
                key=f"download_research_pdf_{symbol}",
                use_container_width=True,
            )

    # ======================================================
    # TAB 5 : NEWS
    # ======================================================
    with tab5:
        st.subheader("Latest Company News")

        if not news:
            st.info("No recent news available.")
        else:
            for article in news[:10]:
                if not isinstance(article, dict):
                    continue

                title = article.get("title", "No Title")
                publisher = article.get("publisher", "Unknown")
                link = article.get("link", "")

                st.markdown(f"### {title}")
                st.write(f"**Source:** {publisher}")

                if link:
                    st.link_button("Read Article", link)

                st.divider()
