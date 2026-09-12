import streamlit as st

from charts.candlestick import create_candlestick
from scanner.market_scanner import market_scan
from services.analyzer import analyze_stock
from services.eros_frontend_adapter import EROSFrontendAdapter

# ============================================================
# EROS 3.0 — FRONTEND V2
# INSTITUTIONAL INTELLIGENCE COMMAND CENTER
# ============================================================

st.set_page_config(
    page_title="EROS 3.0 — Institutional Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ADAPTER
# ============================================================

adapter = EROSFrontendAdapter()


# ============================================================
# GLOBAL STYLE
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 18px;
        opacity: 0.75;
        margin-top: 0;
    }

    .section-title {
        font-size: 24px;
        font-weight: 750;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "scan_result" not in st.session_state:
    st.session_state.scan_result = None


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">EROS 3.0</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">' "Institutional Intelligence Command Center" "</div>",
    unsafe_allow_html=True,
)

st.divider()


# ============================================================
# SYSTEM STATUS
# ============================================================

governance = adapter.governance()

status_col, gateway_col, mode_col, execution_col = st.columns(4)

status_col.metric(
    "SYSTEM",
    governance["status"],
)

gateway_col.metric(
    "QUERY GATEWAY",
    f'BLOCK {governance["query_gateway"]["block_id"]}',
)

mode_col.metric(
    "MODE",
    "READ ONLY",
)

execution_col.metric(
    "EXECUTION",
    "BLOCKED",
)


# ============================================================
# COMMAND CENTER
# ============================================================

st.markdown(
    '<div class="section-title">🏠 Command Center</div>',
    unsafe_allow_html=True,
)

st.info(
    "EROS 3.0 is operating through the certified "
    "Block 109 Institutional Application Query Gateway. "
    "The frontend is strictly read-only."
)


# ============================================================
# STOCK INPUT
# ============================================================

st.markdown(
    '<div class="section-title">🔎 Stock Intelligence</div>',
    unsafe_allow_html=True,
)

input_col, button_col = st.columns([5, 1])

with input_col:

    symbol = (
        st.text_input(
            "Stock Symbol",
            value="RELIANCE.NS",
            key="stock_symbol",
        )
        .strip()
        .upper()
    )

with button_col:

    st.write("")

    analyze_clicked = st.button(
        "📊 ANALYZE",
        use_container_width=True,
        type="primary",
    )


# ============================================================
# ANALYSIS
# ============================================================

if analyze_clicked:

    if not symbol:

        st.error("Please enter a stock symbol.")

    else:

        with st.spinner(f"Analyzing {symbol}..."):

            try:

                result = analyze_stock(symbol)

                st.session_state.analysis_result = result

            except Exception as exc:

                st.session_state.analysis_result = None

                st.error(f"Analysis failed: {exc}")


result = st.session_state.analysis_result


# ============================================================
# STOCK RESULT
# ============================================================

