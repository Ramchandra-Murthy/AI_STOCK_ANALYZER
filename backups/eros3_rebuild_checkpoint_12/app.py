# -*- coding: utf-8 -*-
import streamlit as st
import modules.dashboard as dashboard
import modules.market as market
import modules.portfolio as portfolio
import modules.scanner as scanner
import modules.research as research
import modules.fundamentals as fundamentals
import modules.backtesting as backtesting

# Optional imports (graceful fallback if they don't exist)
try:
    import modules.ai_prediction as ai_prediction
except ImportError:
    ai_prediction = None

try:
    import modules.settings as settings
except ImportError:
    settings = None

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Stock Analyzer Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar Navigation ---
st.sidebar.title("📊 AI Stock Analyzer Pro")
st.sidebar.markdown("**Professional Investment Platform**")

# Define Pages
PAGES = {
    "📈 Dashboard": dashboard.show,
    "📊 Market": market.show,
    "💰 Portfolio": portfolio.show,
    "🔍 Scanner": scanner.show,
    "📰 Stock Research": research.show,
    "📋 Fundamentals": fundamentals.show,
    "⚡ Backtesting": backtesting.show,
}

# Add optional pages if they exist
if ai_prediction:
    PAGES["🤖 AI Prediction"] = ai_prediction.show
if settings:
    PAGES["⚙️ Settings"] = settings.show

st.sidebar.divider()
selection = st.sidebar.radio("Navigate to", list(PAGES.keys()), index=0)

st.sidebar.divider()
st.sidebar.caption(f"📍 Current: {selection}")

# --- Render Selected Page ---
page_func = PAGES[selection]
page_func()
