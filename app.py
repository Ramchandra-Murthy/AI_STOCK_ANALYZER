import streamlit as st

from modules.backtesting import show as backtesting

# ==========================================================
# IMPORT MODULES
# ==========================================================
from modules.dashboard import show as dashboard
from modules.fundamentals import show as fundamentals
from modules.market import show as market
from modules.portfolio import show as portfolio
from modules.prediction import show as prediction
from modules.research import show as research
from modules.scanner import show as scanner
from modules.settings import show as settings


def load_css():
    with open("assets/styles.css") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True,
        )


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="AI Stock Analyzer Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()


# ==========================================================
# PAGE REGISTRY
# ==========================================================

PAGES = {
    "🏠 Dashboard": dashboard,
    "📈 Market": market,
    "💼 Portfolio": portfolio,
    "🔍 Scanner": scanner,
    "🔍 Stock Research": research,
    "📊 Fundamentals": fundamentals,
    "📉 Backtesting": backtesting,
    "🤖 AI Prediction": prediction,
    "⚙️ Settings": settings,
}

# ==========================================================
# SIDEBAR
# ==========================================================

st.sidebar.title("📈 AI Stock Analyzer Pro")
st.sidebar.caption("Professional Investment Platform")

selected_page = st.sidebar.radio(
    "📂 Navigation",
    list(PAGES.keys()),
)

st.sidebar.success(f"Current: {selected_page}")

st.sidebar.divider()

st.sidebar.markdown("### 📊 Application")

st.sidebar.metric(
    "Modules",
    len(PAGES),
)

st.sidebar.metric(
    "Version",
    "3.5",
)

st.sidebar.divider()

st.sidebar.caption("© 2026 AI Stock Analyzer Pro")

# ==========================================================
# PAGE ROUTER
# ==========================================================

PAGES[selected_page]()
