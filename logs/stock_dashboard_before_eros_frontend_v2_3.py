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
# V2.2 — MARKET INTELLIGENCE HELPERS
# ============================================================


def _market_pulse_summary(scan):
    """
    Presentation-only summary of the existing market scanner.

    No scanner logic is changed.
    No database write is performed.
    """

    if scan is None or scan.empty:
        return {
            "total": 0,
            "buy": 0,
            "hold": 0,
            "sell": 0,
        }

    signal_column = None

    for candidate in (
        "Signal",
        "Recommendation",
        "signal",
    ):
        if candidate in scan.columns:
            signal_column = candidate
            break

    if signal_column is None:
        return {
            "total": len(scan),
            "buy": 0,
            "hold": 0,
            "sell": 0,
        }

    values = scan[signal_column].astype(str).str.upper()

    return {
        "total": len(scan),
        "buy": int(values.isin(["BUY", "STRONG BUY"]).sum()),
        "hold": int(values.isin(["HOLD", "NEUTRAL"]).sum()),
        "sell": int(values.isin(["SELL", "STRONG SELL"]).sum()),
    }


def _market_pulse_table(scan, buy_only=False):

    if scan is None or scan.empty:
        return scan

    result = scan.copy()

    if "Score" in result.columns:
        result = result.sort_values(
            "Score",
            ascending=False,
        )

    if buy_only and "Signal" in result.columns:

        result = result[result["Signal"].astype(str).str.upper().isin(["BUY", "STRONG BUY"])]

    return result


# ============================================================
# V2.1 — AI DECISION INTELLIGENCE HELPERS
# ============================================================


def _decision_bar(value):
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0

    numeric = max(0.0, min(100.0, numeric))

    return (
        '<div style="'
        "background:rgba(128,128,128,0.18);"
        "border-radius:8px;"
        "height:9px;"
        "width:100%;"
        '">'
        '<div style="'
        "background:currentColor;"
        "border-radius:8px;"
        "height:9px;"
        f"width:{numeric:.0f}%;"
        '"></div>'
        "</div>"
    )


def _decision_score(signal):
    try:
        value = float(signal.get("Score", 0))
    except (TypeError, ValueError):
        value = 0.0

    return max(0.0, min(100.0, value))


def _technical_context(last, trend):

    rsi = float(last.get("RSI_14", 50))
    macd = float(last.get("MACD", 0))
    macd_signal = float(last.get("Signal", 0))
    close = float(last.get("Close", 0))
    support = float(last.get("Support", close))
    resistance = float(last.get("Resistance", close))

    trend_name = str(trend.get("Trend", "UNKNOWN"))

    if rsi < 30:
        rsi_label = "OVERSOLD"
        rsi_strength = 90
    elif rsi > 70:
        rsi_label = "OVERBOUGHT"
        rsi_strength = 90
    else:
        rsi_label = "NEUTRAL"
        rsi_strength = 50

    if macd > macd_signal:
        macd_label = "BULLISH"
        macd_strength = 80
    elif macd < macd_signal:
        macd_label = "BEARISH"
        macd_strength = 30
    else:
        macd_label = "NEUTRAL"
        macd_strength = 50

    trend_upper = trend_name.upper()

    if "BULL" in trend_upper:
        trend_strength = 90
    elif "BEAR" in trend_upper:
        trend_strength = 20
    else:
        trend_strength = 50

    if close != 0:
        support_distance = ((support - close) / close) * 100
        resistance_distance = ((resistance - close) / close) * 100
    else:
        support_distance = 0.0
        resistance_distance = 0.0

    return {
        "rsi": rsi,
        "rsi_label": rsi_label,
        "rsi_strength": rsi_strength,
        "macd": macd,
        "macd_signal": macd_signal,
        "macd_label": macd_label,
        "macd_strength": macd_strength,
        "trend_label": trend_name,
        "trend_strength": trend_strength,
        "close": close,
        "support": support,
        "resistance": resistance,
        "support_distance": support_distance,
        "resistance_distance": resistance_distance,
    }


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
    # V2.1 AI DECISION INTELLIGENCE
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">' "🧠 EROS AI Decision Intelligence" "</div>",
        unsafe_allow_html=True,
    )

    context = _technical_context(last, trend)
    score = _decision_score(signal)

    recommendation = str(signal.get("Recommendation", "UNKNOWN"))

    decision_left, decision_right = st.columns([1, 2])

    with decision_left:

        st.metric(
            "AI DECISION SCORE",
            f"{score:.0f}",
        )

        if recommendation in ("STRONG BUY", "BUY"):
            st.success(recommendation)
        elif recommendation in ("STRONG SELL", "SELL"):
            st.error(recommendation)
        else:
            st.warning(recommendation)

    with decision_right:

        st.write("**Signal Decomposition**")

        rows = [
            (
                "TREND",
                context["trend_label"],
                context["trend_strength"],
            ),
            (
                "MACD",
                context["macd_label"],
                context["macd_strength"],
            ),
            (
                "RSI",
                context["rsi_label"],
                context["rsi_strength"],
            ),
        ]

        for label, state, strength in rows:

            c1, c2 = st.columns([1, 2])

            c1.write(f"**{label}**")

            c2.markdown(
                _decision_bar(strength) + f"<small>{state}</small>",
                unsafe_allow_html=True,
            )

    st.write("")
    st.write("**Key Signal Drivers**")

    reasons = signal.get("Reasons", [])

    if reasons:

        reason_columns = st.columns(2)

        for index, reason in enumerate(reasons):

            reason_columns[index % 2].write(f"✓ {reason}")

    else:

        st.info("No signal drivers returned by the analyzer.")

    st.write("")
    st.write("**Market Structure**")

    structure_left, structure_mid, structure_right = st.columns(3)

    structure_left.metric(
        "SUPPORT",
        f'₹{context["support"]:.2f}',
        f'{context["support_distance"]:.2f}%',
    )

    structure_mid.metric(
        "CURRENT",
        f'₹{context["close"]:.2f}',
    )

    structure_right.metric(
        "RESISTANCE",
        f'₹{context["resistance"]:.2f}',
        f'{context["resistance_distance"]:.2f}%',
    )

    if abs(context["resistance_distance"]) < 2:

        st.warning("Market context: price is close to " "the identified resistance level.")

    elif abs(context["support_distance"]) < 2:

        st.info("Market context: price is close to " "the identified support level.")

    else:

        st.info(
            "Market context: price is operating "
            "away from the immediate support and "
            "resistance levels."
        )

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
# V2.2 — NIFTY MARKET INTELLIGENCE
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">' "🔎 NIFTY Market Intelligence" "</div>",
    unsafe_allow_html=True,
)

