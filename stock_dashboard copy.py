import streamlit as st
from services.analyzer import analyze_stock

st.set_page_config(
    page_title="AI Stock Analyzer",
    page_icon="📈",
    layout="wide"
)

st.title("📈 AI Stock Analyzer Pro")

symbol = st.text_input(
    "Stock Symbol",
    value="RELIANCE.NS"
)

if st.button("Analyze"):

    st.write("Analyzing...")

    result = analyze_stock(symbol)

    st.success("Analysis Complete")

    last = result["last"]

    st.metric(
        "Current Price",
        f"₹{last['Close']:.2f}"
    )