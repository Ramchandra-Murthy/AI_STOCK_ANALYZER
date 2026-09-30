"""AI Stock Analyzer Pro - organized Streamlit application entrypoint."""

import streamlit as st

from components.top10_live import show_live_top10_scanner
from modules.backtesting import show as backtesting
from modules.dashboard import show as dashboard
from modules.fundamentals import show as fundamentals
from modules.intraday import show as intraday
from modules.market import show as market
from modules.portfolio import show as portfolio
from modules.prediction import show as prediction
from modules.research import show as research
from modules.scanner import show as scanner
from modules.settings import show as settings


def load_css() -> None:
    """Load the shared application theme."""
    with open("assets/styles.css", encoding="utf-8") as css_file:
        st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)


st.set_page_config(
    page_title="AI Stock Analyzer Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()

pages = {
    "📊 Core": [
        st.Page(dashboard, title="Dashboard", icon="🏠", default=True),
        st.Page(market, title="Market", icon="📈"),
        st.Page(portfolio, title="Portfolio", icon="💼"),
        st.Page(scanner, title="Scanner", icon="🔍"),
    ],
    "🔴 Live Market": [
        st.Page(show_live_top10_scanner, title="Live Top-10 Scanner", icon="📡"),
        st.Page(intraday, title="Intraday Trading", icon="⏱️"),
    ],
    "🔎 Research": [
        st.Page(research, title="Stock Research", icon="🔍"),
        st.Page(fundamentals, title="Fundamentals", icon="📊"),
        st.Page(prediction, title="AI Prediction", icon="🤖"),
        st.Page(backtesting, title="Backtesting", icon="📉"),
    ],
    "🤖 Algorithmic Trading": [
        st.Page("pages/Algorithmic_Scanner.py", title="Algorithmic Scanner", icon="📊"),
        st.Page("pages/Algorithmic_Backtest.py", title="Algorithmic Backtest", icon="📈"),
        st.Page(
            "pages/Algorithmic_Paper_Trading.py",
            title="Algorithmic Paper Trading",
            icon="🧪",
        ),
        st.Page(
            "pages/Algorithmic_Performance.py",
            title="Algorithmic Performance",
            icon="📊",
        ),
        st.Page(
            "pages/Portfolio_Risk_Allocation.py",
            title="Portfolio Risk & Allocation",
            icon="🛡️",
        ),
        st.Page(
            "pages/Day_Trader_Opportunity_Scanner.py",
            title="Day Trader Opportunity Scanner",
            icon="⚡",
        ),
    ],
    "🧠 AI Trading Intelligence": [
        st.Page(
            "pages/AI_Trading_Intelligence.py",
            title="AI Trading Scanner",
            icon="🧠",
        ),
        st.Page(
            "pages/AI_Paper_Trading.py",
            title="AI Paper Trading",
            icon="🧪",
        ),
    ],
    "⚙️ System": [
        st.Page(settings, title="Settings", icon="⚙️"),
    ],
}

pg = st.navigation(pages, position="sidebar", expanded=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📈 AI Stock Analyzer Pro")
st.sidebar.caption("Professional Investment Platform")
st.sidebar.success(f"Current: {pg.title}")
st.sidebar.metric("Modules", 12)
st.sidebar.metric("Version", "3.7")
st.sidebar.caption("© 2026 AI Stock Analyzer Pro")

pg.run()
