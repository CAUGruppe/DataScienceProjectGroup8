import streamlit as st

st.set_page_config(
    page_title="Media Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Media Analysis Dashboard")

st.markdown("""
This project analyzes media coverage of political actors 
in the context of the Israel–Palestine conflict.

### Research Questions:
- Sentiment differences across media outlets
- Actor-specific tone analysis
- Media framing patterns

👉 Use the sidebar to explore the results.
""")

st.sidebar.success("Select a page above.")