if result is not None:

    last = result["last"]
    trend = result["trend"]
    signal = result["signal"]
    breakout = result["breakout"]
    df = result["df"]

    # ========================================================
    # DECISION SNAPSHOT
    # ========================================================

    st.divider()

    st.markdown(
        f'<div class="section-title">' f"📌 {symbol} Decision Snapshot" f"</div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "CURRENT PRICE",
        f'₹{last["Close"]:.2f}',
    )

    c2.metric(
        "TREND",
        str(trend["Trend"]),
    )

    c3.metric(
        "AI SCORE",
        str(signal["Score"]),
    )

    c4.metric(
        "RECOMMENDATION",
        str(signal["Recommendation"]),
    )

    # ========================================================
    # TECHNICAL INTELLIGENCE
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">' "📈 Technical Intelligence" "</div>",
        unsafe_allow_html=True,
    )

    t1, t2, t3, t4, t5, t6 = st.columns(6)

    t1.metric(
        "RSI",
        f'{last["RSI_14"]:.2f}',
    )

    t2.metric(
        "ATR",
        f'{last["ATR"]:.2f}',
    )

    t3.metric(
        "MACD",
        f'{last["MACD"]:.2f}',
    )

    t4.metric(
        "SIGNAL",
        f'{last["Signal"]:.2f}',
    )

    t5.metric(
        "SUPPORT",
        f'₹{last["Support"]:.2f}',
    )

    t6.metric(
        "RESISTANCE",
        f'₹{last["Resistance"]:.2f}',
    )

    # ========================================================
    # PRICE ACTION
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">' "📊 Price Action" "</div>",
        unsafe_allow_html=True,
    )

    try:

        fig = create_candlestick(
            df,
            symbol,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    except Exception as exc:

        st.warning(f"Chart unavailable: {exc}")

    # ========================================================
    # AI SIGNAL ENGINE
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">' "🤖 EROS AI Signal Engine" "</div>",
        unsafe_allow_html=True,
    )

    ai_col, reason_col = st.columns([1, 2])

    with ai_col:

        score = signal["Score"]

        st.metric(
            "AI SCORE",
            score,
        )

        recommendation = signal["Recommendation"]

        if recommendation in (
            "BUY",
            "STRONG BUY",
        ):

            st.success(recommendation)

        elif recommendation in (
            "SELL",
            "STRONG SELL",
        ):

            st.error(recommendation)

        else:

            st.warning(recommendation)

    with reason_col:

        st.write("**Signal Drivers**")

        reasons = signal.get(
            "Reasons",
            [],
        )

        if reasons:

            for reason in reasons:

                st.write(f"✓ {reason}")

        else:

            st.info("No signal explanations returned.")

    # ========================================================
    # RISK / DECISION CONTEXT
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">' "⚠️ Risk & Decision Context" "</div>",
        unsafe_allow_html=True,
    )

    current_price = float(last["Close"])

    support = float(last["Support"])

    resistance = float(last["Resistance"])

    if current_price != 0:

        support_distance = (support - current_price) / current_price * 100

        resistance_distance = (resistance - current_price) / current_price * 100

    else:

        support_distance = 0.0
        resistance_distance = 0.0

    r1, r2, r3, r4 = st.columns(4)

    r1.metric(
        "CURRENT",
        f"₹{current_price:.2f}",
    )

    r2.metric(
        "SUPPORT",
        f"₹{support:.2f}",
        f"{support_distance:.2f}%",
    )

    r3.metric(
        "RESISTANCE",
        f"₹{resistance:.2f}",
        f"{resistance_distance:.2f}%",
    )

    r4.metric(
        "ATR",
        f'{last["ATR"]:.2f}',
    )

    st.caption("Distance values are contextual market indicators, " "not guaranteed price targets.")

    # ========================================================
    # BREAKOUT ENGINE
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">' "🚀 Breakout Engine" "</div>",
        unsafe_allow_html=True,
    )

    breakout_signal = breakout.get(
        "Signal",
        "UNKNOWN",
    )

    breakout_reason = breakout.get(
        "Reason",
        "",
    )

    if breakout_signal == "BUY":

        st.success(f"BREAKOUT SIGNAL: {breakout_signal}")

    elif breakout_signal == "SELL":

        st.error(f"BREAKOUT SIGNAL: {breakout_signal}")

    else:

        st.info(f"BREAKOUT SIGNAL: {breakout_signal}")

    st.write(breakout_reason)

    # ========================================================
    # RAW MARKET DATA
    # ========================================================

    with st.expander("📄 Latest Market Data"):

        st.dataframe(
            df.tail(20),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# MARKET PULSE
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">' "🔎 Market Pulse" "</div>",
    unsafe_allow_html=True,
)

scan_col, filter_col = st.columns([3, 1])

with filter_col:

    buy_only = st.checkbox(
        "BUY Only",
        value=False,
    )

with scan_col:

    scan_clicked = st.button(
        "🔍 SCAN NIFTY MARKET",
        use_container_width=True,
    )


if scan_clicked:

    with st.spinner("Scanning NIFTY stocks..."):

        try:

            scan = market_scan()

            if scan is not None and not scan.empty:

                scan = scan.sort_values(
                    "Score",
                    ascending=False,
                )

                if buy_only:

                    scan = scan[scan["Signal"] == "BUY"]

                st.session_state.scan_result = scan

            else:

                st.session_state.scan_result = None

                st.warning("No stocks found.")

        except Exception as exc:

            st.session_state.scan_result = None

            st.error(f"Market scan failed: {exc}")


scan = st.session_state.scan_result


if scan is not None and not scan.empty:

    st.dataframe(
        scan,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info("Run the market scanner to populate the NIFTY market pulse.")


# ============================================================
# GOVERNANCE
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">' "🔐 EROS Governance" "</div>",
    unsafe_allow_html=True,
)

governance = adapter.governance()

g1, g2 = st.columns(2)

with g1:

    st.write("**Operating Mode**")

    st.success("READ ONLY")

    st.write("**Execution**")

    st.error("BLOCKED")

    st.write("**Broker**")

    st.error("BLOCKED")

    st.write("**Orders**")

    st.error("BLOCKED")

with g2:

    safety = governance["safety"]

    safety_rows = {
        "Read Only": safety["read_only"],
        "Order Creation": safety["allow_order_creation"],
        "Broker Submission": safety["allow_broker_submission"],
        "Live Execution": safety["allow_live_execution"],
        "Portfolio Mutation": safety["allow_portfolio_mutation"],
        "Valuation Mutation": safety["allow_valuation_mutation"],
        "Performance Mutation": safety["allow_performance_mutation"],
        "Risk Mutation": safety["allow_risk_mutation"],
        "Optimization": safety["allow_optimization"],
        "Execution Blocked": safety["execution_blocked"],
        "Non-Mutation Invariant": safety["non_mutation_invariant"],
    }

    for label, value in safety_rows.items():

        if value is True:

            st.write(f"**{label}** : `TRUE`")

        else:

            st.write(f"**{label}** : `FALSE`")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "EROS 3.0 • Institutional Intelligence Command Center • "
    "Block 109 • Read Only • Execution Blocked"
)
