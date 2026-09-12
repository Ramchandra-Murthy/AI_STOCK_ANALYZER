from __future__ import annotations

import streamlit as st

from charts.candlestick import create_candlestick
from portfolio.portfolio import (
    load_portfolio,
)
from services.eros_frontend_adapter import (
    EROSFrontendAdapter,
)

# ============================================================
# EROS 3.0 - FRONTEND V1
# ============================================================

st.set_page_config(
    page_title="EROS 3.0",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ADAPTER
# ============================================================

adapter = EROSFrontendAdapter()


# ============================================================
# SESSION STATE
# ============================================================

if "eros_analysis" not in st.session_state:
    st.session_state.eros_analysis = None

if "eros_scan" not in st.session_state:
    st.session_state.eros_scan = None

if "eros_symbol" not in st.session_state:
    st.session_state.eros_symbol = "RELIANCE.NS"


# ============================================================
# EROS VISUAL STYLE
# ============================================================

st.markdown(
    """
    <style>

    .eros-title {
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0;
    }

    .eros-subtitle {
        font-size: 1.05rem;
        opacity: 0.75;
        margin-top: 0;
    }

    .eros-status {
        padding: 14px 18px;
        border-radius: 10px;
        border: 1px solid rgba(128,128,128,0.30);
        text-align: center;
        min-height: 95px;
    }

    .eros-status-title {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        opacity: 0.65;
    }

    .eros-status-value {
        font-size: 1.35rem;
        font-weight: 800;
        margin-top: 8px;
    }

    .eros-section {
        font-size: 1.45rem;
        font-weight: 750;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }

    .eros-governance {
        padding: 14px;
        border-radius: 10px;
        border: 1px solid rgba(128,128,128,0.30);
        margin-bottom: 8px;
    }

    .eros-small {
        font-size: 0.82rem;
        opacity: 0.65;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================


def status_card(
    title: str,
    value: str,
) -> None:

    st.markdown(
        f"""
        <div class="eros-status">
            <div class="eros-status-title">
                {title}
            </div>
            <div class="eros-status-value">
                {value}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def governance_policy():
    return adapter.governance()["safety"]


def render_governance_summary():
    safety = governance_policy()

    st.markdown(
        '<div class="eros-section">🔐 EROS Governance</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        status_card(
            "Operating Mode",
            "READ ONLY",
        )

    with c2:
        status_card(
            "Execution",
            "BLOCKED",
        )

    with c3:
        status_card(
            "Broker",
            "BLOCKED",
        )

    with c4:
        status_card(
            "Orders",
            "BLOCKED",
        )

    st.markdown("")

    rows = [
        ("read_only", "Read Only"),
        (
            "allow_order_creation",
            "Order Creation",
        ),
        (
            "allow_broker_submission",
            "Broker Submission",
        ),
        (
            "allow_live_execution",
            "Live Execution",
        ),
        (
            "allow_portfolio_mutation",
            "Portfolio Mutation",
        ),
        (
            "allow_valuation_mutation",
            "Valuation Mutation",
        ),
        (
            "allow_performance_mutation",
            "Performance Mutation",
        ),
        (
            "allow_risk_mutation",
            "Risk Mutation",
        ),
        (
            "allow_optimization",
            "Optimization",
        ),
        (
            "execution_blocked",
            "Execution Blocked",
        ),
        (
            "non_mutation_invariant",
            "Non-Mutation Invariant",
        ),
    ]

    for key, label in rows:

        value = safety.get(key)

        if value is True:
            display = "TRUE"
        else:
            display = "FALSE"

        st.markdown(
            f"""
            <div class="eros-governance">
                <b>{label}</b>
                <span style="float:right;">
                    {display}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_header():

    st.markdown(
        '<div class="eros-title">EROS 3.0</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="eros-subtitle">
            Institutional Intelligence Command Center
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    governance = adapter.governance()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        status_card(
            "System",
            governance["status"],
        )

    with c2:
        status_card(
            "Query Gateway",
            "BLOCK 109",
        )

    with c3:
        status_card(
            "Mode",
            "READ ONLY",
        )

    with c4:
        status_card(
            "Execution",
            "BLOCKED",
        )

    st.divider()


def render_stock_metrics(result):

    last = result["last"]
    trend = result["trend"]
    signal = result["signal"]

    st.markdown(
        '<div class="eros-section">📊 Market Snapshot</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Current Price",
            f"₹{last['Close']:.2f}",
        )

    with c2:

        st.metric(
            "Trend",
            trend["Trend"],
        )

    with c3:

        st.metric(
            "Recommendation",
            signal["Recommendation"],
        )

    with c4:

        st.metric(
            "AI Score",
            signal["Score"],
        )


def render_technical_section(result):

    last = result["last"]

    st.markdown(
        '<div class="eros-section">📈 Technical Intelligence</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric(
        "RSI",
        f"{last['RSI_14']:.2f}",
    )

    c2.metric(
        "ATR",
        f"{last['ATR']:.2f}",
    )

    c3.metric(
        "MACD",
        f"{last['MACD']:.2f}",
    )

    c4.metric(
        "Signal",
        f"{last['Signal']:.2f}",
    )

    c5.metric(
        "Support",
        f"{last['Support']:.2f}",
    )

    c6.metric(
        "Resistance",
        f"{last['Resistance']:.2f}",
    )


def render_ai_section(result):

    signal = result["signal"]

    st.markdown(
        '<div class="eros-section">🧠 AI Signal Engine</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    with c1:

        st.metric(
            "AI Score",
            signal["Score"],
        )

    with c2:

        recommendation = signal["Recommendation"]

        if recommendation == "BUY":
            st.success(f"AI Recommendation: {recommendation}")

        elif recommendation == "SELL":
            st.error(f"AI Recommendation: {recommendation}")

        else:
            st.warning(f"AI Recommendation: {recommendation}")

    st.markdown("#### AI Reasons")

    reasons = signal.get(
        "Reasons",
        [],
    )

    if reasons:

        for reason in reasons:

            st.write(f"✓ {reason}")

    else:

        st.info("No AI reasoning returned.")


def render_breakout(result):

    breakout = result["breakout"]

    st.markdown(
        '<div class="eros-section">🚀 Breakout Intelligence</div>',
        unsafe_allow_html=True,
    )

    signal = breakout.get(
        "Signal",
        "UNKNOWN",
    )

    reason = breakout.get(
        "Reason",
        "",
    )

    if signal == "BUY":

        st.success(f"Breakout Signal: {signal}")

    elif signal == "SELL":

        st.error(f"Breakout Signal: {signal}")

    else:

        st.info(f"Breakout Signal: {signal}")

    if reason:
        st.write(reason)


def render_chart(result, symbol):

    st.markdown(
        '<div class="eros-section">📈 Technical Chart</div>',
        unsafe_allow_html=True,
    )

    fig = create_candlestick(
        result["df"],
        symbol,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


def render_market_data(result):

    st.markdown(
        '<div class="eros-section">📄 Market Evidence</div>',
        unsafe_allow_html=True,
    )

    st.dataframe(
        result["df"].tail(20),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown("# 🧠 EROS 3.0")

st.sidebar.caption("Institutional Intelligence")

st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Command Center",
        "📊 Market Intelligence",
        "🔎 Stock Scanner",
        "📈 Stock Intelligence",
        "🧠 AI Signal Engine",
        "⚠️ Risk Intelligence",
        "📚 Evidence & Lineage",
        "🔐 Governance",
    ],
)

st.sidebar.divider()

st.sidebar.caption("EROS Safety")

st.sidebar.success("READ ONLY")

st.sidebar.warning("EXECUTION BLOCKED")

st.sidebar.caption("Block 109 Query Gateway")


# ============================================================
# COMMAND CENTER
# ============================================================

if page == "🏠 Command Center":

    render_header()

    st.markdown(
        '<div class="eros-section">🏠 Command Center</div>',
        unsafe_allow_html=True,
    )

    st.write("""
        Welcome to the EROS 3.0 Institutional Intelligence
        Command Center.

        This frontend is connected to the certified EROS
        application query boundary and operates in read-only
        mode.
        """)

    st.divider()

    st.markdown(
        '<div class="eros-section">🔎 Quick Stock Intelligence</div>',
        unsafe_allow_html=True,
    )

    symbol = st.text_input(
        "Stock Symbol",
        st.session_state.eros_symbol,
        key="command_symbol",
    )

    if st.button(
        "Analyze Stock",
        type="primary",
        key="command_analyze",
    ):

        st.session_state.eros_symbol = symbol.upper()

        with st.spinner("Running EROS stock intelligence..."):

            try:

                st.session_state.eros_analysis = adapter.stock_analysis(
                    st.session_state.eros_symbol
                )

            except Exception as exc:

                st.error(f"Analysis failed: {exc}")

    if st.session_state.eros_analysis:

        result = st.session_state.eros_analysis

        render_stock_metrics(result)

        st.divider()

        render_technical_section(result)

    st.divider()

    render_governance_summary()


# ============================================================
# MARKET INTELLIGENCE
# ============================================================

elif page == "📊 Market Intelligence":

    render_header()

    st.markdown(
        '<div class="eros-section">📊 Market Intelligence</div>',
        unsafe_allow_html=True,
    )

    st.write("""
        EROS market intelligence provides read-only access to
        the existing quantitative scanner and analytical engine.
        """)

    if st.button(
        "🔍 Scan Market",
        type="primary",
    ):

        with st.spinner("Scanning market..."):

            try:

                scan = adapter.market_scan()

                if scan is None or scan.empty:

                    st.warning("No market data returned.")

                else:

                    scan = scan.sort_values(
                        "Score",
                        ascending=False,
                    )

                    st.session_state.eros_scan = scan

            except Exception as exc:

                st.error(f"Market scan failed: {exc}")

    if st.session_state.eros_scan is not None:

        scan = st.session_state.eros_scan

        st.dataframe(
            scan,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# STOCK SCANNER
# ============================================================

elif page == "🔎 Stock Scanner":

    render_header()

    st.markdown(
        '<div class="eros-section">🔎 EROS Stock Scanner</div>',
        unsafe_allow_html=True,
    )

    buy_only = st.checkbox(
        "Show BUY signals only",
    )

    if st.button(
        "Run NIFTY Scanner",
        type="primary",
    ):

        with st.spinner("Scanning NIFTY stocks..."):

            try:

                scan = adapter.market_scan()

                if scan is None or scan.empty:

                    st.warning("No stocks found.")

                    st.session_state.eros_scan = None

                else:

                    scan = scan.sort_values(
                        "Score",
                        ascending=False,
                    )

                    if buy_only:

                        scan = scan[scan["Signal"] == "BUY"]

                    st.session_state.eros_scan = scan

            except Exception as exc:

                st.error(f"Scanner failed: {exc}")

    if st.session_state.eros_scan is not None:

        scan = st.session_state.eros_scan

        st.dataframe(
            scan,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# STOCK INTELLIGENCE
# ============================================================

elif page == "📈 Stock Intelligence":

    render_header()

    st.markdown(
        '<div class="eros-section">📈 Stock Intelligence</div>',
        unsafe_allow_html=True,
    )

    symbol = st.text_input(
        "Stock Symbol",
        st.session_state.eros_symbol,
        key="stock_intelligence_symbol",
    )

    if st.button(
        "Analyze",
        type="primary",
        key="stock_intelligence_analyze",
    ):

        st.session_state.eros_symbol = symbol.upper()

        with st.spinner("Analyzing stock..."):

            try:

                st.session_state.eros_analysis = adapter.stock_analysis(
                    st.session_state.eros_symbol
                )

            except Exception as exc:

                st.error(f"Stock analysis failed: {exc}")

    result = st.session_state.eros_analysis

    if result:

        render_stock_metrics(result)

        st.divider()

        render_technical_section(result)

        st.divider()

        render_breakout(result)

        st.divider()

        render_chart(
            result,
            st.session_state.eros_symbol,
        )

        st.divider()

        render_market_data(result)

    else:

        st.info("Enter a stock symbol and click Analyze.")


# ============================================================
# AI SIGNAL ENGINE
# ============================================================

elif page == "🧠 AI Signal Engine":

    render_header()

    st.markdown(
        '<div class="eros-section">🧠 AI Signal Engine</div>',
        unsafe_allow_html=True,
    )

    symbol = st.text_input(
        "Stock Symbol",
        st.session_state.eros_symbol,
        key="ai_symbol",
    )

    if st.button(
        "Run AI Analysis",
        type="primary",
    ):

        st.session_state.eros_symbol = symbol.upper()

        with st.spinner("Running AI signal engine..."):

            try:

                st.session_state.eros_analysis = adapter.stock_analysis(
                    st.session_state.eros_symbol
                )

            except Exception as exc:

                st.error(f"AI analysis failed: {exc}")

    result = st.session_state.eros_analysis

    if result:

        render_ai_section(result)

        st.divider()

        render_breakout(result)

    else:

        st.info("Run an analysis to view the AI signal.")


# ============================================================
# RISK INTELLIGENCE
# ============================================================

elif page == "⚠️ Risk Intelligence":

    render_header()

    st.markdown(
        '<div class="eros-section">⚠️ Risk Intelligence</div>',
        unsafe_allow_html=True,
    )

    st.warning("""
        EROS Risk Intelligence is currently operating as a
        read-only presentation layer.

        No risk mutation, optimization, order generation,
        broker submission, or live execution is permitted.
        """)

    result = st.session_state.eros_analysis

    if result:

        last = result["last"]

        st.markdown("### Current Risk Inputs")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "ATR",
            f"{last['ATR']:.2f}",
        )

        c2.metric(
            "Support",
            f"{last['Support']:.2f}",
        )

        c3.metric(
            "Resistance",
            f"{last['Resistance']:.2f}",
        )

        st.info("Risk analytics are observational only.")

    else:

        st.info("Analyze a stock first to display risk inputs.")

    st.divider()

    render_governance_summary()


# ============================================================
# EVIDENCE & LINEAGE
# ============================================================

elif page == "📚 Evidence & Lineage":

    render_header()

    st.markdown(
        '<div class="eros-section">📚 Evidence & Lineage</div>',
        unsafe_allow_html=True,
    )

    governance = adapter.governance()

    st.markdown("### EROS Application Lineage")

    lineage = [
        {
            "Layer": "Frontend",
            "Status": "CERTIFIED",
            "Mode": "READ ONLY",
        },
        {
            "Layer": "Block 109",
            "Status": "CERTIFIED",
            "Mode": "QUERY",
        },
        {
            "Layer": "Block 108",
            "Status": "CERTIFIED",
            "Mode": "APPLICATION SERVICE",
        },
        {
            "Layer": "Block 107",
            "Status": "CERTIFIED",
            "Mode": "APPLICATION READ",
        },
        {
            "Layer": "Block 106",
            "Status": "CERTIFIED",
            "Mode": "INTEGRATION",
        },
        {
            "Layer": "Block 104",
            "Status": "CERTIFIED",
            "Mode": "COMMAND CENTER",
        },
        {
            "Layer": "Block 103",
            "Status": "CERTIFIED",
            "Mode": "READ MODEL",
        },
        {
            "Layer": "Block 102",
            "Status": "CERTIFIED",
            "Mode": "FRONTEND CONTRACT",
        },
    ]

    st.dataframe(
        lineage,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("### Query Gateway")

    st.json(governance["query_gateway"])

    st.markdown("### Frontend Adapter Snapshot")

    st.json(adapter.snapshot())


# ============================================================
# GOVERNANCE
# ============================================================

elif page == "🔐 Governance":

    render_header()

    render_governance_summary()

    st.divider()

    st.markdown(
        '<div class="eros-section">🔐 Complete Safety Contract</div>',
        unsafe_allow_html=True,
    )

    st.json(adapter.governance()["safety"])

    st.divider()

    st.info("""
        EROS 3.0 is currently configured as a read-only
        institutional intelligence system.

        The frontend does not create orders, submit broker
        requests, execute trades, mutate portfolios, mutate
        valuation, mutate performance, mutate risk, or perform
        optimization.
        """)


# ============================================================
# PORTFOLIO — READ ONLY
# ============================================================

st.sidebar.divider()

if st.sidebar.checkbox(
    "Show Read-Only Portfolio",
    value=False,
):

    st.sidebar.caption("Portfolio display only — mutation disabled.")

    try:

        portfolio = load_portfolio()

        if portfolio.empty:

            st.sidebar.info("Portfolio is empty.")

        else:

            st.sidebar.dataframe(
                portfolio,
                hide_index=True,
            )

    except Exception as exc:

        st.sidebar.warning(f"Portfolio unavailable: {exc}")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "EROS 3.0 • Institutional Intelligence • "
    "Block 109 Query Gateway • Read Only • "
    "Execution Blocked"
)