st.caption("Read-only market intelligence generated from the existing " "NIFTY scanner.")

scan_col, filter_col = st.columns([3, 1])

with filter_col:

    buy_only = st.checkbox(
        "BUY signals only",
        value=False,
        key="v22_buy_only",
    )

with scan_col:

    scan_clicked = st.button(
        "🔍 RUN NIFTY MARKET SCANNER",
        use_container_width=True,
        type="primary",
        key="v22_scan_market",
    )


if scan_clicked:

    with st.spinner("Scanning NIFTY stocks..."):

        try:

            raw_scan = market_scan()

            if raw_scan is not None and not raw_scan.empty:

                scan = raw_scan.copy()

                if "Score" in scan.columns:

                    scan = scan.sort_values(
                        "Score",
                        ascending=False,
                    )

                st.session_state.scan_result = scan

            else:

                st.session_state.scan_result = None

                st.warning("No stocks found.")

        except Exception as exc:

            st.session_state.scan_result = None

            st.error(f"Market scan failed: {exc}")


scan = st.session_state.scan_result


if scan is not None and not scan.empty:

    # ========================================================
    # MARKET BREADTH
    # ========================================================

    signal_column = None

    for candidate in (
        "Signal",
        "Recommendation",
        "signal",
    ):

        if candidate in scan.columns:

            signal_column = candidate
            break

    total_count = len(scan)
    buy_count = 0
    hold_count = 0
    sell_count = 0

    if signal_column is not None:

        signal_values = scan[signal_column].astype(str).str.upper()

        buy_count = int(
            signal_values.isin(
                [
                    "BUY",
                    "STRONG BUY",
                ]
            ).sum()
        )

        hold_count = int(
            signal_values.isin(
                [
                    "HOLD",
                    "NEUTRAL",
                ]
            ).sum()
        )

        sell_count = int(
            signal_values.isin(
                [
                    "SELL",
                    "STRONG SELL",
                ]
            ).sum()
        )

    st.subheader("Market Breadth")

    b1, b2, b3, b4 = st.columns(4)

    b1.metric(
        "SCANNED",
        total_count,
    )

    b2.metric(
        "BUY",
        buy_count,
    )

    b3.metric(
        "HOLD",
        hold_count,
    )

    b4.metric(
        "SELL",
        sell_count,
    )

    # ========================================================
    # FILTER
    # ========================================================

    display_scan = scan.copy()

    if buy_only and signal_column is not None:

        display_scan = display_scan[
            display_scan[signal_column]
            .astype(str)
            .str.upper()
            .isin(
                [
                    "BUY",
                    "STRONG BUY",
                ]
            )
        ]

    # ========================================================
    # TOP SIGNALS
    # ========================================================

    st.subheader("Top AI Signals")

    if display_scan.empty:

        st.info("No stocks match the selected filter.")

    else:

        st.dataframe(
            display_scan,
            use_container_width=True,
            hide_index=True,
        )

else:

    st.info("Run the NIFTY market scanner to populate " "Market Intelligence.")


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
