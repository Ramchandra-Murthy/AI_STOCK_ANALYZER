import streamlit as st

from services.recommendation_service import generate_recommendation

st.title("AI Recommendation Test")

result = generate_recommendation(
    technical_score=88,
    fundamental_score=91,
    news_score=78,
    valuation_score=82,
)

st.metric("Confidence", f"{result['confidence']}%")

st.success(result["recommendation"])

st.write(result)
