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
        st.Page(
            dashboard,
            title="Dashboard",
            icon="🏠",
            default=True,
            url_path="dashboard",
        ),
        st.Page(market, title="Market", icon="📈", url_path="market"),
        st.Page(portfolio, title="Portfolio", icon="💼", url_path="portfolio"),
        st.Page(scanner, title="Scanner", icon="🔍", url_path="scanner"),
    ],
    "🔴 Live Market": [
        st.Page(
            show_live_top10_scanner,
            title="Live Top-10 Scanner",
            icon="📡",
            url_path="live-top-10-scanner",
        ),
        st.Page(
            intraday,
            title="Intraday Trading",
            icon="⏱️",
            url_path="intraday-trading",
        ),
    ],
    "🔎 Research": [
        st.Page(
            research,
            title="Stock Research",
            icon="🔍",
            url_path="stock-research",
        ),
        st.Page(
            fundamentals,
            title="Fundamentals",
            icon="📊",
            url_path="fundamentals",
        ),
        st.Page(
            prediction,
            title="AI Prediction",
            icon="🤖",
            url_path="ai-prediction",
        ),
        st.Page(backtesting, title="Backtesting", icon="📉", url_path="backtesting"),
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
        st.Page(
            "pages/AI_Paper_Performance.py",
            title="AI Paper Performance",
            icon="📊",
        ),
        st.Page(
            "pages/AI_Paper_Risk.py",
            title="AI Paper Risk",
            icon="🛡️",
        ),
        st.Page(
            "pages/AI_Paper_Trade_Journal.py",
            title="AI Paper Trade Journal",
            icon="📒",
        ),
        st.Page(
            "pages/AI_Model_Monitoring.py",
            title="AI Model Monitoring",
            icon="🎯",
            url_path="ai-model-monitoring-calibration",
        ),
        st.Page(
            "pages/AI_Signal_History.py",
            title="AI Signal History",
            icon="🗂️",
            url_path="ai-signal-history",
        ),
        st.Page(
            "pages/AI_Adaptive_Performance.py",
            title="AI Adaptive Performance",
            icon="📊",
            url_path="ai-adaptive-performance",
        ),
        st.Page(
            "pages/AI_Adaptive_Learning.py",
            title="AI Adaptive Learning",
            icon="🔄",
            url_path="ai-adaptive-learning",
        ),
        st.Page(
            "pages/AI_Self_Improving_Model.py",
            title="AI Self-Improving Model",
            icon="🧠",
            url_path="ai-self-improving-model",
        ),
        st.Page(
            "pages/AI_News_Sentiment.py",
            title="AI News & Sentiment",
            icon="📰",
            url_path="ai-news-sentiment",
        ),
        st.Page(
            "pages/AI_Fundamental_Intelligence.py",
            title="AI Fundamental Intelligence",
            icon="📊",
            url_path="ai-fundamental-intelligence",
        ),
    ],
    "⚙️ System": [
        st.Page(settings, title="Settings", icon="⚙️", url_path="settings"),
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
